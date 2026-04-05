'use strict';

// ── Mock state for browser-only development ──────────────────────
const MOCK_STATE = {
  version: 'v0.0.7',
  masterVolume: 50,
  masterMute: false,
  sliders: [
    { name: 'Chrome',  volume: 70, mute: false, knob_index: 1, app_names: ['chrome.exe'] },
    { name: 'Discord', volume: 52, mute: false, knob_index: 3, app_names: ['Discord.exe'] },
    { name: 'Spotify', volume: 32, mute: false, knob_index: 2, app_names: ['Spotify.exe'] },
  ],
}

// ── Blaudio namespace ─────────────────────────────────────────────
window.blaudio = {

  state: { version: '', masterVolume: 50, masterMute: false, sliders: [] },
  _editIndex: null,
  _dragMoved: false,
  _draggingCol: null,
  _containerDragover: null,
  _peakHold: {},
  _currentTheme: 'dark',
  _currentLayout: 'vertical',
  _themes: [
    { id: 'dark',      label: 'Dark',      bg: '#1a1a1a', accent: '#9C27B0' },
    { id: 'light',     label: 'Light',     bg: '#f4f4f5', accent: '#9C27B0' },
    { id: 'ocean',     label: 'Ocean',     bg: '#0d1b2a', accent: '#00BCD4' },
    { id: 'synthwave', label: 'Synthwave', bg: '#0a0010', accent: '#e040fb' },
  ],

  // ── Python → JS event receiver ─────────────────────────────────
  _receive(payload) {
    const { event, data } = payload
    switch (event) {
      case 'master_volume': this._syncMasterSlider(data.volume);            break
      case 'master_mute':   this._syncMasterMute(data.mute);               break
      case 'slider_volume': this._syncSliderValue(data.index, data.volume); break
      case 'notification':  this.showToast(data.message);                  break
      case 'peak_levels':   this._updatePeakMeters(data);                  break
    }
  },

  // ── Init ────────────────────────────────────────────────────────
  init(state) {
    // Prefer server-persisted settings; fall back to localStorage for browser testing
    this._applyTheme(state.theme   || localStorage.getItem('blaudio-theme')   || 'dark')
    this._applyLayout(state.layout || localStorage.getItem('blaudio-layout') || 'vertical')
    this.state = state
    this._renderMaster()
    this._renderSliders()
    this._initMasterInteractions()
  },

  // ── Master slider ───────────────────────────────────────────────
  _renderMaster() {
    const slider  = document.getElementById('master-slider')
    const muteBtn = document.getElementById('master-mute-btn')
    const panel   = document.getElementById('master-panel')
    if (slider)  slider.value = this.state.masterVolume
    if (muteBtn) muteBtn.classList.toggle('active', this.state.masterMute)
    if (panel)   panel.classList.toggle('muted', this.state.masterMute)
    if (slider)  slider.disabled = this.state.masterMute
  },

  async setMasterVolume(value) {
    this.state.masterVolume = parseInt(value)
    if (window.pywebview) await window.pywebview.api.set_master_volume(value)
  },

  async toggleMasterMute() {
    if (window.pywebview) {
      this.state.masterMute = await window.pywebview.api.toggle_master_mute()
    } else {
      this.state.masterMute = !this.state.masterMute
    }
    this._renderMaster()
  },

  _syncMasterSlider(volume) {
    this.state.masterVolume = volume
    const el = document.getElementById('master-slider')
    if (el) el.value = volume
    const panel = document.getElementById('master-panel')
    if (panel) this._showVolReadout(panel, volume)
  },

  _syncMasterMute(mute) {
    this.state.masterMute = mute
    this._renderMaster()
  },

  // ── Dynamic sliders ─────────────────────────────────────────────
  _renderSliders() {
    const container = document.getElementById('sliders-container')
    if (!container) return

    // Remove stale delegated dragover before rebuilding
    if (this._containerDragover) {
      container.removeEventListener('dragover', this._containerDragover)
    }

    container.innerHTML = ''
    this.state.sliders.forEach((slider, i) => container.appendChild(this._makeCol(slider, i)))

    // Single delegated dragover for the whole container.
    // Catches events from any depth of children so the cursor never "misses".
    this._containerDragover = e => {
      const src = this._draggingCol
      if (!src) return
      e.preventDefault()
      e.dataTransfer.dropEffect = 'move'
      const targetCol = e.target.closest('.slider-col')
      if (!targetCol || targetCol === src) return
      const rect   = targetCol.getBoundingClientRect()
      const before = document.body.classList.contains('layout-horizontal')
        ? e.clientY < rect.top  + rect.height / 2
        : e.clientX < rect.left + rect.width  / 2
      const ref = before ? targetCol : targetCol.nextSibling
      if (src.nextSibling !== ref) {
        container.insertBefore(src, ref)
        this._dragMoved = true
      }
    }
    container.addEventListener('dragover', this._containerDragover)
  },

  _makeCol(slider, index) {
    const col = document.createElement('div')
    col.className = `slider-col${slider.mute ? ' muted' : ''}`
    col.dataset.index = index
    col.innerHTML = `
      <span class="slider-label" title="${slider.name}">${slider.name}</span>
      <div class="slider-wrapper">
        <div class="vu-meter">
          <div class="vu-bar"></div>
          <div class="vu-peak"></div>
        </div>
        <span class="vol-readout"></span>
        <input type="range" class="vslider" min="0" max="100" value="${slider.volume}"
               ${slider.mute ? 'disabled' : ''}>
      </div>
      <div class="slider-controls">
        <button class="icon-btn mute-btn${slider.mute ? ' active' : ''}" title="Mute"
                onclick="blaudio.toggleSliderMute(${index})">🔇</button>
        <button class="icon-btn" title="Delete"
                onclick="blaudio.removeSlider(${index})">🗑️</button>
        <button class="icon-btn" title="Edit"
                onclick="blaudio.openEditSliderDialog(${index})">📝</button>
      </div>`

    // Range input: fire volume update + readout on drag
    const rangeInput = col.querySelector('.vslider')
    rangeInput.addEventListener('input', e => {
      const val = parseInt(e.target.value)
      this.state.sliders[index].volume = val
      this.setSliderVolume(index, val)
      this._showVolReadout(col, val)
    })

    // Scroll wheel: nudge volume ±2 per notch
    col.addEventListener('wheel', e => {
      e.preventDefault()
      const delta  = e.deltaY < 0 ? 2 : -2
      const cur    = this.state.sliders[index]
      if (!cur) return
      const newVol = Math.min(100, Math.max(0, cur.volume + delta))
      cur.volume   = newVol
      rangeInput.value = newVol
      this.setSliderVolume(index, newVol)
      this._showVolReadout(col, newVol)
    }, { passive: false })

    // ── Drag-to-reorder ─────────────────────────────────────────
    // draggable is on the *label* (the handle), not the whole col.
    // In HTML5 DnD, e.target on a dragstart is always the draggable
    // element itself, so we can't guard by checking e.target on the col.
    const label = col.querySelector('.slider-label')
    label.draggable = true

    label.addEventListener('dragstart', e => {
      this._draggingCol = col
      this._dragMoved   = false
      col.classList.add('dragging')
      e.dataTransfer.effectAllowed = 'move'
      e.dataTransfer.setData('text/plain', String(index))
      // Use the whole column as the drag ghost image
      const r = col.getBoundingClientRect()
      e.dataTransfer.setDragImage(col, e.clientX - r.left, e.clientY - r.top)
    })

    label.addEventListener('dragend', e => {
      col.classList.remove('dragging')
      this._draggingCol = null
      if (this._dragMoved && e.dataTransfer.dropEffect !== 'none') {
        this._commitDragOrder()
      } else if (this._dragMoved) {
        this._renderSliders()  // cancelled (ESC) after partial move — restore
      }
    })

    return col
  },

  async _commitDragOrder() {
    const container = document.getElementById('sliders-container')
    if (!container) return
    // Read the original indices in their new DOM positions
    const domOrder = Array.from(container.querySelectorAll('.slider-col'))
      .map(el => parseInt(el.dataset.index))
    this.state.sliders = domOrder.map(i => this.state.sliders[i])
    this._renderSliders()  // re-render to refresh indices and onclick handlers
    if (window.pywebview) await window.pywebview.api.reorder_sliders(domOrder)
  },

  async setSliderVolume(index, value) {
    this.state.sliders[index].volume = parseInt(value)
    if (window.pywebview) await window.pywebview.api.set_slider_volume(index, value)
  },

  async toggleSliderMute(index) {
    if (window.pywebview) {
      this.state.sliders[index].mute = await window.pywebview.api.toggle_slider_mute(index)
    } else {
      this.state.sliders[index].mute = !this.state.sliders[index].mute
    }
    this._renderSliders()
  },

  async removeSlider(index) {
    if (window.pywebview) await window.pywebview.api.remove_slider(index)
    this.state.sliders.splice(index, 1)
    this._renderSliders()
  },

  _syncSliderValue(index, volume) {
    if (this.state.sliders[index]) this.state.sliders[index].volume = volume
    const col = document.querySelector(`.slider-col[data-index="${index}"]`)
    const input = col && col.querySelector('.vslider')
    if (input) input.value = volume
    if (col) this._showVolReadout(col, volume)
  },

  // ── Add slider dialog ───────────────────────────────────────────
  async openAddSliderDialog() {
    let apps = []
    if (window.pywebview) {
      apps = await window.pywebview.api.get_running_apps()
    } else {
      apps = ['chrome.exe', 'Discord.exe', 'Spotify.exe', 'All Unassigned']
    }

    const list = document.getElementById('app-list')
    list.innerHTML = ''
    apps.forEach(app => {
      const label = document.createElement('label')
      label.className = 'app-entry'
      label.innerHTML = `<input type="checkbox" value="${app}"><span>${app}</span>`
      list.appendChild(label)
    })

    document.getElementById('slider-name').value = ''
    document.getElementById('knob-select').value = '-1'
    document.getElementById('overlay').classList.remove('hidden')
    setTimeout(() => document.getElementById('slider-name').focus(), 50)
  },

  async openEditSliderDialog(index) {
    const slider = this.state.sliders[index]
    if (!slider) return

    let apps = []
    if (window.pywebview) {
      apps = await window.pywebview.api.get_running_apps()
    } else {
      apps = ['chrome.exe', 'Discord.exe', 'Spotify.exe', 'All Unassigned']
    }

    // Merge in any assigned apps that may not currently be running
    slider.app_names.forEach(a => { if (!apps.includes(a)) apps.unshift(a) })

    const list = document.getElementById('app-list')
    list.innerHTML = ''
    apps.forEach(app => {
      const label = document.createElement('label')
      label.className = 'app-entry'
      const checked = slider.app_names.includes(app) ? 'checked' : ''
      label.innerHTML = `<input type="checkbox" value="${app}" ${checked}><span>${app}</span>`
      list.appendChild(label)
    })

    document.getElementById('slider-name').value = slider.name
    document.getElementById('knob-select').value = slider.knob_index ?? -1
    document.getElementById('dialog-title').textContent = 'Edit Slider'
    document.getElementById('dialog-confirm-btn').textContent = 'Save'
    this._editIndex = index
    document.getElementById('overlay').classList.remove('hidden')
    setTimeout(() => document.getElementById('slider-name').focus(), 50)
  },

  closeModal(e) {
    if (!e || e.target.id === 'overlay') {
      document.getElementById('overlay').classList.add('hidden')
      this._editIndex = null
      document.getElementById('dialog-title').textContent = 'Add Slider'
      document.getElementById('dialog-confirm-btn').textContent = 'Add'
    }
  },

  async confirmSlider() {
    const name = document.getElementById('slider-name').value.trim()
    if (!name) { document.getElementById('slider-name').focus(); return }

    const appNames  = Array.from(document.querySelectorAll('#app-list input:checked')).map(cb => cb.value)
    const knobIndex = parseInt(document.getElementById('knob-select').value)

    if (this._editIndex !== null) {
      let updated
      if (window.pywebview) {
        updated = await window.pywebview.api.edit_slider(this._editIndex, name, appNames, knobIndex)
      } else {
        updated = { ...this.state.sliders[this._editIndex], name, app_names: appNames, knob_index: knobIndex }
      }
      if (updated) {
        this.state.sliders[this._editIndex] = updated
        this._renderSliders()
      }
    } else {
      let newSlider
      if (window.pywebview) {
        newSlider = await window.pywebview.api.create_slider(name, appNames, knobIndex)
      } else {
        newSlider = { name, app_names: appNames, volume: 50, mute: false, knob_index: knobIndex }
      }
      if (newSlider) {
        this.state.sliders.push(newSlider)
        this._renderSliders()
      }
    }
    this.closeModal()
  },

  // ── VU meters ───────────────────────────────────────────────────
  _updatePeakMeters({ master, sliders }) {
    const masterBar  = document.querySelector('#master-vu .vu-bar')
    const masterPeak = document.querySelector('#master-vu .vu-peak')
    this._setPeak('master', master, masterBar, masterPeak)

    sliders.forEach((peak, i) => {
      const col = document.querySelector(`.slider-col[data-index="${i}"]`)
      if (!col) return
      this._setPeak(i, peak, col.querySelector('.vu-bar'), col.querySelector('.vu-peak'))
    })
  },

  _setPeak(key, peakVal, barEl, peakEl) {
    if (!barEl) return
    const isHoriz = document.body.classList.contains('layout-horizontal')

    // Move bar via GPU-composited transform (no layout reflow)
    barEl.style.transform = isHoriz
      ? `translateY(-50%) scaleX(${peakVal})`
      : `translateX(-50%) scaleY(${peakVal})`

    // Peak hold: advance when higher, decay after 1.5 s
    let held = this._peakHold[key]
    if (!held) held = this._peakHold[key] = { value: 0, timer: null }

    if (peakVal >= held.value) {
      held.value = peakVal
      clearTimeout(held.timer)
      held.timer = setTimeout(() => {
        held.value = 0
        if (peakEl) {
          if (isHoriz) peakEl.style.left   = '0%'
          else         peakEl.style.bottom = '0%'
        }
      }, 1500)
    }

    if (peakEl) {
      const pos = `${held.value * 100}%`
      if (isHoriz) peakEl.style.left   = pos
      else         peakEl.style.bottom = pos
    }
  },

  // ── Volume readout ───────────────────────────────────────────────
  _showVolReadout(container, value) {
    const el = container.querySelector('.vol-readout')
    if (!el) return
    el.textContent = value
    el.classList.add('visible')
    clearTimeout(el._hideTimer)
    el._hideTimer = setTimeout(() => el.classList.remove('visible'), 1200)
  },

  // ── Master panel interactions (set up once in init) ───────────────
  _initMasterInteractions() {
    const panel  = document.getElementById('master-panel')
    const slider = document.getElementById('master-slider')
    if (!panel || !slider) return

    // Show readout while dragging
    slider.addEventListener('input', () => {
      this._showVolReadout(panel, parseInt(slider.value))
    })

    // Scroll wheel on the whole master panel
    panel.addEventListener('wheel', e => {
      e.preventDefault()
      const delta  = e.deltaY < 0 ? 2 : -2
      const newVol = Math.min(100, Math.max(0, this.state.masterVolume + delta))
      this.state.masterVolume = newVol
      slider.value = newVol
      this.setMasterVolume(newVol)
      this._showVolReadout(panel, newVol)
    }, { passive: false })
  },

  // ── Settings ────────────────────────────────────────────────────
  openSettings() {
    this._renderThemePicker()
    this._renderLayoutPicker()
    document.getElementById('settings-overlay').classList.remove('hidden')
  },

  closeSettings(e) {
    if (!e || e.target.id === 'settings-overlay') {
      document.getElementById('settings-overlay').classList.add('hidden')
    }
  },

  setTheme(id) {
    this._applyTheme(id)
    localStorage.setItem('blaudio-theme', id)  // fallback for browser testing
    if (window.pywebview) window.pywebview.api.save_ui_setting('theme', id)
    this._renderThemePicker()
  },

  setLayout(layout) {
    this._applyLayout(layout)
    localStorage.setItem('blaudio-layout', layout)  // fallback for browser testing
    if (window.pywebview) window.pywebview.api.save_ui_setting('layout', layout)
    this._renderLayoutPicker()
  },

  _applyTheme(id) {
    document.documentElement.setAttribute('data-theme', id)
    this._currentTheme = id
  },

  _applyLayout(layout) {
    document.body.classList.toggle('layout-horizontal', layout === 'horizontal')
    this._currentLayout = layout
  },

  _renderThemePicker() {
    const picker = document.getElementById('theme-picker')
    if (!picker) return
    picker.innerHTML = ''
    this._themes.forEach(t => {
      const btn = document.createElement('button')
      btn.className = `theme-card${this._currentTheme === t.id ? ' active' : ''}`
      btn.onclick = () => this.setTheme(t.id)
      btn.innerHTML = `
        <span class="theme-swatch"
              style="background: linear-gradient(135deg, ${t.bg} 55%, ${t.accent} 55%)"></span>
        <span>${t.label}</span>`
      picker.appendChild(btn)
    })
  },

  _renderLayoutPicker() {
    document.querySelectorAll('.layout-opt').forEach(btn => {
      btn.classList.toggle('active', btn.dataset.layout === this._currentLayout)
    })
  },

  // ── Utilities ───────────────────────────────────────────────────
  showToast(message) {
    const toast = document.getElementById('toast')
    toast.textContent = message
    toast.classList.add('visible')
    clearTimeout(this._toastTimer)
    this._toastTimer = setTimeout(() => toast.classList.remove('visible'), 2500)
  },

  async openMixer() {
    if (window.pywebview) await window.pywebview.api.open_mixer()
  },

  async quit() {
    if (window.pywebview) await window.pywebview.api.quit()
  },

  about() {
    this.showToast(`Blaudio ${this.state.version}`)
  },
}

// ── Bootstrap ────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
  function start() {
    if (window.pywebview) {
      window.pywebview.api.get_initial_state().then(state => window.blaudio.init(state))
    } else {
      window.blaudio.init(MOCK_STATE)
    }
  }

  if (window.pywebview) {
    start()
  } else {
    window.addEventListener('pywebviewready', start)
    // Fallback for plain browser testing (no pywebview)
    setTimeout(() => { if (!window.pywebview) start() }, 500)
  }
})

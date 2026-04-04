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

  // ── Python → JS event receiver ─────────────────────────────────
  _receive(payload) {
    const { event, data } = payload
    switch (event) {
      case 'master_volume': this._syncMasterSlider(data.volume);          break
      case 'master_mute':   this._syncMasterMute(data.mute);              break
      case 'slider_volume': this._syncSliderValue(data.index, data.volume); break
      case 'notification':  this.showToast(data.message);                 break
    }
  },

  // ── Init ────────────────────────────────────────────────────────
  init(state) {
    this.state = state
    this._renderMaster()
    this._renderSliders()
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
  },

  _syncMasterMute(mute) {
    this.state.masterMute = mute
    this._renderMaster()
  },

  // ── Dynamic sliders ─────────────────────────────────────────────
  _renderSliders() {
    const container = document.getElementById('sliders-container')
    if (!container) return
    container.innerHTML = ''
    this.state.sliders.forEach((slider, i) => container.appendChild(this._makeCol(slider, i)))
  },

  _makeCol(slider, index) {
    const col = document.createElement('div')
    col.className = `slider-col${slider.mute ? ' muted' : ''}`
    col.dataset.index = index
    col.innerHTML = `
      <span class="slider-label" title="${slider.name}">${slider.name}</span>
      <div class="slider-wrapper">
        <input type="range" class="vslider" min="0" max="100" value="${slider.volume}"
               ${slider.mute ? 'disabled' : ''}
               oninput="blaudio.setSliderVolume(${index}, this.value)">
      </div>
      <div class="slider-controls">
        <button class="icon-btn mute-btn${slider.mute ? ' active' : ''}" title="Mute"
                onclick="blaudio.toggleSliderMute(${index})">🔇</button>
        <button class="icon-btn" title="Delete"
                onclick="blaudio.removeSlider(${index})">🗑️</button>
        <button class="icon-btn" title="Edit (coming soon)"
                onclick="blaudio.showToast('Edit coming soon')">📝</button>
      </div>`
    return col
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

  closeModal(e) {
    if (!e || e.target.id === 'overlay') {
      document.getElementById('overlay').classList.add('hidden')
    }
  },

  async confirmAddSlider() {
    const name = document.getElementById('slider-name').value.trim()
    if (!name) { document.getElementById('slider-name').focus(); return }

    const appNames   = Array.from(document.querySelectorAll('#app-list input:checked')).map(cb => cb.value)
    const knobIndex  = parseInt(document.getElementById('knob-select').value)

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
    this.closeModal()
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

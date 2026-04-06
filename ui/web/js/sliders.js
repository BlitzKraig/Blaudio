'use strict';

// Dynamic per-app sliders: rendering, interactions, and drag-to-reorder.
Object.assign(window.blaudio, {

  _dragMoved:          false,
  _draggingCol:        null,
  _containerDragover:  null,

  _renderSliders() {
    const container = document.getElementById('sliders-container')
    if (!container) return

    // Remove stale delegated dragover listener before rebuilding DOM.
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
    const isHorizontal = document.body.classList.contains('layout-horizontal')

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
        <div class="vslider"></div>
      </div>
      <div class="slider-controls">
        <button class="icon-btn mute-btn${slider.mute ? ' active' : ''}" title="Mute"
                onclick="blaudio.toggleSliderMute(${index})">🔇</button>
        <button class="icon-btn" title="Delete"
                onclick="blaudio.removeSlider(${index})">🗑️</button>
        <button class="icon-btn" title="Edit"
                onclick="blaudio.openEditSliderDialog(${index})">📝</button>
      </div>`

    const sliderEl = col.querySelector('.vslider')

    noUiSlider.create(sliderEl, {
      start:       [slider.volume],
      range:       { min: 0, max: 100 },
      orientation: isHorizontal ? 'horizontal' : 'vertical',
      direction:   isHorizontal ? 'ltr' : 'rtl',
      connect:     [true, false],
    })

    if (slider.mute) sliderEl.noUiSlider.disable()

    // 'slide' only fires on user drag — not on programmatic .set() calls,
    // so hardware-push syncs don't echo back to Python.
    sliderEl.noUiSlider.on('slide', (values) => {
      const val = Math.round(parseFloat(values[0]))
      this.state.sliders[index].volume = val
      this.setSliderVolume(index, val)
      this._showVolReadout(col, val)
    })

    col.addEventListener('wheel', e => {
      e.preventDefault()
      const delta  = e.deltaY < 0 ? 2 : -2
      const cur    = this.state.sliders[index]
      if (!cur) return
      const newVol = Math.min(100, Math.max(0, cur.volume + delta))
      cur.volume = newVol
      sliderEl.noUiSlider.set(newVol)
      this.setSliderVolume(index, newVol)
      this._showVolReadout(col, newVol)
    }, { passive: false })

    this._attachDragHandlers(col, index)
    return col
  },

  // draggable is on the label (the handle), not the whole column.
  _attachDragHandlers(col, index) {
    const label = col.querySelector('.slider-label')
    label.draggable = true

    label.addEventListener('dragstart', e => {
      this._draggingCol = col
      this._dragMoved   = false
      col.classList.add('dragging')
      e.dataTransfer.effectAllowed = 'move'
      e.dataTransfer.setData('text/plain', String(index))
      const r = col.getBoundingClientRect()
      e.dataTransfer.setDragImage(col, e.clientX - r.left, e.clientY - r.top)
    })

    label.addEventListener('dragend', e => {
      col.classList.remove('dragging')
      this._draggingCol = null
      if (this._dragMoved && e.dataTransfer.dropEffect !== 'none') {
        this._commitDragOrder()
      } else if (this._dragMoved) {
        // Drag cancelled (ESC) after a partial DOM move — restore original order.
        this._renderSliders()
      }
    })
  },

  async _commitDragOrder() {
    const container = document.getElementById('sliders-container')
    if (!container) return
    const domOrder = Array.from(container.querySelectorAll('.slider-col'))
      .map(el => parseInt(el.dataset.index))
    this.state.sliders = domOrder.map(i => this.state.sliders[i])
    this._renderSliders()
    await this._apiReorderSliders(domOrder)
  },

  async setSliderVolume(index, value) {
    this.state.sliders[index].volume = parseInt(value)
    await this._apiSetSliderVolume(index, value)
  },

  async toggleSliderMute(index) {
    this.state.sliders[index].mute = await this._apiToggleSliderMute(index)
    this._renderSliders()
  },

  async removeSlider(index) {
    await this._apiRemoveSlider(index)
    this.state.sliders.splice(index, 1)
    this._renderSliders()
  },

  // Sync a slider's mute state from a hardware button press.
  _syncSliderMute(index, mute) {
    if (this.state.sliders[index]) this.state.sliders[index].mute = mute
    const col = document.querySelector(`.slider-col[data-index="${index}"]`)
    if (!col) return
    col.classList.toggle('muted', mute)
    const sliderEl = col.querySelector('.vslider')
    if (sliderEl && sliderEl.noUiSlider) {
      if (mute) sliderEl.noUiSlider.disable()
      else sliderEl.noUiSlider.enable()
    }
    const btn = col.querySelector('.mute-btn')
    if (btn) btn.classList.toggle('active', mute)
  },

  // Sync a single slider's value from a Python hardware push event.
  _syncSliderValue(index, volume) {
    if (this.state.sliders[index]) this.state.sliders[index].volume = volume
    const col     = document.querySelector(`.slider-col[data-index="${index}"]`)
    const sliderEl = col && col.querySelector('.vslider')
    if (sliderEl && sliderEl.noUiSlider) sliderEl.noUiSlider.set(volume)
    if (col) this._showVolReadout(col, volume)
  },

})

'use strict';

// Dynamic per-app sliders: rendering, interactions, and drag-to-reorder.
Object.assign(window.blaudio, {

  _sortable: null,

  _renderSliders() {
    const container = document.getElementById('sliders-container')
    if (!container) return

    // Tear down previous Sortable instance before rebuilding the DOM.
    if (this._sortable) {
      this._sortable.destroy()
      this._sortable = null
    }

    container.innerHTML = ''
    this.state.sliders.forEach((slider, i) => container.appendChild(this._makeCol(slider, i)))

    const isHorizontal = document.body.classList.contains('layout-horizontal')

    this._sortable = Sortable.create(container, {
      handle:      '.slider-label',
      animation:   200,
      easing:      'cubic-bezier(0.25, 1, 0.5, 1)',
      direction:   isHorizontal ? 'vertical' : 'horizontal',
      chosenClass: 'dragging',     // reuses existing opacity/cursor CSS
      ghostClass:  'slider-ghost', // invisible placeholder; items animate around it
      onEnd: (evt) => {
        if (evt.oldIndex === evt.newIndex) return
        // data-index values still reflect the pre-drag state indices — read them
        // from the DOM (Sortable has already moved the elements) to derive the
        // new order, then hand off to Python.
        const cols = Array.from(container.querySelectorAll('.slider-col'))
        const newOrder = cols.map(col => parseInt(col.dataset.index))
        this.state.sliders = newOrder.map(i => this.state.sliders[i])
        // Defer re-render so Sortable finishes its own cleanup first.
        setTimeout(() => this._renderSliders(), 0)
        this._apiReorderSliders(newOrder)
      },
    })
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

    return col
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
    const col      = document.querySelector(`.slider-col[data-index="${index}"]`)
    const sliderEl = col && col.querySelector('.vslider')
    if (sliderEl && sliderEl.noUiSlider) sliderEl.noUiSlider.set(volume)
    if (col) this._showVolReadout(col, volume)
  },

})

'use strict';

// Master volume panel — rendering, interactions, and sync from hardware/Python.
Object.assign(window.blaudio, {

  _masterWheelAbort: null,

  _renderMaster() {
    const sliderEl = document.getElementById('master-slider')
    const muteBtn  = document.getElementById('master-mute-btn')
    const panel    = document.getElementById('master-panel')
    if (sliderEl && sliderEl.noUiSlider) sliderEl.noUiSlider.set(this.state.masterVolume)
    if (muteBtn) muteBtn.classList.toggle('active', this.state.masterMute)
    if (panel)   panel.classList.toggle('muted', this.state.masterMute)
    if (sliderEl && sliderEl.noUiSlider) {
      if (this.state.masterMute) sliderEl.noUiSlider.disable()
      else sliderEl.noUiSlider.enable()
    }
  },

  // Called by the noUiSlider 'slide' event and scroll wheel handler.
  async setMasterVolume(value) {
    this.state.masterVolume = parseInt(value)
    await this._apiSetMasterVolume(value)
  },

  async toggleMasterMute() {
    this.state.masterMute = await this._apiToggleMasterMute()
    this._renderMaster()
  },

  // ── Sync from Python push events ─────────────────────────────────

  _syncMasterSlider(volume) {
    this.state.masterVolume = volume
    const el = document.getElementById('master-slider')
    if (el && el.noUiSlider) el.noUiSlider.set(volume)
    const panel = document.getElementById('master-panel')
    if (panel) this._showVolReadout(panel, volume)
  },

  _syncMasterMute(mute) {
    this.state.masterMute = mute
    this._renderMaster()
  },

  // ── Interactions — safe to call multiple times (e.g. on layout change) ───

  _initMasterInteractions() {
    const panel    = document.getElementById('master-panel')
    const sliderEl = document.getElementById('master-slider')
    if (!panel || !sliderEl) return

    // Destroy any existing instance before (re-)creating (e.g. layout switch).
    if (sliderEl.noUiSlider) sliderEl.noUiSlider.destroy()

    // Remove the previous wheel listener via AbortController so it doesn't pile up.
    if (this._masterWheelAbort) this._masterWheelAbort.abort()
    this._masterWheelAbort = new AbortController()

    const isHorizontal = document.body.classList.contains('layout-horizontal')
    noUiSlider.create(sliderEl, {
      start:       [this.state.masterVolume],
      range:       { min: 0, max: 100 },
      orientation: isHorizontal ? 'horizontal' : 'vertical',
      direction:   isHorizontal ? 'ltr' : 'rtl',
      connect:     [true, false],
    })

    // Apply initial mute state now that noUiSlider exists.
    if (this.state.masterMute) sliderEl.noUiSlider.disable()

    // 'slide' only fires on user drag — not on programmatic .set() calls,
    // so hardware-push syncs don't echo back to Python.
    sliderEl.noUiSlider.on('slide', (values) => {
      const val = Math.round(parseFloat(values[0]))
      this.state.masterVolume = val
      this._showVolReadout(panel, val)
      this.setMasterVolume(val)
    })

    panel.addEventListener('wheel', e => {
      e.preventDefault()
      const delta  = e.deltaY < 0 ? 2 : -2
      const newVol = Math.min(100, Math.max(0, this.state.masterVolume + delta))
      this.state.masterVolume = newVol
      sliderEl.noUiSlider.set(newVol)
      this.setMasterVolume(newVol)
      this._showVolReadout(panel, newVol)
    }, { passive: false, signal: this._masterWheelAbort.signal })
  },

})

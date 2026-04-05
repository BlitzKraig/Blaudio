'use strict';

// Master volume panel — rendering, interactions, and sync from hardware/Python.
Object.assign(window.blaudio, {

  _renderMaster() {
    const slider  = document.getElementById('master-slider')
    const muteBtn = document.getElementById('master-mute-btn')
    const panel   = document.getElementById('master-panel')
    if (slider)  slider.value = this.state.masterVolume
    if (muteBtn) muteBtn.classList.toggle('active', this.state.masterMute)
    if (panel)   panel.classList.toggle('muted', this.state.masterMute)
    if (slider)  slider.disabled = this.state.masterMute
  },

  // Called by the HTML range input (oninput) and scroll wheel handler.
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
    if (el) el.value = volume
    const panel = document.getElementById('master-panel')
    if (panel) this._showVolReadout(panel, volume)
  },

  _syncMasterMute(mute) {
    this.state.masterMute = mute
    this._renderMaster()
  },

  // ── Interactions (wired up once during init) ──────────────────────

  _initMasterInteractions() {
    const panel  = document.getElementById('master-panel')
    const slider = document.getElementById('master-slider')
    if (!panel || !slider) return

    slider.addEventListener('input', () => {
      this._showVolReadout(panel, parseInt(slider.value))
    })

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

})

'use strict';

// Python → JS event receiver and all pywebview.api.* call wrappers.
Object.assign(window.blaudio, {

  // Called by Python via window.evaluate_js to push server-side events.
  _receive(payload) {
    const { event, data } = payload
    switch (event) {
      case 'master_volume':    this._syncMasterSlider(data.volume);             break
      case 'master_mute':      this._syncMasterMute(data.mute);                break
      case 'slider_volume':    this._syncSliderValue(data.index, data.volume);  break
      case 'slider_mute':      this._syncSliderMute(data.index, data.mute);     break
      case 'button_detected':       this._onButtonDetected(data.button_index);  break
      case 'knob_detected':         this._onKnobDetected(data.knob_index);      break
      case 'port_detected':         this._onPortDetected(data.port);            break
      case 'port_detection_failed': this._onPortDetectionFailed();              break
      case 'notification':          this.showToast(data.message);               break
      case 'peak_levels':      this._updatePeakMeters(data);                   break
    }
  },

  // ── Wrappers around window.pywebview.api.* ───────────────────────────────

  async _apiSetMasterVolume(value) {
    if (window.pywebview) await window.pywebview.api.set_master_volume(value)
  },

  async _apiToggleMasterMute() {
    if (window.pywebview) return await window.pywebview.api.toggle_master_mute()
    return !this.state.masterMute
  },

  async _apiGetRunningApps() {
    if (window.pywebview) return await window.pywebview.api.get_running_apps()
    return ['chrome.exe', 'Discord.exe', 'Spotify.exe', 'All Unassigned']
  },

  async _apiCreateSlider(name, appNames, knobIndex, buttonIndex) {
    if (window.pywebview) return await window.pywebview.api.create_slider(name, appNames, knobIndex, buttonIndex)
    const btn = buttonIndex >= 0 ? buttonIndex : null
    return { name, app_names: appNames, volume: 50, mute: false, knob_index: knobIndex, button_index: btn }
  },

  async _apiEditSlider(index, name, appNames, knobIndex, buttonIndex) {
    if (window.pywebview) return await window.pywebview.api.edit_slider(index, name, appNames, knobIndex, buttonIndex)
    const btn = buttonIndex >= 0 ? buttonIndex : null
    return { ...this.state.sliders[index], name, app_names: appNames, knob_index: knobIndex, button_index: btn }
  },

  async _apiSetSliderVolume(index, value) {
    if (window.pywebview) await window.pywebview.api.set_slider_volume(index, value)
  },

  async _apiToggleSliderMute(index) {
    if (window.pywebview) return await window.pywebview.api.toggle_slider_mute(index)
    return !this.state.sliders[index].mute
  },

  async _apiRemoveSlider(index) {
    if (window.pywebview) await window.pywebview.api.remove_slider(index)
  },

  async _apiReorderSliders(order) {
    if (window.pywebview) await window.pywebview.api.reorder_sliders(order)
  },

  async _apiSaveUiSetting(key, value) {
    if (window.pywebview) window.pywebview.api.save_ui_setting(key, value)
  },

  async _apiStartButtonDetection() {
    if (window.pywebview) await window.pywebview.api.start_button_detection()
  },

  async _apiCancelButtonDetection() {
    if (window.pywebview) await window.pywebview.api.cancel_button_detection()
  },

  async _apiStartKnobDetection() {
    if (window.pywebview) await window.pywebview.api.start_knob_detection()
  },

  async _apiCancelKnobDetection() {
    if (window.pywebview) await window.pywebview.api.cancel_knob_detection()
  },

  async _apiStartPortDetection() {
    if (window.pywebview) await window.pywebview.api.start_port_detection()
    else setTimeout(() => this._onPortDetected('COM6'), 2000)  // mock
  },

  async _apiCancelPortDetection() {
    if (window.pywebview) await window.pywebview.api.cancel_port_detection()
  },

  async _apiSaveComPort(port) {
    if (window.pywebview) await window.pywebview.api.save_com_port(port)
  },

  async openMixer() {
    if (window.pywebview) await window.pywebview.api.open_mixer()
  },

  async quit() {
    if (window.pywebview) await window.pywebview.api.quit()
  },

})

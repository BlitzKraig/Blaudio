'use strict';

// Overrides and bootstrap for the Add/Edit Slider popup window.
// Loaded after dialogs.js; replaces the methods that interact with the main
// window DOM (overlay visibility, local state mutation, _renderSliders).
Object.assign(window.blaudio, {

  // Close the popup window instead of hiding an overlay.
  closeModal(e) {
    if (this._detecting)     this._apiCancelButtonDetection()
    if (this._detectingKnob) this._apiCancelKnobDetection()
    this._editIndex          = null
    this._pendingButtonIndex = null
    this._pendingKnobIndex   = null
    if (window.pywebview) window.pywebview.api.close_popup_window()
  },

  // After confirm, Python pushes 'sliders_changed' to the main window so it
  // re-renders.  We just close the popup - no local state mutation needed.
  async confirmSlider() {
    const name = document.getElementById('slider-name').value.trim()
    if (!name) { document.getElementById('slider-name').focus(); return }

    const appNames    = Array.from(document.querySelectorAll('#app-list input:checked')).map(cb => cb.value)
    const knobIndex   = this._pendingKnobIndex   !== null ? this._pendingKnobIndex   : -1
    const buttonIndex = this._pendingButtonIndex !== null ? this._pendingButtonIndex : -1

    if (this._editIndex !== null) {
      await this._apiEditSlider(this._editIndex, name, appNames, knobIndex, buttonIndex)
    } else {
      await this._apiCreateSlider(name, appNames, knobIndex, buttonIndex)
    }
    if (window.pywebview) window.pywebview.api.close_popup_window()
  },

})

// ── Bootstrap ────────────────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
  function start() {
    window.pywebview.api.get_popup_context().then(ctx => {
      window.blaudio._applyTheme(ctx.theme || 'dark')

      const slider = (ctx.editIndex >= 0 && ctx.slider) ? ctx.slider : null
      window.blaudio._editIndex          = slider ? ctx.editIndex          : null
      window.blaudio._pendingButtonIndex = slider ? (slider.button_index ?? null) : null
      window.blaudio._pendingKnobIndex   = slider ? (slider.knob_index   ?? null) : null

      // _populateAndShowDialog fetches running apps, populates the form,
      // and removes 'hidden' from #overlay (which in popup mode is just a container).
      window.blaudio._populateAndShowDialog(slider).then(() => {
        requestAnimationFrame(() => {
          if (window.pywebview)
            window.pywebview.api.resize_popup_to_fit(document.getElementById('dialog').offsetHeight)
        })
      })
    })
  }

  if (window.pywebview) {
    start()
  } else {
    window.addEventListener('pywebviewready', start)
  }
})

'use strict';

// Overrides and bootstrap for the Settings popup window.
// Loaded after settings.js; replaces the methods that interact with the main
// window DOM (overlay visibility, _renderSliders, _initMasterInteractions).
Object.assign(window.blaudio, {

  // Close the popup window instead of hiding an overlay.
  closeSettings() {
    if (window.pywebview) window.pywebview.api.close_popup_window()
  },

  // Apply theme locally (so the popup reflects the choice) and persist.
  // Python's save_ui_setting pushes 'settings_changed' to the main window.
  setTheme(id) {
    this._applyTheme(id)
    this._apiSaveUiSetting('theme', id)
    this._renderThemePicker()
  },

  // Apply layout locally and persist.  No slider re-render needed here.
  setLayout(layout) {
    this._applyLayout(layout)
    this._apiSaveUiSetting('layout', layout)
    this._renderLayoutPicker()
  },

})

// ── Bootstrap ────────────────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
  function start() {
    window.pywebview.api.get_popup_context().then(ctx => {
      window.blaudio._currentTheme  = ctx.theme  || 'dark'
      window.blaudio._currentLayout = ctx.layout || 'vertical'
      window.blaudio._applyTheme(ctx.theme || 'dark')
      window.blaudio._renderThemePicker()
      window.blaudio._renderLayoutPicker()
      window.blaudio._renderPortDetection()
      window.blaudio.state.version = ctx.version || ''
      if (ctx.pendingUpdate) {
        // Update was already found - skip the idle state and go straight to ready.
        window.blaudio._onUpdateAvailable(ctx.pendingUpdate)
      } else {
        window.blaudio._renderUpdateSection()
      }
      document.getElementById('settings-overlay').classList.remove('hidden')
    })
  }

  if (window.pywebview) {
    start()
  } else {
    window.addEventListener('pywebviewready', start)
  }
})

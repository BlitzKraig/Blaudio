'use strict';

// ── App-level methods (init, misc actions) ───────────────────────────────────
// All other behaviour lives in the js/ sub-modules, which extend window.blaudio
// via Object.assign before this file runs.
Object.assign(window.blaudio, {

  init(state) {
    // Prefer server-persisted settings; fall back to localStorage for browser testing.
    this._applyTheme(state.theme   || localStorage.getItem('blaudio-theme')   || 'dark')
    this._applyLayout(state.layout || localStorage.getItem('blaudio-layout') || 'vertical')
    this.state = state
    this._renderMaster()
    this._renderSliders()
    this._initMasterInteractions()
    this._wmInit()
  },

  about() {
    this.showToast(`Blaudio ${this.state.version}`)
  },

})

// ── Bootstrap ────────────────────────────────────────────────────────────────
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
    // Fallback for plain browser testing (no pywebview event fires).
    setTimeout(() => { if (!window.pywebview) start() }, 500)
  }
})

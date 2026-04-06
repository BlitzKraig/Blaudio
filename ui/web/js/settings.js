'use strict';

// Theme and layout settings panel.
Object.assign(window.blaudio, {

  _currentTheme:   'dark',
  _currentLayout:  'vertical',
  _portDetecting:  false,
  _detectedPort:   null,
  _themes: [
    { id: 'dark',      label: 'Dark',      bg: '#1a1a1a', accent: '#9C27B0' },
    { id: 'light',     label: 'Light',     bg: '#f4f4f5', accent: '#9C27B0' },
    { id: 'ocean',     label: 'Ocean',     bg: '#0d1b2a', accent: '#00BCD4' },
    { id: 'synthwave', label: 'Synthwave', bg: '#0a0010', accent: '#e040fb' },
  ],

  async openSettings() {
    if (window.pywebview) { await this._apiOpenSettingsWindow(); return }
    // Browser / mock mode: use the in-page overlay.
    this._renderThemePicker()
    this._renderLayoutPicker()
    this._renderPortDetection()
    document.getElementById('settings-overlay').classList.remove('hidden')
  },

  closeSettings(e) {
    if (!e || e.target.id === 'settings-overlay') {
      document.getElementById('settings-overlay').classList.add('hidden')
    }
  },

  setTheme(id) {
    this._applyTheme(id)
    localStorage.setItem('blaudio-theme', id)   // fallback for browser testing
    this._apiSaveUiSetting('theme', id)
    this._renderThemePicker()
  },

  setLayout(layout) {
    this._applyLayout(layout)
    localStorage.setItem('blaudio-layout', layout)  // fallback for browser testing
    this._apiSaveUiSetting('layout', layout)
    // Sliders and master must be re-initialized: noUiSlider orientation is
    // baked in at creation time and cannot be changed by CSS alone.
    this._renderSliders()
    this._initMasterInteractions()
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

  startPortDetection() {
    this._portDetecting = true
    this._detectedPort  = null
    this._renderPortDetection()
    this._apiStartPortDetection()
  },

  cancelPortDetection() {
    this._portDetecting = false
    this._detectedPort  = null
    this._apiCancelPortDetection()
    this._renderPortDetection()
  },

  async saveDetectedPort() {
    const port = this._detectedPort
    if (!port) return
    await this._apiSaveComPort(port)
    this._detectedPort = null
    this._renderPortDetection()
    this.showToast(`Device saved on ${port}`)
  },

  _onPortDetected(port) {
    this._portDetecting = false
    this._detectedPort  = port
    this._renderPortDetection()
  },

  _onPortDetectionFailed() {
    this._portDetecting = false
    this._detectedPort  = null
    this._renderPortDetection()
    this.showToast('No device found. Make sure it is plugged in and sweep a knob.')
  },

  _renderPortDetection() {
    const el = document.getElementById('port-detect-section')
    if (!el) return
    if (this._portDetecting) {
      el.innerHTML = `
        <div class="detect-row">
          <span class="detect-label">Sweep any knob on your device\u2026</span>
          <button class="btn-flat detect-btn detecting"
                  onclick="blaudio.cancelPortDetection()">Cancel</button>
        </div>`
    } else if (this._detectedPort) {
      el.innerHTML = `
        <div class="detect-row">
          <span class="detect-label">Found on ${this._detectedPort}</span>
          <button class="btn-accent" onclick="blaudio.saveDetectedPort()">Save</button>
          <button class="btn-flat"   onclick="blaudio.cancelPortDetection()">Discard</button>
        </div>`
    } else {
      el.innerHTML = `
        <button class="btn-flat" onclick="blaudio.startPortDetection()">Detect Device</button>`
    }
  },

})

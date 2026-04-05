'use strict';

// Theme and layout settings panel.
Object.assign(window.blaudio, {

  _currentTheme:  'dark',
  _currentLayout: 'vertical',
  _themes: [
    { id: 'dark',      label: 'Dark',      bg: '#1a1a1a', accent: '#9C27B0' },
    { id: 'light',     label: 'Light',     bg: '#f4f4f5', accent: '#9C27B0' },
    { id: 'ocean',     label: 'Ocean',     bg: '#0d1b2a', accent: '#00BCD4' },
    { id: 'synthwave', label: 'Synthwave', bg: '#0a0010', accent: '#e040fb' },
  ],

  openSettings() {
    this._renderThemePicker()
    this._renderLayoutPicker()
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

})

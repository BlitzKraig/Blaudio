'use strict';

// Bootstrap and logic for the Advanced Settings popup window.
Object.assign(window.blaudio, {

  _advancedSettings: {
    autoSaveInterval:  300,
    smoothingWindow:   10,
    callbackInterval:  0.02,
    knobDetectionLow:  10,
    knobDetectionHigh: 90,
  },

  _advancedParams: [
    {
      key:    'AUTO_SAVE_INTERVAL',
      jsKey:  'autoSaveInterval',
      label:  'Auto-save interval',
      unit:   's',
      min: 30, max: 3600, step: 10,
      default: 300,
      tip: 'How often your slider configuration is saved to disk. Lower values reduce the risk of data loss on a crash; the default of 5 minutes is fine for most users.',
    },
    {
      key:    'SMOOTHING_WINDOW',
      jsKey:  'smoothingWindow',
      label:  'Knob smoothing window',
      unit:   'samples',
      min: 1, max: 50, step: 1,
      default: 10,
      tip: 'Number of hardware readings averaged together before updating the volume. Higher = smoother but slightly slower response. Lower = more immediate but can feel jittery on noisy hardware.',
    },
    {
      key:    'CALLBACK_INTERVAL',
      jsKey:  'callbackInterval',
      label:  'Hardware poll interval',
      unit:   's',
      min: 0.005, max: 0.5, step: 0.005,
      default: 0.1,
      tip: 'How frequently (in seconds) knob and button changes are processed. Lower = more responsive UI; higher = less CPU usage at the cost of a little lag.',
    },
    {
      key:    'KNOB_DETECTION_LOW',
      jsKey:  'knobDetectionLow',
      label:  'Knob detect \u2014 low mark',
      unit:   '',
      min: 0, max: 49, step: 1,
      default: 10,
      tip: 'During knob mapping, the knob must reach at or below this value (0\u2013100 scale). Raise it if your hardware cannot physically turn all the way to zero.',
    },
    {
      key:    'KNOB_DETECTION_HIGH',
      jsKey:  'knobDetectionHigh',
      label:  'Knob detect \u2014 high mark',
      unit:   '',
      min: 50, max: 100, step: 1,
      default: 90,
      tip: 'During knob mapping, the knob must reach at or above this value. Lower it if your hardware cannot physically turn all the way to maximum.',
    },
  ],

  _renderAdvancedSection() {
    const el = document.getElementById('advanced-section')
    if (!el) return
    const s = this._advancedSettings
    el.innerHTML = this._advancedParams.map(p => `
      <div class="adv-row">
        <div class="adv-info">
          <span class="adv-label">${p.label}${p.unit ? ' (' + p.unit + ')' : ''}</span>
          <span class="adv-tip">${p.tip}</span>
        </div>
        <input class="dialog-input adv-input"
               type="number" min="${p.min}" max="${p.max}" step="${p.step}"
               value="${s[p.jsKey]}"
               onchange="blaudio._saveAdvancedSetting('${p.key}', this.value)">
        <button class="btn-flat adv-reset"
                title="Reset to default (${p.default}${p.unit ? '\u00a0' + p.unit : ''})"
                onclick="blaudio._resetAdvancedSetting('${p.key}')">&#x21ba;</button>
      </div>`).join('')
  },

  async _saveAdvancedSetting(key, value) {
    const result = await this._apiSaveAdvancedSetting(key, parseFloat(value))
    if (result === false) {
      this.showToast('Invalid value.')
      this._renderAdvancedSection()
    }
    // Browser-testing path: update in-memory state immediately.
    if (!window.pywebview) {
      const param = this._advancedParams.find(p => p.key === key)
      if (param) this._advancedSettings[param.jsKey] = parseFloat(value)
    }
  },

  async _resetAdvancedSetting(key) {
    const param = this._advancedParams.find(p => p.key === key)
    if (!param) return
    const result = await this._apiSaveAdvancedSetting(key, param.default)
    if (result !== false) {
      this._advancedSettings[param.jsKey] = param.default
      this._renderAdvancedSection()
    }
  },

  _onAdvancedSettingChanged(key, value) {
    const param = this._advancedParams.find(p => p.key === key)
    if (param) {
      this._advancedSettings[param.jsKey] = value
      this._renderAdvancedSection()
    }
  },

  closeAdvancedSettings() {
    if (window.pywebview) window.pywebview.api.close_popup_window()
    else window.close()
  },

})

// ── Bootstrap ────────────────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
  function start() {
    if (window.pywebview) {
      window.pywebview.api.get_popup_context().then(ctx => {
        if (ctx.advancedSettings) window.blaudio._advancedSettings = ctx.advancedSettings
        window.blaudio._renderAdvancedSection()
        document.getElementById('settings-overlay').classList.remove('hidden')
        requestAnimationFrame(() => {
          window.pywebview.api.resize_popup_to_fit(document.getElementById('settings-dialog').offsetHeight)
        })
      })
    } else {
      window.blaudio._renderAdvancedSection()
      document.getElementById('settings-overlay').classList.remove('hidden')
    }
  }

  if (window.pywebview) {
    start()
  } else {
    window.addEventListener('pywebviewready', start)
    setTimeout(() => { if (!window.pywebview) start() }, 500)
  }
})

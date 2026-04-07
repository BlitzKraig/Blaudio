'use strict';

// VU meter visualisation - peak bar animation and peak-hold tick logic.
Object.assign(window.blaudio, {

  // Keyed by slider index (or 'master'). Each entry: { value, timer }.
  _peakHold: {},

  // Called by api_bridge when Python pushes a 'peak_levels' event.
  _updatePeakMeters({ master, sliders }) {
    const masterBar  = document.querySelector('#master-vu .vu-bar')
    const masterPeak = document.querySelector('#master-vu .vu-peak')
    this._setPeak('master', master, masterBar, masterPeak)

    sliders.forEach((peak, i) => {
      const col = document.querySelector(`.slider-col[data-index="${i}"]`)
      if (!col) return
      this._setPeak(i, peak, col.querySelector('.vu-bar'), col.querySelector('.vu-peak'))
    })
  },

  // Animate a single VU bar and its peak-hold tick.
  _setPeak(key, peakVal, barEl, peakEl) {
    if (!barEl) return
    const isHoriz = document.body.classList.contains('layout-horizontal')

    // Move bar via GPU-composited transform (avoids layout reflow).
    barEl.style.transform = isHoriz
      ? `translateY(-50%) scaleX(${peakVal})`
      : `translateX(-50%) scaleY(${peakVal})`

    // Peak hold: advance when signal rises, decay after 1.5 s of silence.
    let held = this._peakHold[key]
    if (!held) held = this._peakHold[key] = { value: 0, timer: null }

    if (peakVal >= held.value) {
      held.value = peakVal
      clearTimeout(held.timer)
      held.timer = setTimeout(() => {
        held.value = 0
        if (peakEl) {
          if (isHoriz) peakEl.style.left   = '0%'
          else         peakEl.style.bottom = '0%'
        }
      }, 1500)
    }

    if (peakEl) {
      const pos = `${held.value * 100}%`
      if (isHoriz) peakEl.style.left   = pos
      else         peakEl.style.bottom = pos
    }
  },

})

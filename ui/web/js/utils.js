'use strict';

// Shared UI utilities used by multiple modules.
Object.assign(window.blaudio, {

  _toastTimer: null,

  showToast(message) {
    const toast = document.getElementById('toast')
    toast.textContent = message
    toast.classList.add('visible')
    clearTimeout(this._toastTimer)
    this._toastTimer = setTimeout(() => toast.classList.remove('visible'), 2500)
  },

  // Show the numeric volume readout inside *container*, then fade it out.
  _showVolReadout(container, value) {
    const el = container.querySelector('.vol-readout')
    if (!el) return
    el.textContent = value
    el.classList.add('visible')
    clearTimeout(el._hideTimer)
    el._hideTimer = setTimeout(() => el.classList.remove('visible'), 1200)
  },

})

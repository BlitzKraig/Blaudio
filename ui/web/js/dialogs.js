'use strict';

// Add Slider and Edit Slider modal dialogs, including hardware button detection.
Object.assign(window.blaudio, {

  _editIndex:          null,
  _pendingButtonIndex: null,   // button_index being configured in the open dialog
  _pendingKnobIndex:   null,   // knob_index being configured in the open dialog
  _detecting:          false,  // true while waiting for a hardware button press
  _detectingKnob:      false,  // true while waiting for a hardware knob sweep

  // ── Open dialogs ──────────────────────────────────────────────────

  async openAddSliderDialog() {
    if (window.pywebview) { await this._apiOpenDialogWindow(-1); return }
    // Browser / mock mode: use the in-page overlay.
    this._editIndex          = null
    this._pendingButtonIndex = null
    this._pendingKnobIndex   = null
    await this._populateAndShowDialog(null)
  },

  async openEditSliderDialog(index) {
    if (window.pywebview) { await this._apiOpenDialogWindow(index); return }
    // Browser / mock mode: use the in-page overlay.
    const slider = this.state.sliders[index]
    if (!slider) return
    this._editIndex          = index
    this._pendingButtonIndex = slider.button_index ?? null
    this._pendingKnobIndex   = slider.knob_index   ?? null
    await this._populateAndShowDialog(slider)
  },

  async _populateAndShowDialog(slider) {
    let apps = await this._apiGetRunningApps()

    // For edit: merge in assigned apps that may not currently be running.
    if (slider) {
      slider.app_names.forEach(a => { if (!apps.includes(a)) apps.unshift(a) })
    }

    const list = document.getElementById('app-list')
    list.innerHTML = ''
    apps.forEach(app => {
      const label   = document.createElement('label')
      label.className = 'app-entry'
      const checked = slider && slider.app_names.includes(app) ? 'checked' : ''
      label.innerHTML = `<input type="checkbox" value="${app}" ${checked}><span>${app}</span>`
      list.appendChild(label)
    })

    document.getElementById('slider-name').value              = slider ? slider.name : ''
    document.getElementById('dialog-title').textContent       = slider ? 'Edit Slider' : 'Add Slider'
    document.getElementById('dialog-confirm-btn').textContent = slider ? 'Save' : 'Add'

    this._renderKnobDetectRow()
    this._renderButtonDetectRow()
    document.getElementById('overlay').classList.remove('hidden')
    setTimeout(() => document.getElementById('slider-name').focus(), 50)
  },

  // ── Knob detection ────────────────────────────────────────────────

  _renderKnobDetectRow() {
    const label = document.getElementById('knob-index-label')
    const btn   = document.getElementById('knob-detect-btn')
    if (!label || !btn) return
    label.textContent = this._pendingKnobIndex !== null
      ? `Knob ${this._pendingKnobIndex}`
      : 'None'
    btn.textContent = this._detectingKnob ? 'Sweep knob…' : 'Detect'
    btn.classList.toggle('detecting', this._detectingKnob)
  },

  async _startKnobDetection() {
    this._detectingKnob = true
    this._renderKnobDetectRow()
    await this._apiStartKnobDetection()
  },

  // Called by api_bridge when Python pushes a 'knob_detected' event.
  _onKnobDetected(knobIndex) {
    this._detectingKnob    = false
    this._pendingKnobIndex = knobIndex
    this._renderKnobDetectRow()
  },

  _clearKnobIndex() {
    if (this._detectingKnob) {
      this._detectingKnob = false
      this._apiCancelKnobDetection()
    }
    this._pendingKnobIndex = null
    this._renderKnobDetectRow()
  },

  // ── Button detection ──────────────────────────────────────────────

  _renderButtonDetectRow() {
    const label = document.getElementById('button-index-label')
    const btn   = document.getElementById('button-detect-btn')
    if (!label || !btn) return
    label.textContent = this._pendingButtonIndex !== null
      ? `Button ${this._pendingButtonIndex}`
      : 'None'
    btn.textContent = this._detecting ? 'Listening…' : 'Detect'
    btn.classList.toggle('detecting', this._detecting)
  },

  async _startButtonDetection() {
    this._detecting = true
    this._renderButtonDetectRow()
    await this._apiStartButtonDetection()
  },

  // Called by api_bridge when Python pushes a 'button_detected' event.
  _onButtonDetected(buttonIndex) {
    this._detecting          = false
    this._pendingButtonIndex = buttonIndex
    this._renderButtonDetectRow()
  },

  _clearButtonIndex() {
    if (this._detecting) {
      this._detecting = false
      this._apiCancelButtonDetection()
    }
    this._pendingButtonIndex = null
    this._renderButtonDetectRow()
  },

  // ── Close / confirm ───────────────────────────────────────────────

  closeModal(e) {
    if (!e || e.target.id === 'overlay') {
      // Cancel any in-progress detection when the dialog is dismissed.
      if (this._detecting) {
        this._detecting = false
        this._apiCancelButtonDetection()
      }
      if (this._detectingKnob) {
        this._detectingKnob = false
        this._apiCancelKnobDetection()
      }
      document.getElementById('overlay').classList.add('hidden')
      this._editIndex          = null
      this._pendingButtonIndex = null
      this._pendingKnobIndex   = null
    }
  },

  async confirmSlider() {
    const name = document.getElementById('slider-name').value.trim()
    if (!name) { document.getElementById('slider-name').focus(); return }

    const appNames    = Array.from(document.querySelectorAll('#app-list input:checked')).map(cb => cb.value)
    const knobIndex   = this._pendingKnobIndex   !== null ? this._pendingKnobIndex   : -1
    const buttonIndex = this._pendingButtonIndex !== null ? this._pendingButtonIndex : -1

    if (this._editIndex !== null) {
      const updated = await this._apiEditSlider(this._editIndex, name, appNames, knobIndex, buttonIndex)
      if (updated) {
        this.state.sliders[this._editIndex] = updated
        this._renderSliders()
      }
    } else {
      const newSlider = await this._apiCreateSlider(name, appNames, knobIndex, buttonIndex)
      if (newSlider) {
        this.state.sliders.push(newSlider)
        this._renderSliders()
      }
    }
    this.closeModal()
  },

})

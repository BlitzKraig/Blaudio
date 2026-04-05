'use strict';

// Add Slider and Edit Slider modal dialogs.
Object.assign(window.blaudio, {

  _editIndex: null,

  async openAddSliderDialog() {
    const apps = await this._apiGetRunningApps()

    const list = document.getElementById('app-list')
    list.innerHTML = ''
    apps.forEach(app => {
      const label = document.createElement('label')
      label.className = 'app-entry'
      label.innerHTML = `<input type="checkbox" value="${app}"><span>${app}</span>`
      list.appendChild(label)
    })

    document.getElementById('slider-name').value   = ''
    document.getElementById('knob-select').value   = '-1'
    document.getElementById('dialog-title').textContent       = 'Add Slider'
    document.getElementById('dialog-confirm-btn').textContent = 'Add'
    document.getElementById('overlay').classList.remove('hidden')
    setTimeout(() => document.getElementById('slider-name').focus(), 50)
  },

  async openEditSliderDialog(index) {
    const slider = this.state.sliders[index]
    if (!slider) return

    let apps = await this._apiGetRunningApps()

    // Merge in any assigned apps that may not currently be running.
    slider.app_names.forEach(a => { if (!apps.includes(a)) apps.unshift(a) })

    const list = document.getElementById('app-list')
    list.innerHTML = ''
    apps.forEach(app => {
      const label   = document.createElement('label')
      label.className = 'app-entry'
      const checked = slider.app_names.includes(app) ? 'checked' : ''
      label.innerHTML = `<input type="checkbox" value="${app}" ${checked}><span>${app}</span>`
      list.appendChild(label)
    })

    document.getElementById('slider-name').value             = slider.name
    document.getElementById('knob-select').value             = slider.knob_index ?? -1
    document.getElementById('dialog-title').textContent      = 'Edit Slider'
    document.getElementById('dialog-confirm-btn').textContent = 'Save'
    this._editIndex = index
    document.getElementById('overlay').classList.remove('hidden')
    setTimeout(() => document.getElementById('slider-name').focus(), 50)
  },

  closeModal(e) {
    if (!e || e.target.id === 'overlay') {
      document.getElementById('overlay').classList.add('hidden')
      this._editIndex = null
    }
  },

  async confirmSlider() {
    const name = document.getElementById('slider-name').value.trim()
    if (!name) { document.getElementById('slider-name').focus(); return }

    const appNames  = Array.from(document.querySelectorAll('#app-list input:checked')).map(cb => cb.value)
    const knobIndex = parseInt(document.getElementById('knob-select').value)

    if (this._editIndex !== null) {
      const updated = await this._apiEditSlider(this._editIndex, name, appNames, knobIndex)
      if (updated) {
        this.state.sliders[this._editIndex] = updated
        this._renderSliders()
      }
    } else {
      const newSlider = await this._apiCreateSlider(name, appNames, knobIndex)
      if (newSlider) {
        this.state.sliders.push(newSlider)
        this._renderSliders()
      }
    }
    this.closeModal()
  },

})

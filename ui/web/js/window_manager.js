'use strict';

// Frameless window drag (menubar) and edge/corner resize handling.
Object.assign(window.blaudio, {

  _wm: {
    drag:     null,   // { startScreenX, startScreenY, winX, winY }
    resize:   null,   // { dir, startScreenX, startScreenY, winX, winY, winW, winH }
    pending:  null,   // latest geometry update to flush
    inFlight: false,
  },

  // ── Async "latest wins" flush loop ──────────────────────────────────────────
  // Prevents call pile-up on rapid mousemove events: only the most recent
  // geometry update is sent, and we never send a new one until the previous
  // Python call has returned.

  _wmFlush() {
    const wm = this._wm
    const self = this
    ;(async function flush() {
      while (wm.pending) {
        const p = wm.pending
        wm.pending = null
        if (p.w !== undefined) {
          await self._apiSetWindowGeometry(p.x, p.y, p.w, p.h)
        } else {
          await self._apiMoveWindow(p.x, p.y)
        }
      }
      wm.inFlight = false
    })()
  },

  _wmSchedule(data) {
    this._wm.pending = data
    if (!this._wm.inFlight) {
      this._wm.inFlight = true
      this._wmFlush()
    }
  },

  // ── Drag (menubar) ──────────────────────────────────────────────────────────

  _wmInitDrag() {
    const dragEl = document.getElementById('menubar-drag')
    if (!dragEl) return

    dragEl.addEventListener('mousedown', async (e) => {
      if (e.button !== 0) return
      e.preventDefault()
      const geo = await this._apiGetWindowGeometry()
      this._wm.drag = {
        startScreenX: e.screenX,
        startScreenY: e.screenY,
        winX: geo.x,
        winY: geo.y,
      }
      dragEl.classList.add('dragging')
    })
  },

  // ── Resize handles ──────────────────────────────────────────────────────────

  _wmInitResize() {
    document.querySelectorAll('.resize-handle').forEach(handle => {
      handle.addEventListener('mousedown', async (e) => {
        if (e.button !== 0) return
        e.preventDefault()
        const geo = await this._apiGetWindowGeometry()
        this._wm.resize = {
          dir: handle.dataset.dir,
          startScreenX: e.screenX,
          startScreenY: e.screenY,
          winX: geo.x,
          winY: geo.y,
          winW: geo.width,
          winH: geo.height,
        }
      })
    })
  },

  // ── Global mouse handlers ───────────────────────────────────────────────────

  _wmInitMouseHandlers() {
    const MIN_W = 300, MIN_H = 200

    document.addEventListener('mousemove', (e) => {
      const wm = this._wm

      if (wm.drag) {
        const dx = e.screenX - wm.drag.startScreenX
        const dy = e.screenY - wm.drag.startScreenY
        this._wmSchedule({ x: wm.drag.winX + dx, y: wm.drag.winY + dy })
        return
      }

      if (wm.resize) {
        const r = wm.resize
        const dx = e.screenX - r.startScreenX
        const dy = e.screenY - r.startScreenY
        let x = r.winX, y = r.winY, w = r.winW, h = r.winH

        if (r.dir.includes('e')) w = Math.max(MIN_W, r.winW + dx)
        if (r.dir.includes('s')) h = Math.max(MIN_H, r.winH + dy)
        if (r.dir.includes('w')) {
          const newW = Math.max(MIN_W, r.winW - dx)
          x = r.winX + (r.winW - newW)
          w = newW
        }
        if (r.dir.includes('n')) {
          const newH = Math.max(MIN_H, r.winH - dy)
          y = r.winY + (r.winH - newH)
          h = newH
        }

        this._wmSchedule({ x, y, w, h })
      }
    })

    const endOp = () => {
      const dragEl = document.getElementById('menubar-drag')
      if (dragEl) dragEl.classList.remove('dragging')
      this._wm.drag = null
      this._wm.resize = null
    }

    document.addEventListener('mouseup', endOp)
    // Cancel if focus leaves the window mid-drag (e.g. Alt+Tab)
    window.addEventListener('blur', endOp)

    document.addEventListener('selectstart', (e) => {
      if (this._wm.drag || this._wm.resize) e.preventDefault()
    })
  },

  // ── Entry point ─────────────────────────────────────────────────────────────

  _wmInit() {
    this._wmInitDrag()
    this._wmInitResize()
    this._wmInitMouseHandlers()
  },

})

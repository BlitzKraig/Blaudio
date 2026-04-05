# Blaudio — Claude Code Guide

## Commands

```bash
invoke start       # Run the app
invoke buildEXE    # Package to dist/blaudio.exe via PyInstaller
```

No build step for the UI. Open `ui/web/index.html` directly in any browser for design work — the mock state kicks in automatically when `pywebview` is absent.

## Architecture in brief

- **Arduino → `serial_reader.py`** — parses the serial protocol and smooths knob values
- **`hardware/serial_handler.py`** — translates parsed events into API calls
- **`api.py` (`Api` class)** — the single class exposed to JS via pywebview's `js_api`; manages sliders, wires audio and serial
- **`audio/audio_controller.py`** — pycaw wrapper for master + per-app volume/mute
- **`audio/peak_meter.py`** — background thread pushing peak levels to the UI at ~20fps
- **`tray.py`** — system tray via pystray (daemon thread)
- **`ui/web/`** — plain HTML/CSS/vanilla JS, no framework, no build step

## JS module pattern

All JS files extend the same `window.blaudio` object via `Object.assign`. Load order matters — `index.html` loads them in the right sequence ending with `app.js` which bootstraps everything.

```
js/state.js         ← MOCK_STATE lives here (edit for browser preview)
js/api_bridge.js    ← _receive() and all pywebview.api.* wrappers
js/sliders.js
js/dialogs.js
js/settings.js
js/master_slider.js
js/vu_meter.js
js/utils.js
app.js              ← init(), bootstrap (loaded last)
```

## Python ↔ JS communication

**JS → Python:** call `await this._api*()` wrappers in `api_bridge.js` — these proxy to `window.pywebview.api.*` and no-op gracefully in the browser.

**Python → JS:** `self._push('event_name', {data})` in `api.py` → handled by the `switch` in `_receive()` in `api_bridge.js`.

## Theming

Themes are CSS custom property sets in `style.css`, switched by setting `data-theme` on `<html>`. Tokens include `--vu-low/mid/hi/peak/tick` for the VU meter in addition to the standard bg/text/accent tokens. Adding a theme means adding a `[data-theme="name"]` block to `style.css` and an entry to `_themes` in `js/settings.js`.

## TODO tracking

Open items live in `TODO.md` with `BLA-XXX` IDs. Reference the ID when working on an item. Mark items done with `~~strikethrough~~ ✅ DONE` rather than deleting them.

## Things to know

- **Windows only** — `pycaw` is Windows Core Audio; the app won't run on other platforms.
- **pywebview uses Edge WebView2** — CSS/JS behaves like a modern Chromium browser.
- `blaudio_config.json` is runtime config (COM port etc.) — don't assume its values in code.
- There is no test suite.
- Known broken: horizontal slider layout (`BLA-UI-HORZSLIDERBUG1`) — avoid touching that code path without addressing the underlying bug.
- Version string is currently inconsistent (`BLA-001`) — `version.txt` is the intended source of truth.

# Blaudio

Grouped Windows audio control with custom Arduino hardware. Inspired by [Deej](https://github.com/omriharel/deej).


## What is Blaudio?

Blaudio is a Windows volume mixer controlled by a custom 3D-printed box with **5 potentiometers (knobs)** and **6 buttons**, connected via an Arduino Nano (or ESP32) over serial USB.

You assign running Windows applications to virtual sliders, then control their volume by turning physical knobs - or directly through the GUI. For example, you can put Discord on knob 1, Spotify on knob 2, and assign "All Unassigned" to knob 3 to control game audio without adding every game individually.

The app lives in the system tray when minimized and auto-reconnects after sleep.

## Features

- **Per-app volume control** - assign one or more running applications to each slider
- **"All Unassigned" mode** - a single slider controls every app not explicitly assigned (great for games)
- **Master volume slider** - system-wide volume control mapped to a dedicated knob
- **Hardware knob mapping** - up to 5 potentiometers, each assignable to a slider; use Detect to map by turning the knob
- **Hardware buttons** - 6 buttons for mute toggle, show/hide window, etc.; use Detect to map by pressing the button
- **System tray** - minimizes to tray, runs silently in the background
- **Auto-reconnect** - handles sleep/wake cycles without losing configuration
- **Persistent config** - slider assignments are saved and restored on startup (auto-saves every 5 minutes)
- **Drag-to-reorder** - drag any slider by its title label to reorder; persists automatically
- **Themes** - Dark, Light, Ocean, and Synthwave themes selectable from Settings
- **Horizontal layout** - switch between vertical and horizontal slider orientations in Settings
- **Master mute** - dedicated hardware button to toggle system mute

## Architecture Overview

```
Arduino Nano (USB Serial)          Windows PC
+---------------------+           +---------------------------+
| 5x Potentiometers   |  Serial   | serial_reader.py          |
| 6x Buttons          | -------> |   Parses protocol         |
| BlaudioNano.ino     |  115200   |   Smooths knob values     |
+---------------------+  baud    +---------------------------+
                                          |
                                          v
                                  +---------------------------+
                                  | hardware/                 |
                                  |   serial_handler.py       |
                                  |   Translates events →     |
                                  |   API actions             |
                                  +---------------------------+
                                          |
                                          v
                                  +---------------------------+
                                  | api.py  (Api class)       |
                                  |   Slider management       |
                                  |   JS ↔ Python bridge      |
                                  +---------------------------+
                                       |          |
                              +--------+          +----------+
                              v                              v
                    +------------------+         +------------------+
                    | audio/           |         | tray.py          |
                    |   audio_         |         |   pystray tray   |
                    |   controller.py  |         +------------------+
                    |   peak_meter.py  |
                    +------------------+
                              |
                              v
                    +------------------+
                    | ui/web/          |
                    |   HTML/CSS/JS    |
                    |   pywebview      |
                    +------------------+
```

## Project Structure

```
blaudio.py              App entry point — creates pywebview window, wires tray and serial
api.py                  Public API class exposed to JS via pywebview's js_api
serial_reader.py        Serial communication with Arduino, protocol parsing, value smoothing
slider.py               Slider data model (name, apps, volume, knob index, mute state)
slider_data.py          Persistence layer - saves/loads slider config as JSON
tray.py                 System tray icon (pystray) with show/hide/quit menu
blaudio_config.json     Runtime config (COM port, button/knob assignments, baud rate)
blaudio.spec            PyInstaller build spec for creating standalone exe
tasks.py                Invoke tasks (start, buildEXE, bump)
version.txt             Version info for PyInstaller (currently v0.1.1)

audio/
  audio_controller.py   Wraps pycaw to control master volume/mute and per-app volumes
  peak_meter.py         Background thread polling audio levels at ~20fps, pushes to UI

hardware/
  serial_handler.py     Translates raw serial knob/button events into API actions

ui/web/
  index.html            Main application window (HTML shell)
  style.css             Theme system — Dark, Light, Ocean, Synthwave + noUiSlider overrides
  vendor/               Bundled third-party libraries (noUiSlider 15.8.1, Sortable.js 1.15.6)
  app.js                App init, bootstrap, and window.blaudio namespace assembly
  js/
    api_bridge.js       Python → JS event receiver (_receive) and pywebview.api.* wrappers
    sliders.js          Dynamic slider rendering and drag-to-reorder
    dialogs.js          Add/Edit slider modals and hardware knob/button detection UI
    settings.js         Theme and layout picker, persists UI settings
    master_slider.js    Master volume control and mute interactions
    vu_meter.js         Real-time peak meter rendering
    state.js            UI state management and MOCK_STATE for browser testing
    utils.js            Shared helper utilities

resources/
  storm.ico             Application icon

Arduino/
  Nano/BlaudioNano/
    BlaudioNano.ino     Arduino Nano firmware (recommended)
    Config.h            Hardware pin configuration
  ESP32/Blaudio/
    Blaudio.ino         ESP32 firmware (outdated, not recommended)
```

## Serial Protocol

The Arduino sends data to the PC at 115200 baud in this format:

```
VER{version}#BTN{b0}|{b1}|{b2}|{b3}|{b4}|{b5}#KNOB{k0}|{k1}|{k2}|{k3}|{k4}#
```

Example:

```
VER1#BTN0|1|0|1|0|1#KNOB512|712|923|100|234#
```

| Field | Description |
| -------- | ------------- |
| `VER` | Protocol version (must be >= 1) |
| `BTN` | Button states separated by `\|` (0 = pressed, 1 = released; buttons use INPUT_PULLUP) |
| `KNOB` | Raw analog values 0-1023, separated by `\|` |

The PC sends a **heartbeat** (`BLAUDIO_HEARTBEAT\n`) every 5 seconds. If the Arduino doesn't receive a heartbeat within 15 seconds, it resets its serial connection (Nano) or restarts entirely (ESP32) - this is why the Nano is recommended.

Knob values are smoothed on the PC side using a rolling average over 10 samples and mapped from 0-1023 to 0-100.

## Default Hardware Pin Mapping

### Arduino Nano (Config.h)

| Component | Pin | Index |
| --------- | --- | ----- |
| Knob 0 | A0 | Mapped to Master Volume by default |
| Knob 1 | A1 | Assignable to any slider |
| Knob 2 | A2 | Assignable to any slider |
| Knob 3 | A3 | Assignable to any slider |
| Knob 4 | A4 | Assignable to any slider |
| Button 0 | D7 | Master Mute toggle |
| Button 1 | D6 | Unassigned (shows notification) |
| Button 2 | D5 | Unassigned (shows notification) |
| Button 3 | D4 | Show/Hide window toggle |
| Button 4 | D3 | Unassigned (shows notification) |
| Button 5 | D2 | Unassigned (shows notification) |

### Default blaudio_config.json

```json
{
    "COM_PORT": "COM6",
    "MASTER_KNOB_INDEX": 0,
    "MUTE_BUTTON_INDEX": 0,
    "SHOW_HIDE_BUTTON_INDEX": 3,
    "BAUD_RATE": 115200
}
```

## Dependencies

**Python packages:**

- **pywebview** - Embeds a WebView2 (Edge Chromium) window; exposes `Api` class to JS
- **pystray** - System tray icon (pure Python, no Qt required)
- **Pillow** - Icon image loading for pystray
- **pycaw** - Windows Core Audio API (per-app volume control)
- **pyserial** - Serial communication with Arduino
- **comtypes** - COM interface access (used by pycaw)
- **numpy** - Knob value smoothing (rolling average)

**Build tools:**

- **PyInstaller** - Standalone exe packaging
- **invoke** - Task runner (`invoke start`, `invoke buildEXE`, `invoke bump`)

## Installation

### For users

1. Download and unzip the latest release
2. Edit `blaudio_config.json` with your device's COM port (find it in Device Manager or Arduino IDE)
3. Run the exe

You may need to whitelist the exe in Windows Defender since it's bundled with PyInstaller.

To start Blaudio on login, create a shortcut in:

```
%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup
```

(Type `shell:startup` in Run dialog - Win+R)

### For developers

1. Clone the repo
2. Create and activate a virtual environment, then install dependencies:

   ```
   pip install -r requirements.txt
   ```

3. Use invoke tasks:
   - `invoke start` - Run the app
   - `invoke buildEXE` - Build standalone exe with PyInstaller
   - `invoke bump --version X.Y.Z` - Update the version number across all project files

### Hardware setup

1. Open `Arduino/Nano/BlaudioNano/Config.h`
2. Update `KNOB_COUNT`, `analogInputs`, `BUTTON_COUNT`, and `digitalInputs` to match your wiring
3. A typical setup:

   ```cpp
   const int KNOB_COUNT = 5;
   const int analogInputs[KNOB_COUNT] = {A0, A1, A2, A3, A4};
   const int BUTTON_COUNT = 6;
   const int digitalInputs[BUTTON_COUNT] = {2, 3, 4, 5, 6, 7};
   ```

4. Open `Arduino/Nano/BlaudioNano/BlaudioNano.ino` in the Arduino IDE
5. Select your board, connect it, and click Upload
6. Verify with the Serial Monitor (close it before running Blaudio)
7. Back up your `Config.h` for future updates - just replace the new one with yours

**Note:** An Arduino Nano is recommended over an ESP32. The Nano gracefully re-establishes serial on heartbeat timeout, while the ESP32 does a full device restart.

## UI Development

The UI lives entirely in `ui/web/` — plain HTML, CSS, and vanilla JavaScript. No build step, no framework, no tooling required. You can open `ui/web/index.html` directly in any browser to work on the design.

**Bundled vendor libraries** (in `ui/web/vendor/`, no CDN required):

| Library | Version | Purpose |
| ------- | ------- | ------- |
| [noUiSlider](https://refreshless.com/nouislider/) | 15.8.1 | Custom range sliders — coloured fill track, styled via CSS custom properties |
| [Sortable.js](https://sortablejs.github.io/Sortable/) | 1.15.6 | Animated drag-to-reorder for slider columns — spring-eased "make room" transitions |

### Files

| File | Purpose |
| ---- | ------- |
| `ui/web/index.html` | HTML shell: menubar, master panel, slider area, add-slider dialog, toast |
| `ui/web/style.css` | Theme system: CSS custom properties for Dark, Light, Ocean, and Synthwave themes; noUiSlider overrides |
| `ui/web/vendor/` | Bundled third-party libraries (noUiSlider 15.8.1) |
| `ui/web/app.js` | App init and bootstrap; assembles `window.blaudio` from the modules below |
| `ui/web/js/api_bridge.js` | `_receive()` event handler and all `pywebview.api.*` call wrappers |
| `ui/web/js/sliders.js` | Dynamic slider rendering; Sortable.js drag-to-reorder with animated transitions |
| `ui/web/js/dialogs.js` | Add/Edit slider modals and hardware button detection UI |
| `ui/web/js/settings.js` | Theme and layout picker; persists choices to server and localStorage |
| `ui/web/js/master_slider.js` | Master volume control and mute button interactions |
| `ui/web/js/vu_meter.js` | Real-time peak meter rendering with peak-hold tick |
| `ui/web/js/state.js` | UI state management and `MOCK_STATE` for browser testing |
| `ui/web/js/utils.js` | Shared helper utilities (toast notifications, formatting, etc.) |

### Browser-first development

`js/state.js` defines a `MOCK_STATE` object with sample sliders. When `index.html` is opened directly in a browser (without pywebview), the UI initialises from this mock data instead of calling Python. This means you can iterate on layout and styling entirely in your browser — no Python runtime needed.

```javascript
// js/state.js — edit this to change the design preview data
const MOCK_STATE = {
  version: 'v0.1.1',
  masterVolume: 50,
  masterMute: false,
  sliders: [
    { name: 'Chrome',  volume: 70, mute: false, knob_index: 1, app_names: ['chrome.exe'] },
    ...
  ],
}
```

### Theming with CSS custom properties

All design tokens are defined as CSS variables at the top of `style.css`. Change them in one place to retheme the whole app:

```css
:root {
  --bg-primary:    #1a1a1a;   /* main window background */
  --bg-secondary:  #222222;   /* panel/card background  */
  --bg-hover:      #2a2a2a;   /* hover state */
  --bg-input:      #2d2d2d;   /* input fields */
  --accent:        #9C27B0;   /* purple — buttons, sliders, focus rings */
  --accent-hover:  #AB47BC;
  --danger:        #e53935;   /* delete / muted state */
  --text-primary:  #e0e0e0;
  --text-secondary:#9e9e9e;
  --text-muted:    #4a4a4a;
  --divider:       #2e2e2e;
  --vu-low:        #00e676;   /* VU meter — safe level  */
  --vu-mid:        #ffee58;   /* VU meter — caution     */
  --vu-hi:         #ff9800;   /* VU meter — warning     */
  --vu-peak:       #f44336;   /* VU meter — peak/clip   */
  --vu-tick:       rgba(255,255,255,0.9); /* peak-hold tick */
}
```

### How Python and JS communicate

`Api` (in `api.py`) is a plain Python class registered as pywebview's `js_api`. Every public method on `Api` becomes callable from JS as `await window.pywebview.api.method_name(args)`.

**JS → Python (user actions):**

```javascript
// Call a Python method and await its return value
const state = await window.pywebview.api.get_initial_state()
await window.pywebview.api.set_master_volume(75)
const muted = await window.pywebview.api.toggle_master_mute()
```

**Python → JS (hardware updates):**

```python
# api.py — push a real-time event to the frontend
self._push('master_volume', {'volume': knob_value})
self._push('notification',  {'message': 'Button 0 pressed'})
```

```javascript
// js/api_bridge.js — handle incoming events
_receive(payload) {
  const { event, data } = payload
  switch (event) {
    case 'master_volume': this._syncMasterSlider(data.volume); break
    case 'notification':  this.showToast(data.message);        break
  }
}
```

To add a new Python-callable action: add a public method to `Api` in `api.py`.
To push a new event type to JS: call `self._push('event_name', {...})` from Python and add a `case` to `_receive()` in `js/api_bridge.js`.

### Swapping the UI framework

The `ui/web/` directory is self-contained. To replace the UI with a different framework (React, Vue, Svelte, etc.):

1. Build your new UI so it produces a static `index.html` (and any assets) in `ui/web/`
2. Keep the `window.blaudio` namespace: `init(state)` (entry point in `app.js`), `_receive(payload)` (event handler in `js/api_bridge.js`), and the `window.pywebview.api.*` call sites
3. The Python side (`api.py`) does not need to change

## How It Works

### Startup

1. Loads config from `blaudio_config.json`
2. Restores saved slider assignments from `slider_data.json` and `master_slider_data.json`
3. Creates a pywebview window pointing at `ui/web/index.html`, registering `Api` as `js_api`
4. Connects to Arduino via serial (daemon thread)
5. Creates system tray icon (pystray, daemon thread)
6. Starts auto-save timer (every 5 minutes)

### Runtime

- Arduino sends knob/button data every 10ms
- `serial_reader.py` parses the protocol and smooths knob values
- Knob changes call `api._push()` to update the JS frontend in real time
- Slider changes are applied to Windows audio sessions via pycaw
- Button presses trigger mute toggle, show/hide, or notifications
- Configuration is auto-saved periodically and on quit

### Adding a slider

1. Click "Add Slider" in the toolbar
2. Enter a name for the slider
3. Select running applications from the checklist (or choose "All Unassigned")
4. Optionally assign a hardware knob — click **Detect** and sweep the knob from min to max
5. Optionally assign a hardware mute button — click **Detect** and press the button
6. The slider appears in the scrollable area and persists across restarts

## Current Status

**Version:** 0.1.1 (early development)

**Known limitations:**

- Some button indices are unassigned (show a notification when pressed)
- Horizontal slider layout has a known rendering issue (BLA-UI-HORZSLIDERBUG1)

## License

GNU General Public License v3.0 - see [LICENSE](LICENSE)

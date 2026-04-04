# Blaudio

Grouped Windows audio control with custom Arduino hardware. Inspired by [Deej](https://github.com/omriharel/deej).

> This is the first thing I've ever built with Python - the structure is not ideal. Improvements welcome.

## What is Blaudio?

Blaudio is a Windows volume mixer controlled by a custom 3D-printed box with **5 potentiometers (knobs)** and **6 buttons**, connected via an Arduino Nano (or ESP32) over serial USB.

You assign running Windows applications to virtual sliders, then control their volume by turning physical knobs - or directly through the GUI. For example, you can put Discord on knob 1, Spotify on knob 2, and assign "All Unassigned" to knob 3 to control game audio without adding every game individually.

The app lives in the system tray when minimized and auto-reconnects after sleep.

## Features

- **Per-app volume control** - assign one or more running applications to each slider
- **"All Unassigned" mode** - a single slider controls every app not explicitly assigned (great for games)
- **Master volume slider** - system-wide volume control mapped to a dedicated knob
- **Hardware knob mapping** - up to 5 potentiometers, each assignable to a slider
- **Hardware buttons** - 6 buttons for mute toggle, show/hide window, etc.
- **System tray** - minimizes to tray, runs silently in the background
- **Auto-reconnect** - handles sleep/wake cycles without losing configuration
- **Persistent config** - slider assignments are saved and restored on startup (auto-saves every 5 minutes)
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
                                  | api.py  (Api class)       |
                                  |   pycaw audio control     |
                                  |   Slider management       |
                                  |   JS ↔ Python bridge      |
                                  +---------------------------+
                                       |          |
                              +--------+          +----------+
                              v                              v
                    +------------------+         +------------------+
                    | ui/web/          |         | tray.py          |
                    |   HTML/CSS/JS    |         |   pystray tray   |
                    |   pywebview      |         +------------------+
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
tasks.py                Invoke tasks (start, buildEXE)
version.txt             Version info for PyInstaller (currently v0.0.7)

ui/web/
  index.html            Main application window (HTML shell)
  style.css             Dark theme with CSS custom properties (design tokens)
  app.js                All UI logic — window.blaudio namespace, Python↔JS bridge

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
|-------|-------------|
| `VER` | Protocol version (must be >= 1) |
| `BTN` | Button states separated by `\|` (0 = pressed, 1 = released; buttons use INPUT_PULLUP) |
| `KNOB` | Raw analog values 0-1023, separated by `\|` |

The PC sends a **heartbeat** (`BLAUDIO_HEARTBEAT\n`) every 5 seconds. If the Arduino doesn't receive a heartbeat within 15 seconds, it resets its serial connection (Nano) or restarts entirely (ESP32) - this is why the Nano is recommended.

Knob values are smoothed on the PC side using a rolling average over 10 samples and mapped from 0-1023 to 0-100.

## Default Hardware Pin Mapping

### Arduino Nano (Config.h)

| Component | Pin | Index |
|-----------|-----|-------|
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
- **invoke** - Task runner (`invoke start`, `invoke buildEXE`)

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
   pip install pywebview pystray Pillow pycaw pyserial comtypes numpy invoke pyinstaller
   ```
3. Use invoke tasks:
   - `invoke start` - Run the app
   - `invoke buildEXE` - Build standalone exe with PyInstaller

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

### Files

| File | Purpose |
|------|---------|
| `ui/web/index.html` | HTML shell: menubar, master panel, slider area, add-slider dialog, toast |
| `ui/web/style.css` | Dark theme using CSS custom properties (design tokens) |
| `ui/web/app.js` | All UI logic in the `window.blaudio` namespace |

### Browser-first development

`app.js` includes a `MOCK_STATE` object at the top with sample sliders. When `index.html` is opened directly in a browser (without pywebview), the UI initialises from this mock data instead of calling Python. This means you can iterate on layout and styling entirely in your browser — no Python runtime needed.

```javascript
// app.js — edit this to change the design preview data
const MOCK_STATE = {
  version: 'v0.0.7',
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
  --bg-tertiary:   #2a2a2a;   /* input/hover background */
  --accent:        #9C27B0;   /* purple — buttons, sliders, focus rings */
  --accent-hover:  #AB47BC;
  --danger:        #e53935;   /* delete / muted state */
  --text-primary:  #e0e0e0;
  --text-muted:    #888888;
  --border:        #333333;
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
// app.js — handle incoming events
_receive(payload) {
  const { event, data } = payload
  switch (event) {
    case 'master_volume': this._syncMasterSlider(data.volume); break
    case 'notification':  this.showToast(data.message);        break
  }
}
```

To add a new Python-callable action: add a public method to `Api` in `api.py`.
To push a new event type to JS: call `self._push('event_name', {...})` from Python and add a `case` to `_receive()` in `app.js`.

### Swapping the UI framework

The `ui/web/` directory is self-contained. To replace the UI with a different framework (React, Vue, Svelte, etc.):

1. Build your new UI so it produces a static `index.html` (and any assets) in `ui/web/`
2. Keep the `window.blaudio` namespace: `init(state)`, `_receive(payload)`, and the `window.pywebview.api.*` call sites
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
4. Optionally assign a hardware knob (0-4)
5. The slider appears in the scrollable area and persists across restarts

## Current Status

**Version:** 0.0.7 (early development)

**Known limitations:**
- Edit slider functionality is not yet implemented (button exists but shows a toast)
- Settings menu is present but does nothing
- Some button indices are unassigned (show a notification when pressed)

## License

GNU General Public License v3.0 - see [LICENSE](LICENSE)

# Blaudio - TODO

Items are identified by `BLA-XXX`. Reference an ID directly to have it worked on.

**Categories:** `bug` `feature` `improvement` `housekeeping`

---

## Bugs

### BLA-001 · Version mismatch `bug`

`blaudio.py` hardcodes `v0.0.3` (line 103) but `version.txt` and the README both state `0.0.7`.
The version string should be read from a single source of truth (e.g. `version.txt`).

### ~~BLA-002 · README still references pickle files~~ ✅ DONE

Updated README to reference `slider_data.json` and `master_slider_data.json`.

### BLA-003 · Thread safety on serial data `bug`

`serial_reader.py` writes to `self.knobs` and `self.buttons` from a daemon thread.
`blaudio.py` reads the same dicts in `on_serial_update()` on the Qt thread.
No lock or thread-safe structure is used - could cause a race condition under load.


---

## Features

### ~~BLA-004 · Edit slider functionality `feature`~~

The Edit button on each slider fires a "coming soon" notification (line 227).
Should open a dialog pre-populated with the slider's current name, apps, and knob assignment,
matching the existing Create Slider dialog flow.

### ~~BLA-005 · Settings menu `feature`~~

`ui.actionSettings.setEnabled(False)` (line 101) - the menu item exists but does nothing.
Candidates for a settings panel: auto-save interval, smoothing window size, notification duration,
COM port override without editing JSON directly.

### ~~BLA-006 · Configurable button actions `feature`~~

Buttons 1, 2, 4, and 5 currently only show a "Button X pressed" notification.
A settings panel (see BLA-005) or an extended `blaudio_config.json` schema could let users bind
actions (open mixer, mute a specific slider, etc.) to each unassigned button.
The commented-out `open_windows_volume_mixer` binding (line 141) is a ready example.

Updated: Buttons are now mappable for slider mute

### BLA-007 · Single-instance enforcement `feature`

There is a `# TODO: Add a check to see if the app is already running` comment in `__main__`
(line 343). Launching a second instance silently competes for the serial port and save files.
A mutex or socket-based check would prevent this.


### ~~BLA-UI-STYLE-1 - Add themes, selectable in Settings~~

With our new web-based UI, we can use CSS and JS to create multiple themes, which the user can switch between.
The initial theme pack should consist of the current theme, an alternative colour theme, a light theme, and a theme with horizontal sliders instead of vertical.
The horizontal/vertical sliders can be controlled by another setting if that is more sensible.

### ~~BLA-UI-HARDWAREKNOBDETECT-1~~ ✅ DONE

When adding or editing a slider, we should provide a detect knob option. This will allow the user to interact with a knob to select that knob as the knob to tie to this slider.
Since we are constantly updating values, and sometimes a knob may be between two values, causing noise, we should design this in such a way that it only reacts to clearly intentional knob changes, such as "move knob to min then max" (though with a window in case a knob cannot reach full min or max due to hardware issues)

---

## Improvements

### BLA-008 · Centralise magic constants `improvement`

Several values are hardcoded across files with no easy way for users to tune them:

- Auto-save interval: `300000` ms (`blaudio.py` line 59)
- Notification display duration: `2000` ms (`blaudio.py` line 262)
- Fade animation duration: `300` / `1000` ms (`blaudio.py` lines 270, 278)
- Smoothing window: `10` samples (`serial_reader.py` line 11)
- Callback interval: `0.02` s (`serial_reader.py` line 11)

These belong either in a `constants.py` module or in the user-facing settings (see BLA-005).

### BLA-009 · Extract duplicate audio session logic `improvement`

`toggle_mute()` and `change_volume()` (lines 283–329) both iterate `AudioUtilities.GetAllSessions()`
with identical branching for Master / All Unassigned / named app.
Extracting a shared `apply_to_sessions(slider_object, fn)` helper would halve the duplicated code
and make future audio changes a single edit.

### BLA-010 · Replace numpy with stdlib for smoothing `improvement`

`numpy` is imported solely to compute a mean over a 10-element `deque` (line 86–88).
`statistics.mean()` or a plain `sum() / len()` achieves the same result, removes the numpy
dependency, and marginally reduces the packaged exe size.

### BLA-011 · Improve serial message parsing robustness `improvement`

The protocol is parsed with chained `.split()` calls and no format validation (lines 72–93).
A malformed or partial line falls through to a bare `except IndexError: pass` which silently
discards the error. A regex match with an explicit format check would catch corruption early
and make the `except` block meaningful.

### BLA-012 · Replace `print()` with `logging` `improvement`

Debug output uses `print()` throughout (`serial_reader.py`, `blaudio.py`).
Using Python's `logging` module would allow log levels, optional file output, and cleaner
production behaviour in the packaged exe.

### BLA-013 · Performance: pre-build knob→slider lookup `improvement`

`on_serial_update()` iterates all knobs × all sliders on every callback (tagged with
`# TODO: Improve the performance of this` on line 119).
Building a `{knob_index: slider_object}` dict whenever sliders are added or removed
would reduce this to O(knobs) per callback.

### BLA-014 · Bare `except` in serial connect `improvement`

`serial_reader.py` line 51 uses a bare `except: pass` when closing the port before reconnect.
Should be `except serial.SerialException` (or at minimum `except Exception`) so unexpected
errors are not silently swallowed.

### ~~BLA-UI-REF1 · Current UI design tooling is untenable~~ ✅ DONE

Migrated from PySide6 + QML to **PyWebView + pystray**. UI lives in `ui/web/` as plain
HTML/CSS/vanilla JS - open `index.html` directly in any browser for design work (mock state
provided). No Qt, no kit setup, no code generation. `PySide6` replaced by `pywebview`,
`pystray`, and `Pillow`.

### ~~BLA-UI-SLIDERARRANGE-1~~ ✅ DONE

Drag the slider label to reorder sliders. Live reorder updates the UI as you drag; order
is committed to `slider_data.json` on drop via `api.reorder_sliders()`. ESC during drag
restores the original order. Works in both vertical and horizontal layout modes.

### BLA-UI-SLIDERINTERACT-1

Sliders with an attached hardware knob should not be interactable in the UI, as this causes UI jumping.

---

## Housekeeping

### BLA-015 · Add `requirements.txt` `housekeeping`

There is no `requirements.txt` or `pyproject.toml`. New contributors must guess dependencies.
Should pin at minimum: `pywebview`, `pystray`, `Pillow`, `pycaw`, `pyserial`, `comtypes`,
`numpy`, `invoke`, `PyInstaller`.

### ~~BLA-016 · Add `.ui` source files to version control~~ ✅ SUPERSEDED

Resolved by BLA-UI-REF1 migration. `ui/web/` files are plain HTML/CSS/JS committed directly.

### BLA-017 · Knob count in Create Slider dialog is hardcoded `housekeeping`

The knob dropdown in `create_slider()` hardcodes `range(0, 9)` (line 178), regardless of
how many knobs the hardware actually has. It should read from config or match the
hardware's reported knob count.

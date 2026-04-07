# Blaudio - TODO

Items are identified by `BLA-XXX`. Reference an ID directly to have it worked on.

**Categories:** `bug` `feature` `improvement` `housekeeping`

---

## Bugs

### BLA-001 · Version mismatch `bug`

`api.py` hardcodes the version string (e.g. `v0.1.2`) in the `Api` constructor instead of reading
from `version.txt`. The version string should be read from a single source of truth (`version.txt`).

### ~~BLA-002 · README still references pickle files~~ ✅ DONE

Updated README to reference `slider_data.json` and `master_slider_data.json`.

### BLA-003 · Thread safety on serial data `bug`

`serial_reader.py` writes to `self.knobs` and `self.buttons` from the `read_from_port` daemon thread
with no lock or thread-safe structure. The callback is called synchronously on that same thread so
normal operation is safe, but a reconnect can spawn a new `read_from_port` thread while
`_connection_loop` is still running, giving two threads concurrent access to those dicts.


---

## Features

### ~~BLA-004 · Edit slider functionality `feature`~~ ✅ DONE

Edit button opens `dialog.html` pre-populated with the slider's current name, apps, knob
assignment, and button mapping - matching the Create Slider dialog flow.

### ~~BLA-005 · Settings menu `feature`~~ ✅ DONE

Settings panel implemented in `ui/web/js/settings.js` with theme selection, layout toggle,
COM port override, and other options accessible from the tray icon.

### ~~BLA-006 · Configurable button actions `feature`~~ ✅ DONE

Buttons are now mappable to slider mute actions via the Edit Slider dialog.
Unassigned buttons show a notification prompting the user to map them.

### BLA-007 · Single-instance enforcement `feature`

Launching a second instance silently competes for the serial port and save files.
A mutex or socket-based check in `blaudio.py` would prevent this.


### ~~BLA-UI-STYLE-1 · Add themes, selectable in Settings~~ ✅ DONE

Four themes implemented (`dark`, `light`, `ocean`, `synthwave`) via CSS custom property blocks in
`style.css` and a theme picker in `js/settings.js`. Horizontal layout is a separate setting.

### ~~BLA-UI-HARDWAREKNOBDETECT-1~~ ✅ DONE

When adding or editing a slider, we should provide a detect knob option. This will allow the user to interact with a knob to select that knob as the knob to tie to this slider.
Since we are constantly updating values, and sometimes a knob may be between two values, causing noise, we should design this in such a way that it only reacts to clearly intentional knob changes, such as "move knob to min then max" (though with a window in case a knob cannot reach full min or max due to hardware issues)

---

## Improvements

### BLA-008 · Centralise magic constants `improvement`

Several values are hardcoded across files with no easy way for users to tune them:

- Auto-save interval: `300` s (`api.py` autosave timer)
- Smoothing window: `10` samples (`serial_reader.py` default arg)
- Callback interval: `0.02` s (`serial_reader.py` default arg)
- Knob detection thresholds: `_KNOB_LOW = 10`, `_KNOB_HIGH = 90` (`hardware/serial_handler.py`)

These belong either in a `constants.py` module or in the user-facing settings (see BLA-005).

### ~~BLA-009 · Extract duplicate audio session logic~~ ✅ DONE

Audio control is now centralised in `AudioController` (`audio/audio_controller.py`). `api.py` delegates
to `_audio.apply_slider_mute/volume()` - no duplicated session iteration.

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

### ~~BLA-013 · Performance: pre-build knob→slider lookup~~ ✅ DONE

`on_serial_update()` in `hardware/serial_handler.py` checks the master slider first (O(1)), then
short-circuits to a per-slider loop only when needed. The `# TODO` comment is gone and the
old all-knobs×all-sliders iteration has been replaced.

### ~~BLA-014 · Bare `except` in serial connect~~ ✅ DONE

All bare `except:` clauses in `serial_reader.py` have been replaced with `except Exception:`.
Could be narrowed further to `serial.SerialException` but no longer silently swallows all exceptions.

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
`sliders.js` already disables the noUiSlider element when `slider.mute` is true, so the disable
mechanism exists - it just needs to also trigger when `slider.knob_index` is set.

---

## Housekeeping

### ~~BLA-015 · Add `requirements.txt`~~ ✅ DONE

`requirements.txt` exists and lists all runtime dependencies.

### ~~BLA-016 · Add `.ui` source files to version control~~ ✅ SUPERSEDED

Resolved by BLA-UI-REF1 migration. `ui/web/` files are plain HTML/CSS/JS committed directly.

### ~~BLA-017 · Knob count in Create Slider dialog is hardcoded~~ ✅ DONE

Resolved by BLA-UI-HARDWAREKNOBDETECT-1. The dialog now uses a hardware detect button
(`_startKnobDetection()`) instead of a hardcoded dropdown range.

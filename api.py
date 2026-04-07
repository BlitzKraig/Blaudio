import os
import sys
import json
import time
import threading
import webview
from screeninfo import get_monitors

from audio.audio_controller import ensure_com, AudioController
from audio.peak_meter import PeakMeter
from hardware.serial_handler import SerialHandler
from slider_data import SliderData
from serial_reader import SerialReader
from slider import Slider
from updater import Updater


def screen_center_x(width):
    monitors = get_monitors()
    if monitors:
        m = monitors[0]
        return (m.width - width) // 2 + m.x
    return 100


def screen_center_y(height):
    monitors = get_monitors()
    if monitors:
        m = monitors[0]
        return (m.height - height) // 2 + m.y
    return 100


class Api:
    """
    Public methods on this class are exposed to JavaScript via pywebview.

    Responsibilities:
      - Owns application state (sliders, master volume/mute, UI settings)
      - Exposes the JS-callable API surface
      - Wires together AudioController, PeakMeter, SerialHandler, SerialReader
      - Pushes server-side events back to the JS UI
    """

    _ADVANCED_SETTING_SCHEMA = {
        'AUTO_SAVE_INTERVAL':  (30,    3600,  int),
        'SMOOTHING_WINDOW':    (1,     50,    int),
        'CALLBACK_INTERVAL':   (0.005, 2,   float),
        'KNOB_DETECTION_LOW':  (0,     49,    int),
        'KNOB_DETECTION_HIGH': (50,    100,   int),
    }

    def __init__(self):
        if getattr(sys, 'frozen', False):
            self._app_path = os.path.dirname(sys.executable)
            self._ui_path  = sys._MEIPASS          # bundled ui/web/ lives here
        else:
            self._app_path = os.path.dirname(os.path.abspath(__file__))
            self._ui_path  = self._app_path        # dev: ui/web/ is next to api.py

        with open(os.path.join(self._app_path, 'blaudio_config.json')) as f:
            self.config = json.load(f)

        self.config.setdefault('AUTO_SAVE_INTERVAL', 300)
        self.config.setdefault('SMOOTHING_WINDOW',    10)
        self.config.setdefault('CALLBACK_INTERVAL',   0.02)
        self.config.setdefault('KNOB_DETECTION_LOW',  10)
        self.config.setdefault('KNOB_DETECTION_HIGH', 90)

        self._ui_settings_path = os.path.join(self._app_path, 'ui_settings.json')
        try:
            with open(self._ui_settings_path) as f:
                self._ui_settings = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            self._ui_settings = {}

        self._window             = None
        self._popup_window       = None
        self._pending_edit_index = -1
        self._visible    = True
        self._force_quit = False
        self._version    = 'v0.1.2'

        # ── State ────────────────────────────────────────────────────
        self._sliders       = []
        self._master_slider = None
        self._master_volume = 50
        self._master_mute   = False

        # ── Dependencies ─────────────────────────────────────────────
        self._audio       = AudioController()
        self._peak_meter  = None   # created in set_window() once we have the window

        slider_data = SliderData(self)
        loaded_master = slider_data.load_master()
        if loaded_master:
            self._master_slider = loaded_master
            self._master_volume = loaded_master.volume
            self._master_mute   = loaded_master.mute
        else:
            self._master_slider = Slider(
                'Master Volume', ['Blaudio: Master Volume'], 50,
                knob_index=self.config['MASTER_KNOB_INDEX'],
            )

        slider_data.load()
        self._slider_data = slider_data

        self._save_timer = None
        self._schedule_save()

        self._port_detection_active = False

        # ── Auto-updater (frozen exe only) ───────────────────────────
        self._tray           = None
        self._pending_update = None   # set when update_available fires
        self._updater        = None
        if getattr(sys, 'frozen', False):
            self._updater = Updater(
                current_version=self._version,
                app_exe_path=sys.executable,
                on_event=self._on_updater_event,
            )

        self._serial_handler = SerialHandler(self.config, self)
        self._serial_reader  = SerialReader(
            self.config['COM_PORT'],
            baudrate=self.config['BAUD_RATE'],
            callback=self._serial_handler.on_serial_update,
            message_callback=self._serial_handler.on_message,
            callback_interval=self.config['CALLBACK_INTERVAL'],
            smoothing_window=self.config['SMOOTHING_WINDOW'],
        )

    def set_tray(self, tray):
        self._tray = tray

    def _on_updater_event(self, event, data):
        """Relay updater callbacks to JS (both windows) and the tray icon."""
        self._push(event, data)
        self._push_popup(event, data)
        if event == 'update_available':
            self._pending_update = data
            if self._tray:
                self._tray.notify_update(data['version'])

    def set_window(self, window):
        self._window = window
        self._peak_meter = PeakMeter(
            get_state_fn=lambda: (list(self._sliders), self._master_mute),
            push_fn=self._push,
        )
        self._peak_meter.start()
        if self._updater:
            threading.Timer(3.0, self._updater.check_async).start()

    # ── JS-callable API ──────────────────────────────────────────────

    def get_initial_state(self):
        return {
            'version':      self._version,
            'masterVolume': self._master_volume,
            'masterMute':   self._master_mute,
            'sliders':      [s.serialize() for s in self._sliders],
            'theme':        self._ui_settings.get('theme',  'dark'),
            'layout':       self._ui_settings.get('layout', 'vertical'),
        }

    def save_ui_setting(self, key, value, push=True):
        old_layout = self._ui_settings.get('layout') if key == 'layout' else None
        self._ui_settings[key] = value
        try:
            with open(self._ui_settings_path, 'w') as f:
                json.dump(self._ui_settings, f, indent=2)
        except Exception:
            pass
        if old_layout is not None and old_layout != value and self._window:
            self._on_layout_change(old_layout, value)
        if push:
            self._push('settings_changed', {'key': key, 'value': value})

    def _on_layout_change(self, old_layout, new_layout):
        prefix_old = f'{old_layout}_window_'
        prefix_new = f'{new_layout}_window_'
        self._ui_settings[f'{prefix_old}x'] = self._window.x
        self._ui_settings[f'{prefix_old}y'] = self._window.y
        self._ui_settings[f'{prefix_old}width'] = self._window.width
        self._ui_settings[f'{prefix_old}height'] = self._window.height
        with open(self._ui_settings_path, 'w') as f:
            json.dump(self._ui_settings, f, indent=2)
        new_x = self._ui_settings.get(f'{prefix_new}x')
        new_y = self._ui_settings.get(f'{prefix_new}y')
        new_width = self._ui_settings.get(f'{prefix_new}width')
        new_height = self._ui_settings.get(f'{prefix_new}height')
        if new_x is not None and new_y is not None:
            self._window.move(new_x, new_y)
        if new_width is not None and new_height is not None:
            self._window.resize(new_width, new_height)

    def set_master_volume(self, value):
        ensure_com()
        value = int(value)
        self._master_volume       = value
        self._master_slider.volume = value
        self._audio.apply_master_volume(value)

    def toggle_master_mute(self):
        ensure_com()
        self._master_mute          = not self._master_mute
        self._master_slider.mute   = self._master_mute
        self._audio.apply_master_mute(self._master_mute)
        self._slider_data.save_master(should_notify=False)
        return self._master_mute

    def get_running_apps(self):
        ensure_com()
        return self._audio.get_running_apps()

    def create_slider(self, name, app_names, knob_index, button_index):
        if not name:
            return None
        knob   = None if int(knob_index)    < 0 else int(knob_index)
        btn    = None if int(button_index)  < 0 else int(button_index)
        slider = Slider(name, list(app_names), 50, knob_index=knob, button_index=btn)
        self.add_slider(slider)
        self._slider_data.save(should_notify=False)
        self._push('sliders_changed', {'sliders': [s.serialize() for s in self._sliders]})
        return slider.serialize()

    def edit_slider(self, index, name, app_names, knob_index, button_index):
        index = int(index)
        if not name or not (0 <= index < len(self._sliders)):
            return None
        knob                         = None if int(knob_index)   < 0 else int(knob_index)
        btn                          = None if int(button_index) < 0 else int(button_index)
        slider                       = self._sliders[index]
        slider.name                  = name
        slider.app_names             = list(app_names)
        slider.knob_index            = knob
        slider.button_index          = btn
        self._slider_data.save(should_notify=False)
        self._push('sliders_changed', {'sliders': [s.serialize() for s in self._sliders]})
        return slider.serialize()

    def start_button_detection(self):
        """Tell the serial handler to capture the next button press for mapping."""
        self._serial_handler.start_detection(
            lambda btn: self._push_popup('button_detected', {'button_index': btn})
        )

    def cancel_button_detection(self):
        """Abort an in-progress button detection (e.g. dialog closed)."""
        self._serial_handler.cancel_detection()

    def start_knob_detection(self):
        """Tell the serial handler to capture the next intentional knob sweep for mapping."""
        self._serial_handler.start_knob_detection(
            lambda knob: self._push_popup('knob_detected', {'knob_index': knob})
        )

    def cancel_knob_detection(self):
        """Abort an in-progress knob detection (e.g. dialog closed)."""
        self._serial_handler.cancel_knob_detection()

    def start_port_detection(self):
        """Scan all COM ports for a Blaudio device. Sweep a knob to identify it."""
        if self._port_detection_active:
            return
        self._port_detection_active = True
        self._serial_reader.suspend_for_detection()
        threading.Thread(target=self._run_port_detection, daemon=True).start()

    def cancel_port_detection(self):
        """Abort an in-progress port scan and restore the serial connection."""
        if self._port_detection_active:
            self._port_detection_active = False
            self._serial_reader.resume_from_detection()

    def _run_port_detection(self):
        import serial
        import serial.tools.list_ports
        ports = [p.device for p in serial.tools.list_ports.comports()]

        result     = [None]
        done_event = threading.Event()

        def try_port(port):
            try:
                ser = serial.Serial(port, self.config['BAUD_RATE'], timeout=0.5)
                deadline = time.time() + 30
                while time.time() < deadline and self._port_detection_active and result[0] is None:
                    if ser.in_waiting > 0:
                        try:
                            line = ser.readline().decode('utf-8', errors='ignore').strip()
                            if 'VER' in line and 'KNOB' in line and 'BTN' in line:
                                if result[0] is None:
                                    result[0] = port
                                    done_event.set()
                                break
                        except Exception:
                            pass
                    time.sleep(0.05)
                ser.close()
            except Exception:
                pass

        for port in ports:
            threading.Thread(target=try_port, args=(port,), daemon=True).start()

        done_event.wait(timeout=30)

        if not self._port_detection_active:
            return   # was cancelled; cleanup already done by cancel_port_detection

        self._port_detection_active = False
        self._serial_reader.resume_from_detection()

        if result[0]:
            self._push_popup('port_detected', {'port': result[0]})
        else:
            self._push_popup('port_detection_failed', {})

    def save_com_port(self, port):
        """Persist a new COM port to blaudio_config.json and reconnect."""
        self.config['COM_PORT'] = port
        config_path = os.path.join(self._app_path, 'blaudio_config.json')
        with open(config_path, 'w') as f:
            json.dump(self.config, f, indent=4)
        self._serial_reader.reconnect(port)

    def save_advanced_setting(self, key, value):
        """Persist and live-apply one of the tunable advanced constants."""
        schema = self._ADVANCED_SETTING_SCHEMA.get(key)
        if schema is None:
            return False
        lo, hi, cast = schema
        try:
            value = max(lo, min(hi, cast(value)))
        except (TypeError, ValueError):
            return False
        self.config[key] = value
        config_path = os.path.join(self._app_path, 'blaudio_config.json')
        with open(config_path, 'w') as f:
            json.dump(self.config, f, indent=4)
        if key == 'AUTO_SAVE_INTERVAL':
            if self._save_timer:
                self._save_timer.cancel()
            self._schedule_save()
        elif key == 'SMOOTHING_WINDOW':
            self._serial_reader.smoothing_window = value
            self._serial_reader.knob_buffers = {}
        elif key == 'CALLBACK_INTERVAL':
            self._serial_reader.callback_interval = value
        elif key == 'KNOB_DETECTION_LOW':
            self._serial_handler._KNOB_LOW = value
        elif key == 'KNOB_DETECTION_HIGH':
            self._serial_handler._KNOB_HIGH = value
        self._push('advanced_setting_changed', {'key': key, 'value': value})
        self._push_popup('advanced_setting_changed', {'key': key, 'value': value})
        return True

    def reorder_sliders(self, order):
        order = [int(i) for i in order]
        if sorted(order) != list(range(len(self._sliders))):
            return False
        self._sliders = [self._sliders[i] for i in order]
        self._slider_data.save(should_notify=False)
        return True

    def remove_slider(self, index):
        index = int(index)
        if 0 <= index < len(self._sliders):
            self._sliders.pop(index)
            self._slider_data.save(should_notify=False)
            return True
        return False

    def set_slider_volume(self, index, value):
        ensure_com()
        index, value = int(index), int(value)
        if 0 <= index < len(self._sliders):
            self._sliders[index].volume = value
            self._audio.apply_slider_volume(value, self._sliders[index], self._sliders)

    def toggle_slider_mute(self, index):
        ensure_com()
        index = int(index)
        if 0 <= index < len(self._sliders):
            self._sliders[index].mute = not self._sliders[index].mute
            self._audio.apply_slider_mute(self._sliders[index], self._sliders)
            self._slider_data.save(should_notify=False)
            return self._sliders[index].mute
        return False

    def check_for_update(self):
        """JS-callable: manually trigger an update check."""
        if self._updater:
            self._updater.check_async()

    def download_update(self, download_url, size):
        """JS-callable: begin downloading the queued update."""
        if self._updater:
            self._updater.download_and_install(download_url, int(size))

    def cancel_update_download(self):
        """JS-callable: abort an in-progress download."""
        if self._updater:
            self._updater.cancel_download()

    def install_update(self):
        """JS-callable: quit so the waiting PowerShell script can swap the exe."""
        # Short delay so pywebview can return the call result before the window dies.
        threading.Timer(0.5, self.quit).start()

    def open_mixer(self):
        self._audio.open_mixer()

    def show_window(self):
        if self._window:
            self._window.show()
            self._visible = True

    def get_window_geometry(self):
        if self._window:
            return {'x': self._window.x, 'y': self._window.y,
                    'width': self._window.width, 'height': self._window.height}
        return {'x': 0, 'y': 0, 'width': 800, 'height': 600}

    def move_window(self, x, y):
        if self._window:
            self._window.move(int(x), int(y))

    def set_window_geometry(self, x, y, w, h):
        if self._window:
            self._window.move(int(x), int(y))
            self._window.resize(int(w), int(h))

    def hide_window(self):
        if self._window:
            self._window.hide()
            self._visible = False

    def quit(self):
        self._force_quit = True
        if self._peak_meter:
            self._peak_meter.stop()
        if self._save_timer:
            self._save_timer.cancel()
        self._slider_data.save(should_notify=False)
        self._slider_data.save_master(should_notify=False)
        if self._popup_window:
            try:
                self._popup_window.destroy()
            except Exception:
                pass
            self._popup_window = None
        if self._window:
            self._window.destroy()

    # ── SliderData compatibility (not intended for JS) ───────────────

    def add_slider(self, slider):
        self._sliders.append(slider)

    def show_notification(self, message):
        self._push('notification', {'message': message})

    @property
    def sliders(self):
        return list(self._sliders)

    @property
    def master_slider(self):
        class _Shim:
            def __init__(self, obj):
                self.slider_object = obj
        return _Shim(self._master_slider)

    # ── Popup window management ──────────────────────────────────────

    def open_dialog_window(self, edit_index=-1):
        """Open the Add/Edit Slider dialog in a dedicated popup window."""
        if self._popup_window is not None and self._popup_window in webview.windows:
            try:
                self._popup_window.focus()
            except Exception:
                pass
            return
        self._pending_edit_index = int(edit_index)
        title = 'Edit Slider' if int(edit_index) >= 0 else 'Add Slider'
        url   = os.path.join(self._ui_path, 'ui', 'web', 'dialog.html')
        self._popup_window = webview.create_window(
            title, url, js_api=self,
            width=420, height=500,
            x=screen_center_x(420), y=screen_center_y(500),
            resizable=False,
            background_color='#1a1a1a',
            frameless=True,
            on_top=True
        )

    def open_settings_window(self):
        """Open the Settings panel in a dedicated popup window."""
        if self._popup_window is not None and self._popup_window in webview.windows:
            try:
                self._popup_window.focus()
            except Exception:
                pass
            return
        url = os.path.join(self._ui_path, 'ui', 'web', 'settings.html')
        self._popup_window = webview.create_window(
            'Settings', url, js_api=self,
            width=420, height=560,
            x=screen_center_x(420), y=screen_center_y(560),
            resizable=False,
            background_color='#1a1a1a',
            frameless=True,
            on_top=True
        )

    def get_popup_context(self):
        """Called by a popup window on load to get its initial state."""
        ctx = {
            'editIndex':     self._pending_edit_index,
            'theme':         self._ui_settings.get('theme',  'dark'),
            'layout':        self._ui_settings.get('layout', 'vertical'),
            'version':       self._version,
            'pendingUpdate': self._pending_update,
            'advancedSettings': {
                'autoSaveInterval':  self.config['AUTO_SAVE_INTERVAL'],
                'smoothingWindow':   self.config['SMOOTHING_WINDOW'],
                'callbackInterval':  self.config['CALLBACK_INTERVAL'],
                'knobDetectionLow':  self.config['KNOB_DETECTION_LOW'],
                'knobDetectionHigh': self.config['KNOB_DETECTION_HIGH'],
            },
        }
        if 0 <= self._pending_edit_index < len(self._sliders):
            ctx['slider'] = self._sliders[self._pending_edit_index].serialize()
        return ctx

    def open_advanced_window(self):
        """Open the Advanced Settings panel, closing any existing popup first."""
        if self._popup_window is not None:
            win = self._popup_window
            self._popup_window = None
            try:
                win.destroy()
            except Exception:
                pass
        url = os.path.join(self._ui_path, 'ui', 'web', 'advanced.html')
        self._popup_window = webview.create_window(
            'Advanced Settings', url, js_api=self,
            width=460, height=580,
            x=screen_center_x(460), y=screen_center_y(580),
            resizable=False,
            background_color='#1a1a1a',
            frameless=True,
            on_top=True
        )

    def close_popup_window(self):
        """Called from popup JS to close itself cleanly."""
        if self._popup_window:
            win = self._popup_window
            self._popup_window = None
            try:
                win.destroy()
            except Exception:
                pass

    # ── Push events to JS ────────────────────────────────────────────

    def _push(self, event, data=None):
        if not self._window:
            return
        try:
            payload = json.dumps({'event': event, 'data': data or {}})
            self._window.evaluate_js(
                f'window.blaudio && window.blaudio._receive({payload})'
            )
        except Exception:
            pass

    def _push_popup(self, event, data=None):
        """Push an event to the popup window only (e.g. hardware detection results)."""
        if not self._popup_window:
            return
        try:
            payload = json.dumps({'event': event, 'data': data or {}})
            self._popup_window.evaluate_js(
                f'window.blaudio && window.blaudio._receive({payload})'
            )
        except Exception:
            pass

    # ── Persistence timer ────────────────────────────────────────────

    def _auto_save(self):
        self._slider_data.save(should_notify=False)
        self._slider_data.save_master(should_notify=False)
        self._schedule_save()

    def _schedule_save(self):
        interval = self.config.get('AUTO_SAVE_INTERVAL', 300)
        self._save_timer = threading.Timer(interval, self._auto_save)
        self._save_timer.daemon = True
        self._save_timer.start()

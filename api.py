import os
import sys
import json
import time
import threading
import subprocess
from comtypes import CLSCTX_ALL, CoInitialize, CoUninitialize
from pycaw.pycaw import AudioUtilities, ISimpleAudioVolume, IAudioEndpointVolume, IAudioMeterInformation
from slider_data import SliderData
from serial_reader import SerialReader
from slider import Slider

_com_local = threading.local()

def _ensure_com():
    """Initialise COM for the current thread (pywebview uses a thread pool)."""
    if not getattr(_com_local, 'ready', False):
        CoInitialize()
        _com_local.ready = True


class Api:
    """Public methods on this class are exposed to JavaScript via pywebview."""

    def __init__(self):
        if getattr(sys, 'frozen', False):
            self._app_path = os.path.dirname(sys.executable)
        else:
            self._app_path = os.path.dirname(os.path.abspath(__file__))

        with open(os.path.join(self._app_path, 'blaudio_config.json')) as f:
            self.config = json.load(f)

        self._window      = None
        self._visible     = True
        self._force_quit  = False
        self._version     = 'v0.0.7'

        self._sliders        = []
        self._master_slider  = None
        self._master_volume  = 50
        self._master_mute    = False

        self._slider_data = SliderData(self)

        loaded_master = self._slider_data.load_master()
        if loaded_master:
            self._master_slider  = loaded_master
            self._master_volume  = loaded_master.volume
            self._master_mute    = loaded_master.mute
        else:
            self._master_slider = Slider(
                'Master Volume', ['Blaudio: Master Volume'], 50,
                knob_index=self.config['MASTER_KNOB_INDEX'],
            )

        self._slider_data.load()

        self._last_button_values = {}
        self._save_timer = None
        self._schedule_save()
        self._peak_meter_active = False

        self._serial_reader = SerialReader(
            self.config['COM_PORT'],
            baudrate=self.config['BAUD_RATE'],
            callback=self._on_serial_update,
            message_callback=self._on_message,
        )

    def set_window(self, window):
        self._window = window
        self._start_peak_meter()

    # ── JS-callable API ──────────────────────────────────────────────

    def get_initial_state(self):
        return {
            'version':      self._version,
            'masterVolume': self._master_volume,
            'masterMute':   self._master_mute,
            'sliders':      [s.serialize() for s in self._sliders],
        }

    def set_master_volume(self, value):
        _ensure_com()
        value = int(value)
        self._master_volume = value
        self._master_slider.volume = value
        self._apply_master_volume(value)

    def toggle_master_mute(self):
        _ensure_com()
        self._master_mute = not self._master_mute
        self._master_slider.mute = self._master_mute
        self._apply_master_mute()
        self._slider_data.save_master(should_notify=False)
        return self._master_mute

    def get_running_apps(self):
        _ensure_com()
        sessions = AudioUtilities.GetAllSessions()
        apps = [s.Process.name() for s in sessions if s.Process]
        apps.append('All Unassigned')
        return apps

    def create_slider(self, name, app_names, knob_index):
        if not name:
            return None
        knob = None if int(knob_index) < 0 else int(knob_index)
        slider = Slider(name, list(app_names), 50, knob_index=knob)
        self.add_slider(slider)
        self._slider_data.save(should_notify=False)
        return slider.serialize()

    def edit_slider(self, index, name, app_names, knob_index):
        index = int(index)
        if not name or not (0 <= index < len(self._sliders)):
            return None
        knob = None if int(knob_index) < 0 else int(knob_index)
        slider = self._sliders[index]
        slider.name = name
        slider.app_names = list(app_names)
        slider.knob_index = knob
        self._slider_data.save(should_notify=False)
        return slider.serialize()

    def reorder_sliders(self, order):
        order = [int(i) for i in order]
        if sorted(order) != list(range(len(self._sliders))):
            return False  # invalid order — ignore
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
        _ensure_com()
        index, value = int(index), int(value)
        if 0 <= index < len(self._sliders):
            self._sliders[index].volume = value
            self._apply_volume(value, self._sliders[index])

    def toggle_slider_mute(self, index):
        _ensure_com()
        index = int(index)
        if 0 <= index < len(self._sliders):
            self._sliders[index].mute = not self._sliders[index].mute
            self._apply_mute(self._sliders[index])
            self._slider_data.save(should_notify=False)
            return self._sliders[index].mute
        return False

    def open_mixer(self):
        subprocess.Popen('SndVol.exe')

    def show_window(self):
        if self._window:
            self._window.show()
            self._visible = True

    def hide_window(self):
        if self._window:
            self._window.hide()
            self._visible = False

    def quit(self):
        self._force_quit = True
        self._stop_peak_meter()
        if self._save_timer:
            self._save_timer.cancel()
        self._slider_data.save(should_notify=False)
        self._slider_data.save_master(should_notify=False)
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

    # ── Audio ────────────────────────────────────────────────────────

    def _apply_master_volume(self, value):
        devices = AudioUtilities.GetSpeakers()
        iface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
        iface.QueryInterface(IAudioEndpointVolume).SetMasterVolumeLevelScalar(value / 100.0, None)

    def _apply_master_mute(self):
        devices = AudioUtilities.GetSpeakers()
        iface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
        iface.QueryInterface(IAudioEndpointVolume).SetMute(self._master_mute, None)

    def _apply_volume(self, value, slider_object):
        for session in AudioUtilities.GetAllSessions():
            if not session.Process:
                continue
            vol = session._ctl.QueryInterface(ISimpleAudioVolume)
            if 'All Unassigned' in slider_object.app_names:
                if not self._is_app_assigned(session.Process.name()):
                    vol.SetMasterVolume(value / 100.0, None)
            elif session.Process.name() in slider_object.app_names:
                vol.SetMasterVolume(value / 100.0, None)

    def _apply_mute(self, slider_object):
        for session in AudioUtilities.GetAllSessions():
            if not session.Process:
                continue
            vol = session._ctl.QueryInterface(ISimpleAudioVolume)
            if 'All Unassigned' in slider_object.app_names:
                if not self._is_app_assigned(session.Process.name()):
                    vol.SetMute(slider_object.mute, None)
            elif session.Process.name() in slider_object.app_names:
                vol.SetMute(slider_object.mute, None)

    def _is_app_assigned(self, app_name):
        return any(app_name in s.app_names for s in self._sliders)

    # ── Persistence timer ────────────────────────────────────────────

    def _auto_save(self):
        self._slider_data.save(should_notify=False)
        self._slider_data.save_master(should_notify=False)
        self._schedule_save()

    def _schedule_save(self):
        self._save_timer = threading.Timer(300, self._auto_save)
        self._save_timer.daemon = True
        self._save_timer.start()

    # ── Push updates to JS ───────────────────────────────────────────

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

    # ── Serial callbacks ─────────────────────────────────────────────

    def _on_serial_update(self, knobs, buttons):
        _ensure_com()
        for knob_index, knob_value in knobs.items():
            if self._master_slider.knob_index == knob_index:
                self._master_volume = knob_value
                self._master_slider.volume = knob_value
                self._apply_master_volume(knob_value)
                self._push('master_volume', {'volume': knob_value})
            else:
                for i, slider in enumerate(self._sliders):
                    if slider.knob_index == knob_index:
                        slider.volume = knob_value
                        self._apply_volume(knob_value, slider)
                        self._push('slider_volume', {'index': i, 'volume': knob_value})

        for button_index, button_value in buttons.items():
            if button_value == 0 and self._last_button_values.get(button_index, 1) == 1:
                if button_index == self.config['MUTE_BUTTON_INDEX']:
                    muted = self.toggle_master_mute()
                    self._push('master_mute', {'mute': muted})
                elif button_index == self.config['SHOW_HIDE_BUTTON_INDEX']:
                    if self._visible:
                        self.hide_window()
                    else:
                        self.show_window()
                self._push('notification', {'message': f'Button {button_index} pressed'})
            self._last_button_values[button_index] = button_value

    def _on_message(self, message):
        self._push('notification', {'message': message})

    # ── Peak meter ───────────────────────────────────────────────────

    def _start_peak_meter(self):
        self._peak_meter_active = True
        t = threading.Thread(target=self._peak_meter_loop, daemon=True)
        t.start()

    def _stop_peak_meter(self):
        self._peak_meter_active = False

    def _peak_meter_loop(self):
        CoInitialize()

        # Activate the endpoint meter once in this thread's COM context
        master_meter = None
        try:
            iface = AudioUtilities.GetSpeakers().Activate(
                IAudioMeterInformation._iid_, CLSCTX_ALL, None
            )
            master_meter = iface.QueryInterface(IAudioMeterInformation)
        except Exception:
            pass

        cached_sessions  = []
        last_refresh     = 0.0

        while self._peak_meter_active:
            now = time.monotonic()

            # Re-enumerate sessions every 2 s to pick up new/closed apps
            if now - last_refresh > 2.0:
                try:
                    cached_sessions = [
                        s for s in AudioUtilities.GetAllSessions() if s.Process
                    ]
                except Exception:
                    cached_sessions = []
                last_refresh = now

            try:
                self._push('peak_levels', self._read_peaks(cached_sessions, master_meter))
            except Exception:
                pass

            time.sleep(0.05)   # 20 fps — light enough not to stress the CPU

    def _read_peaks(self, sessions, master_meter):
        # Build app_name → peak map from cached sessions
        app_peaks = {}
        for session in sessions:
            try:
                meter = session._ctl.QueryInterface(IAudioMeterInformation)
                peak  = meter.GetPeakValue()
                name  = session.Process.name()
                if peak > app_peaks.get(name, 0.0):
                    app_peaks[name] = peak
            except Exception:
                pass

        # Master endpoint peak
        try:
            master_peak = master_meter.GetPeakValue() if master_meter else 0.0
        except Exception:
            master_peak = max(app_peaks.values(), default=0.0)

        if self._master_mute:
            master_peak = 0.0

        # Per-slider peaks (snapshot to avoid race with mutation)
        sliders  = list(self._sliders)
        assigned = {
            a for s in sliders
            for a in s.app_names
            if 'All Unassigned' not in s.app_names
        }

        slider_peaks = []
        for slider in sliders:
            if slider.mute:
                slider_peaks.append(0.0)
                continue
            if 'All Unassigned' in slider.app_names:
                peak = max(
                    (v for k, v in app_peaks.items() if k not in assigned),
                    default=0.0,
                )
            else:
                peak = max(
                    (app_peaks.get(a, 0.0) for a in slider.app_names),
                    default=0.0,
                )
            slider_peaks.append(round(peak, 4))

        return {
            'master':  round(master_peak, 4),
            'sliders': slider_peaks,
        }

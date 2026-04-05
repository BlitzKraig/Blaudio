import time
import threading
from comtypes import CLSCTX_ALL, CoInitialize
from pycaw.pycaw import AudioUtilities, IAudioMeterInformation


class PeakMeter:
    """
    Background thread that reads audio peak levels at ~20 fps and pushes
    them to the UI via a push callback.
    """

    # Re-enumerate audio sessions every 2 s to pick up new/closed apps.
    SESSION_REFRESH_INTERVAL = 2.0
    # Poll interval — 20 fps is smooth without stressing the CPU.
    # TODO: Make this configurable in settings. Also allow turning off meter.
    POLL_INTERVAL = 0.05

    def __init__(self, get_state_fn, push_fn):
        """
        Args:
            get_state_fn: callable() -> (sliders: list, master_mute: bool)
                          Called on every tick to get a consistent snapshot.
            push_fn:      callable(event: str, data: dict)
                          Sends a push event to the JavaScript UI.
        """
        self._get_state = get_state_fn
        self._push      = push_fn
        self._active    = False

    def start(self):
        self._active = True
        threading.Thread(target=self._loop, daemon=True).start()

    def stop(self):
        self._active = False

    # ── Internal ─────────────────────────────────────────────────────

    def _loop(self):
        CoInitialize()
        master_meter    = self._init_master_meter()
        cached_sessions = []
        last_refresh    = 0.0

        while self._active:
            now = time.monotonic()

            if now - last_refresh > self.SESSION_REFRESH_INTERVAL:
                try:
                    cached_sessions = [s for s in AudioUtilities.GetAllSessions() if s.Process]
                except Exception:
                    cached_sessions = []
                last_refresh = now

            try:
                sliders, master_mute = self._get_state()
                self._push('peak_levels', self._read_peaks(
                    cached_sessions, master_meter, sliders, master_mute
                ))
            except Exception:
                pass

            time.sleep(self.POLL_INTERVAL)

    @staticmethod
    def _init_master_meter():
        """Activate the endpoint peak meter for this thread's COM context."""
        try:
            iface = AudioUtilities.GetSpeakers().Activate(
                IAudioMeterInformation._iid_, CLSCTX_ALL, None
            )
            return iface.QueryInterface(IAudioMeterInformation)
        except Exception:
            return None

    def _read_peaks(self, sessions, master_meter, sliders, master_mute):
        app_peaks   = self._collect_app_peaks(sessions)
        master_peak = self._master_peak(master_meter, app_peaks, master_mute)

        # Collect app names that are explicitly assigned to a slider (not "All Unassigned")
        assigned = {
            app
            for slider in sliders
            for app in slider.app_names
            if 'All Unassigned' not in slider.app_names
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

        return {'master': round(master_peak, 4), 'sliders': slider_peaks}

    @staticmethod
    def _collect_app_peaks(sessions):
        """Return a dict of {process_name: peak_value} across all sessions."""
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
        return app_peaks

    @staticmethod
    def _master_peak(master_meter, app_peaks, master_mute):
        if master_mute:
            return 0.0
        try:
            return master_meter.GetPeakValue() if master_meter else max(app_peaks.values(), default=0.0)
        except Exception:
            return max(app_peaks.values(), default=0.0)

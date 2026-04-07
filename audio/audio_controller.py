import subprocess
import threading
import traceback
from comtypes import CLSCTX_ALL, CoInitialize
from pycaw.pycaw import AudioUtilities, ISimpleAudioVolume, IAudioEndpointVolume

_com_local = threading.local()

# HRESULT returned when CoInitialize is called on a thread that already has
# COM initialised with a different apartment model (e.g. Edge WebView2 uses
# COINIT_MULTITHREADED).  This is not an error - we can still use COM objects.
_RPC_E_CHANGED_MODE = -2147417850  # 0x80010106 as a signed 32-bit int


def ensure_com():
    """Initialise COM for the current thread (pywebview uses a thread pool)."""
    if not getattr(_com_local, 'ready', False):
        try:
            CoInitialize()
        except OSError as e:
            if getattr(e, 'winerror', None) != _RPC_E_CHANGED_MODE:
                print(f'[audio] CoInitialize failed: {e!r}')
            # Either RPC_E_CHANGED_MODE (COM already initialised by WebView2 - fine)
            # or another transient error.  Mark as ready and proceed; pycaw works
            # in both STA and MTA contexts for the interfaces we use.
        _com_local.ready = True


class AudioController:
    """Wraps pycaw to control Windows audio sessions and the master endpoint."""

    def apply_master_volume(self, value):
        """Set the system master output volume (0-100)."""
        try:
            devices = AudioUtilities.GetSpeakers()
            iface   = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
            iface.QueryInterface(IAudioEndpointVolume).SetMasterVolumeLevelScalar(value / 100.0, None)
        except Exception:
            print('[audio] apply_master_volume failed:')
            traceback.print_exc()
            raise

    def apply_master_mute(self, muted):
        """Mute or unmute the system master output."""
        try:
            devices = AudioUtilities.GetSpeakers()
            iface   = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
            iface.QueryInterface(IAudioEndpointVolume).SetMute(muted, None)
        except Exception:
            print('[audio] apply_master_mute failed:')
            traceback.print_exc()
            raise

    def apply_slider_volume(self, value, slider, all_sliders):
        """Set per-application volume for every app assigned to *slider*."""
        try:
            for session in AudioUtilities.GetAllSessions():
                if not session.Process:
                    continue
                vol = session._ctl.QueryInterface(ISimpleAudioVolume)
                if 'All Unassigned' in slider.app_names:
                    if not self.is_app_assigned(session.Process.name(), all_sliders):
                        vol.SetMasterVolume(value / 100.0, None)
                elif session.Process.name() in slider.app_names:
                    vol.SetMasterVolume(value / 100.0, None)
        except Exception:
            print('[audio] apply_slider_volume failed:')
            traceback.print_exc()
            raise

    def apply_slider_mute(self, slider, all_sliders):
        """Mute or unmute every app assigned to *slider*."""
        try:
            for session in AudioUtilities.GetAllSessions():
                if not session.Process:
                    continue
                vol = session._ctl.QueryInterface(ISimpleAudioVolume)
                if 'All Unassigned' in slider.app_names:
                    if not self.is_app_assigned(session.Process.name(), all_sliders):
                        vol.SetMute(slider.mute, None)
                elif session.Process.name() in slider.app_names:
                    vol.SetMute(slider.mute, None)
        except Exception:
            print('[audio] apply_slider_mute failed:')
            traceback.print_exc()
            raise

    def get_running_apps(self):
        """Return a list of process names that currently have audio sessions."""
        try:
            sessions = AudioUtilities.GetAllSessions()
            apps = [s.Process.name() for s in sessions if s.Process]
            apps.append('All Unassigned')
            return apps
        except Exception:
            print('[audio] get_running_apps failed:')
            traceback.print_exc()
            return ['All Unassigned']

    @staticmethod
    def is_app_assigned(app_name, all_sliders):
        """Return True if *app_name* is explicitly assigned to any slider."""
        return any(app_name in s.app_names for s in all_sliders)

    @staticmethod
    def open_mixer():
        """Open the Windows sound mixer."""
        subprocess.Popen('SndVol.exe')

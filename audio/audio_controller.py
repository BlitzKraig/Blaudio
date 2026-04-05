import subprocess
import threading
from comtypes import CLSCTX_ALL, CoInitialize
from pycaw.pycaw import AudioUtilities, ISimpleAudioVolume, IAudioEndpointVolume

_com_local = threading.local()


def ensure_com():
    """Initialise COM for the current thread (pywebview uses a thread pool)."""
    if not getattr(_com_local, 'ready', False):
        CoInitialize()
        _com_local.ready = True


class AudioController:
    """Wraps pycaw to control Windows audio sessions and the master endpoint."""

    def apply_master_volume(self, value):
        """Set the system master output volume (0-100)."""
        devices = AudioUtilities.GetSpeakers()
        iface   = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
        iface.QueryInterface(IAudioEndpointVolume).SetMasterVolumeLevelScalar(value / 100.0, None)

    def apply_master_mute(self, muted):
        """Mute or unmute the system master output."""
        devices = AudioUtilities.GetSpeakers()
        iface   = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
        iface.QueryInterface(IAudioEndpointVolume).SetMute(muted, None)

    def apply_slider_volume(self, value, slider, all_sliders):
        """Set per-application volume for every app assigned to *slider*."""
        for session in AudioUtilities.GetAllSessions():
            if not session.Process:
                continue
            vol = session._ctl.QueryInterface(ISimpleAudioVolume)
            if 'All Unassigned' in slider.app_names:
                if not self.is_app_assigned(session.Process.name(), all_sliders):
                    vol.SetMasterVolume(value / 100.0, None)
            elif session.Process.name() in slider.app_names:
                vol.SetMasterVolume(value / 100.0, None)

    def apply_slider_mute(self, slider, all_sliders):
        """Mute or unmute every app assigned to *slider*."""
        for session in AudioUtilities.GetAllSessions():
            if not session.Process:
                continue
            vol = session._ctl.QueryInterface(ISimpleAudioVolume)
            if 'All Unassigned' in slider.app_names:
                if not self.is_app_assigned(session.Process.name(), all_sliders):
                    vol.SetMute(slider.mute, None)
            elif session.Process.name() in slider.app_names:
                vol.SetMute(slider.mute, None)

    def get_running_apps(self):
        """Return a list of process names that currently have audio sessions."""
        sessions = AudioUtilities.GetAllSessions()
        apps = [s.Process.name() for s in sessions if s.Process]
        apps.append('All Unassigned')
        return apps

    @staticmethod
    def is_app_assigned(app_name, all_sliders):
        """Return True if *app_name* is explicitly assigned to any slider."""
        return any(app_name in s.app_names for s in all_sliders)

    @staticmethod
    def open_mixer():
        """Open the Windows sound mixer."""
        subprocess.Popen('SndVol.exe')

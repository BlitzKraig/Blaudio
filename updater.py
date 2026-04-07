"""
Auto-updater for Blaudio.

Checks GitHub Releases for a newer version, downloads it, and performs the
exe-swap via a detached PowerShell script (required because Windows will not
allow overwriting a running .exe in place).

Only active when running as a frozen PyInstaller executable.
"""

import json
import os
import subprocess
import sys
import tempfile
import threading
import urllib.error
import urllib.request

GITHUB_REPO = 'BlitzKraig/Blaudio'
ASSET_NAME  = 'blaudio.exe'
GITHUB_API  = f'https://api.github.com/repos/{GITHUB_REPO}/releases/latest'
REQUEST_TIMEOUT = 10   # seconds


def _parse_version(tag: str) -> tuple:
    """Parse 'vX.Y.Z' or 'X.Y.Z' to a comparable tuple of ints."""
    tag = tag.lstrip('v')
    parts = tag.split('.')
    try:
        return (int(parts[0]), int(parts[1]), int(parts[2]))
    except (IndexError, ValueError):
        return (0, 0, 0)


def _is_newer(remote_tag: str, current_tag: str) -> bool:
    return _parse_version(remote_tag) > _parse_version(current_tag)


class Updater:
    """
    Handles all update lifecycle:
      check_async()            - background version check
      download_and_install()   - background download + exe-swap script
      cancel_download()        - abort in-progress download
    """

    def __init__(self, current_version: str, app_exe_path: str, on_event):
        """
        current_version : e.g. 'v0.1.2'
        app_exe_path    : absolute path to the running .exe (sys.executable when frozen)
        on_event        : callable(event: str, data: dict) - relays events to JS
        """
        self._current_version  = current_version
        self._app_exe_path     = app_exe_path
        self._on_event         = on_event
        self._download_thread  = None
        self._cancel_download  = False

    # ── Public API ────────────────────────────────────────────────────────────

    def check_async(self):
        """Spawn a daemon thread to check for updates. Returns immediately."""
        t = threading.Thread(target=self._check_worker, daemon=True)
        t.start()

    def download_and_install(self, download_url: str, size: int):
        """Begin downloading the update in a background thread. No-ops if already running."""
        if self._download_thread and self._download_thread.is_alive():
            return
        self._cancel_download = False
        self._download_thread = threading.Thread(
            target=self._download_worker,
            args=(download_url, int(size)),
            daemon=True,
        )
        self._download_thread.start()

    def cancel_download(self):
        """Signal the download loop to stop on the next chunk boundary."""
        self._cancel_download = True

    # ── Workers ───────────────────────────────────────────────────────────────

    def _check_worker(self):
        try:
            req = urllib.request.Request(
                GITHUB_API,
                headers={
                    'Accept':     'application/vnd.github+json',
                    'User-Agent': 'Blaudio-Updater',
                },
            )
            with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT) as resp:
                data = json.loads(resp.read().decode())

            tag    = data.get('tag_name', '')
            body   = data.get('body', '')
            assets = data.get('assets', [])
            asset  = next((a for a in assets if a['name'] == ASSET_NAME), None)

            if not asset:
                return   # release exists but no matching exe asset

            if _is_newer(tag, self._current_version):
                self._on_event('update_available', {
                    'version':      tag,
                    'notes':        body,
                    'download_url': asset['browser_download_url'],
                    'size':         asset['size'],
                })
            # else: already up to date - silent

        except urllib.error.URLError:
            self._on_event('update_error', {'reason': 'network'})
        except Exception:
            pass   # swallow all other errors silently at startup

    def _download_worker(self, url: str, total_size: int):
        tmp_path = os.path.join(
            tempfile.gettempdir(),
            f'blaudio_update_{os.getpid()}.exe',
        )

        try:
            req = urllib.request.Request(
                url,
                headers={'User-Agent': 'Blaudio-Updater'},
            )
            with urllib.request.urlopen(req, timeout=60) as resp, \
                 open(tmp_path, 'wb') as out:

                downloaded = 0
                chunk_size = 65536   # 64 KB
                last_pct   = -1

                while True:
                    if self._cancel_download:
                        return

                    chunk = resp.read(chunk_size)
                    if not chunk:
                        break

                    out.write(chunk)
                    downloaded += len(chunk)

                    if total_size > 0:
                        pct = int(downloaded * 100 / total_size)
                        if pct != last_pct:
                            last_pct = pct
                            self._on_event('update_progress', {
                                'percent':    pct,
                                'downloaded': downloaded,
                                'total':      total_size,
                            })

            if self._cancel_download:
                return

            # All bytes written - stage the replacement script and signal JS.
            # JS will call install_update() which quits the process; the script
            # waits for that, then moves the new exe over the old one and relaunches.
            self._on_event('update_progress', {
                'percent': 100, 'downloaded': downloaded, 'total': total_size,
            })
            self._launch_replace_script(tmp_path)
            self._on_event('update_complete', {})

        except urllib.error.URLError:
            self._on_event('update_error', {'reason': 'download_network'})
        except OSError:
            self._on_event('update_error', {'reason': 'disk'})
        except Exception:
            self._on_event('update_error', {'reason': 'unknown'})

    def _launch_replace_script(self, tmp_path: str):
        """
        Write and launch a detached PowerShell script that:
          1. Polls until the current process (by PID) has exited.
          2. Moves the downloaded exe over the installed exe (retries for AV locks).
          3. Relaunches the updated exe.

        PowerShell is used instead of a batch file for reliable path handling
        (spaces, non-ASCII) and the retry loop.
        """
        current_pid  = os.getpid()
        target_path  = self._app_exe_path
        # Use single-quoted PS strings - safe for paths with spaces.
        script = f"""\
$pidToWait = {current_pid}
$source    = '{tmp_path}'
$target    = '{target_path}'

# Wait for the old process to exit (max 30 s)
for ($i = 0; $i -lt 60; $i++) {{
    Start-Sleep -Milliseconds 500
    if (-not (Get-Process -Id $pidToWait -ErrorAction SilentlyContinue)) {{ break }}
}}

# Move new exe over old (retry in case AV scanner holds a brief lock)
for ($attempt = 0; $attempt -lt 10; $attempt++) {{
    try {{
        Move-Item -Path $source -Destination $target -Force -ErrorAction Stop
        break
    }} catch {{
        Start-Sleep -Milliseconds 500
    }}
}}

Start-Process -FilePath $target
"""
        script_fd, script_path = tempfile.mkstemp(
            suffix='.ps1', prefix='blaudio_upd_',
        )
        try:
            with os.fdopen(script_fd, 'w') as f:
                f.write(script)
        except Exception:
            try:
                os.close(script_fd)
            except Exception:
                pass
            raise

        CREATE_NO_WINDOW = 0x08000000
        subprocess.Popen(
            [
                'powershell.exe',
                '-NoProfile',
                '-ExecutionPolicy', 'Bypass',
                '-NonInteractive',
                '-WindowStyle', 'Hidden',
                '-File', script_path,
            ],
            creationflags=CREATE_NO_WINDOW,
            close_fds=True,
        )

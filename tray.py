import os
import sys
import pystray
from PIL import Image


class Tray:
    def __init__(self, api):
        self._api            = api
        self._update_version = None

        if getattr(sys, 'frozen', False):
            base_path = sys._MEIPASS
        else:
            base_path = os.path.dirname(__file__)

        image = Image.open(os.path.join(base_path, 'resources', 'storm.ico'))

        # Menu is rebuilt each time it opens so the update item appears dynamically.
        self._icon = pystray.Icon(
            'Blaudio',
            image,
            'Blaudio Volume Controller',
            menu=pystray.Menu(self._build_menu),
        )

    def start(self):
        self._icon.run_detached()

    def stop(self):
        self._icon.stop()

    def notify_update(self, version):
        """Show a balloon notification and add a persistent tray menu item."""
        self._update_version = version
        try:
            self._icon.notify(
                f'Version {version} is available - open Settings to download.',
                'Blaudio Update',
            )
        except Exception:
            pass   # notify() is best-effort; not all platforms support it

    def _build_menu(self):
        items = [pystray.MenuItem('Show', self._on_show, default=True)]
        if self._update_version:
            items.append(pystray.MenuItem(
                f'Update available: {self._update_version}',
                self._on_update,
            ))
        items.append(pystray.MenuItem('Quit', self._on_quit))
        return items

    def _on_show(self):
        self._api.show_window()

    def _on_update(self):
        """Bring the window up and open Settings so the user can download."""
        self._api.show_window()
        self._api.open_settings_window()

    def _on_quit(self):
        self._icon.stop()
        self._api.quit()

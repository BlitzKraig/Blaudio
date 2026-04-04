import os
import sys
import pystray
from PIL import Image


class Tray:
    def __init__(self, api):
        self._api = api

        if getattr(sys, 'frozen', False):
            base_path = sys._MEIPASS
        else:
            base_path = os.path.dirname(__file__)

        image = Image.open(os.path.join(base_path, 'resources', 'storm.ico'))

        self._icon = pystray.Icon(
            'Blaudio',
            image,
            'Blaudio Volume Controller',
            menu=pystray.Menu(
                pystray.MenuItem('Show', self._on_show, default=True),
                pystray.MenuItem('Quit', self._on_quit),
            ),
        )

    def start(self):
        self._icon.run_detached()

    def stop(self):
        self._icon.stop()

    def _on_show(self):
        self._api.show_window()

    def _on_quit(self):
        self._icon.stop()
        self._api.quit()

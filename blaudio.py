import sys
import os
import webview
from api import Api
from tray import Tray


if __name__ == '__main__':
    if getattr(sys, 'frozen', False):
        base_path    = sys._MEIPASS
        start_hidden = True
    else:
        base_path    = os.path.dirname(__file__)
        start_hidden = False

    api = Api()

    window = webview.create_window(
        'Blaudio',
        os.path.join(base_path, 'ui', 'web', 'index.html'),
        js_api=api,
        width=1400,
        height=800,
        min_size=(300, 300),
        background_color='#1a1a1a',
    )

    api.set_window(window)

    def on_closing():
        if api._force_quit:
            return True
        api.hide_window()
        return False

    window.events.closing += on_closing

    tray = Tray(api)

    def on_shown():
        tray.start()
        if start_hidden:
            api.hide_window()

    webview.start(func=on_shown, debug=not getattr(sys, 'frozen', False))

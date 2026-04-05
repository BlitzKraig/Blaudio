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

    if start_hidden:
        # Hide only after the page has fully loaded so WebView2 finishes
        # initialising its JS bridge.  Hiding during on_shown (before load)
        # permanently breaks evaluate_js — even after the window is shown again.
        window.events.loaded += lambda: api.hide_window()

    def on_shown():
        tray.start()

    webview.start(func=on_shown, debug=not getattr(sys, 'frozen', False))

    # webview.start() returns once the window has been destroyed (i.e. the user
    # quit).  The pystray icon runs on a non-daemon thread, so we must stop it
    # explicitly — otherwise the process hangs even though the window is gone.
    tray.stop()

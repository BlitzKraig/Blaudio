import sys
import os
import json
import webview
from api import Api
from tray import Tray
import single_instance


if __name__ == '__main__':
    # ── Single-instance enforcement ───────────────────────────────────────
    # Try to acquire the lock socket.  If another instance already holds it,
    # signal that instance to show its window and exit immediately.
    _instance_lock = single_instance.try_acquire()
    if _instance_lock is None:
        single_instance.signal_existing()
        sys.exit(0)

    if getattr(sys, 'frozen', False):
        base_path    = sys._MEIPASS
        start_hidden = True
    else:
        base_path    = os.path.dirname(__file__)
        start_hidden = False

    api = Api()

    try:
        with open(os.path.join(base_path, 'ui_settings.json')) as f:
            ui_settings = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        ui_settings = {}

    layout = ui_settings.get('layout', 'vertical')
    prefix = f'{layout}_window_'

    window = webview.create_window(
        'Blaudio',
        os.path.join(base_path, 'ui', 'web', 'index.html'),
        js_api=api,
        width=ui_settings.get(f'{prefix}width', 800),
        height=ui_settings.get(f'{prefix}height', 600),
        x=ui_settings.get(f'{prefix}x'),
        y=ui_settings.get(f'{prefix}y'),
        min_size=(300, 300),
        background_color='#1a1a1a',
        frameless=True,
        on_top=True,
        easy_drag=False,
    )

    api.set_window(window)

    # Start listening for "show" signals from any future second-instance launch.
    single_instance.start_listener(_instance_lock, api.show_window)

    def on_closing():
        if api._force_quit:
            return True
        current_layout = api._ui_settings.get('layout', 'vertical')
        prefix = f'{current_layout}_window_'
        api._ui_settings[f'{prefix}x'] = window.x
        api._ui_settings[f'{prefix}y'] = window.y
        api._ui_settings[f'{prefix}width'] = window.width
        api._ui_settings[f'{prefix}height'] = window.height
        try:
            with open(os.path.join(base_path, 'ui_settings.json'), 'w') as f:
                json.dump(api._ui_settings, f, indent=2)
        except Exception:
            pass
        api.hide_window()
        return False

    window.events.closing += on_closing

    tray = Tray(api)
    api.set_tray(tray)

    if start_hidden:
        # Hide only after the page has fully loaded so WebView2 finishes
        # initialising its JS bridge.  Hiding during on_shown (before load)
        # permanently breaks evaluate_js - even after the window is shown again.
        window.events.loaded += lambda: api.hide_window()

    def on_shown():
        tray.start()

    webview.start(func=on_shown, debug=not getattr(sys, 'frozen', False))

    # webview.start() returns once the window has been destroyed (i.e. the user
    # quit).  The pystray icon runs on a non-daemon thread, so we must stop it
    # explicitly - otherwise the process hangs even though the window is gone.
    tray.stop()

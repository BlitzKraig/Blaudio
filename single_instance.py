"""
Single-instance enforcement via a localhost TCP socket.

Usage (in blaudio.py):
    import single_instance

    _lock = single_instance.try_acquire()
    if _lock is None:
        single_instance.signal_existing()
        sys.exit(0)

    # ... create api, window ...

    single_instance.start_listener(_lock, api.show_window)
"""

import socket
import threading

_HOST = '127.0.0.1'
_PORT = 25346   # BLDIO fixed port; unlikely to clash with other apps


def try_acquire() -> socket.socket | None:
    """
    Attempt to bind the single-instance socket.

    Returns the bound, listening socket if this is the first instance,
    or None if another instance already holds the port.
    """
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 0)
    try:
        sock.bind((_HOST, _PORT))
        sock.listen(5)
        return sock
    except OSError:
        sock.close()
        return None


def signal_existing() -> None:
    """
    Connect to the running instance and send a 'show' command.
    Silently does nothing if the connection fails.
    """
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(2)
        s.connect((_HOST, _PORT))
        s.sendall(b'show')
        s.close()
    except OSError:
        pass


def start_listener(sock: socket.socket, on_show) -> None:
    """
    Start a daemon thread that accepts connections on *sock* and calls
    *on_show()* whenever a 'show' command is received.

    The caller must keep a reference to *sock* for the lifetime of the
    process (to prevent it being garbage-collected and the port released).
    """
    def _listen():
        while True:
            try:
                conn, _ = sock.accept()
                with conn:
                    data = conn.recv(16)
                    if data.strip() == b'show':
                        on_show()
            except OSError:
                break

    t = threading.Thread(target=_listen, daemon=True, name='instance-listener')
    t.start()

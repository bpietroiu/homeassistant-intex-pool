import sys

import pytest


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    yield


if sys.platform == "win32":
    # On Windows, asyncio event loops use socketpair() internally (AF_INET); pytest-socket
    # blocks those at creation even though the HA harness intends to allow 127.0.0.1.
    # Fix: route socketpair() through the real socket class.
    import socket as _socket_module

    _true_socket = _socket_module.socket
    _orig_socketpair = getattr(_socket_module, "_real_socketpair", _socket_module.socketpair)
    _socket_module._real_socketpair = _orig_socketpair

    def _unblocked_socketpair(family=None, type=None, proto=None):
        import socket as _s
        _guarded = _s.socket
        _s.socket = _true_socket
        try:
            if family is not None:
                return _orig_socketpair(family, type, proto)
            return _orig_socketpair()
        finally:
            _s.socket = _guarded

    _socket_module.socketpair = _unblocked_socketpair

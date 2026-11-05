import ctypes as C
import sys
import threading

import pytest

pytestmark = pytest.mark.skipif(sys.platform != "win32", reason="Windows only")


def test_input_structure_size():
    from uncanny_clicker.mouse_controller import INPUT
    assert C.sizeof(INPUT) == (40 if C.sizeof(C.c_void_p) == 8 else 28)


def test_display_change_prevents_input(monkeypatch):
    from uncanny_clicker import mouse_controller as m
    monkeypatch.setattr(m, "monitors", lambda: ((0, 0, 100, 100),))
    mouse = m.WindowsMouse()
    mouse.prepare(10, 10)
    monkeypatch.setattr(m, "monitors", lambda: ((0, 0, 200, 100),))
    with pytest.raises(RuntimeError, match="構成"):
        mouse.click(10, 10, threading.Event())


def test_partial_send_releases_button(monkeypatch):
    from uncanny_clicker import mouse_controller as m
    monkeypatch.setattr(m, "monitors", lambda: ((0, 0, 100, 100),))
    monkeypatch.setattr(m, "position", lambda: (10, 10))
    monkeypatch.setattr(m.user32, "SetCursorPos", lambda x, y: True)
    sends = []
    def send(count, inputs, size):
        sends.append(count)
        return 1
    monkeypatch.setattr(m.user32, "SendInput", send)
    mouse = m.WindowsMouse()
    with pytest.raises(RuntimeError, match="送信"):
        mouse.click(10, 10, threading.Event())
    assert sends == [2, 1]


def test_corner_prevents_cursor_warp(monkeypatch):
    from uncanny_clicker import mouse_controller as m
    monkeypatch.setattr(m, "monitors", lambda: ((0, 0, 100, 100),))
    monkeypatch.setattr(m, "position", lambda: (0, 0))
    def forbidden(*args):
        pytest.fail("Must not inject any input")
    monkeypatch.setattr(m.user32, "SetCursorPos", forbidden)
    mouse = m.WindowsMouse()
    with pytest.raises(RuntimeError, match="安全停止"):
        mouse.click(10, 10, threading.Event())

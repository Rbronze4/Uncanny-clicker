import json
import sys
import threading
from types import SimpleNamespace

import pytest

from uncanny_clicker.config import Settings, load, save
from uncanny_clicker.keybindings import DEFAULT_KEYS, parse_binding, validate_bindings


@pytest.mark.parametrize("text, expected, modifiers, vk", [
    (" ctrl + SHIFT + a ", "Ctrl+Shift+A", 6, 65),
    ("F8", "F8", 0, 0x77), ("alt+Num3", "Alt+Num3", 1, 0x63),
    ("Win+PageDown", "Win+PageDown", 8, 0x22), ("Esc", "Esc", 0, 27),
])
def test_parse(text, expected, modifiers, vk):
    result = parse_binding(text)
    assert (result.text, result.modifiers, result.vk) == (expected, modifiers, vk)


@pytest.mark.parametrize("text", ["", "F12", "Ctrl", "Ctrl++A", "Ctrl+Ctrl+A", "A+B", "Alt+F4", "Win+L", "Ctrl+Alt+Delete", None])
def test_invalid(text):
    with pytest.raises(ValueError):
        parse_binding(text)


def test_duplicates_are_case_and_order_independent():
    with pytest.raises(ValueError, match="異なる"):
        validate_bindings({**DEFAULT_KEYS, "stop_key": "ctrl+shift+a", "start_key": "Shift+Ctrl+A"})


def test_old_config_migrates(tmp_path):
    path = tmp_path / "config.json"
    path.write_text(json.dumps({"x": -500, "cps": 25}), encoding="utf-8")
    settings, warning = load(path)
    assert not warning
    assert settings.x == -500 and settings.cps == 25
    assert settings.stop_key == "F8"


def test_custom_bindings_roundtrip(tmp_path):
    path = tmp_path / "config.json"
    settings = Settings(stop_key="Ctrl+Shift+S", start_key="Ctrl+Shift+A")
    save(path, settings)
    assert load(path) == (settings, "")


@pytest.mark.skipif(sys.platform != "win32", reason="Windows service")
@pytest.mark.parametrize("failed_id", [None, 8, 9, 27])
def test_service_registers_custom_keys_and_cleans_up(monkeypatch, failed_id):
    from uncanny_clicker import hotkeys as h
    registered, removed = [], []
    def register(hwnd, ident, modifiers, vk):
        registered.append((ident, modifiers, vk))
        return ident != failed_id
    monkeypatch.setattr(h.user32, "RegisterHotKey", register)
    monkeypatch.setattr(h.user32, "UnregisterHotKey", lambda hwnd, ident: removed.append(ident) or 1)
    monkeypatch.setattr(h.user32, "SetWindowsHookExW", lambda *args: 123)
    monkeypatch.setattr(h.user32, "UnhookWindowsHookEx", lambda *args: 1)
    monkeypatch.setattr(h.user32, "PeekMessageW", lambda *args: 0)
    clicker = SimpleNamespace(stop=lambda reason: None, active=False, mouse=SimpleNamespace(screens=()))
    service = h.SafetyService(clicker, {**DEFAULT_KEYS, "stop_key": "Ctrl+Shift+S", "cancel_key": "Alt+Q"})
    try:
        assert service.ready.wait(1)
        assert service.configured == (failed_id is None)
        assert service.safe == (failed_id != 8)
        assert (8, 0x4006, ord("S")) in registered
        assert (27, 0x4001, ord("Q")) in registered
    finally:
        service.close()
    assert set(removed) == {ident for ident, _, _ in registered if ident != failed_id}
    assert not service.thread.is_alive()

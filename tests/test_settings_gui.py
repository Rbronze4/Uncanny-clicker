"""Tk integration tests with all native input and key registration replaced."""
import queue
import os
import sys
import threading

import pytest

pytestmark = pytest.mark.skipif(
    sys.platform != "win32" or os.environ.get("UNCANNY_GUI_TESTS") != "1",
    reason="Requires an interactive Windows desktop; set UNCANNY_GUI_TESTS=1",
)


class FakeSafety:
    def __init__(self, clicker, bindings):
        self.events = queue.SimpleQueue()
        self.capture = threading.Event()
        self.suspended = threading.Event()
        self.ready = threading.Event()
        self.ready.set()
        self.safe = self.configured = bindings["start_key"] != "Ctrl+Q"
        self.registered = {6, 8, 9}
        self.last_stop = 0
        self.closed = False
        if not self.configured:
            self.events.put(("warning", "テスト用：キーの競合"))

    def close(self):
        self.closed = True


@pytest.fixture
def app(monkeypatch, tmp_path):
    from uncanny_clicker import gui
    monkeypatch.setattr(gui, "SafetyService", FakeSafety)
    monkeypatch.setattr(gui, "WindowsMouse", lambda: object())
    monkeypatch.setattr(gui, "config_path", lambda: tmp_path / "config.json")
    root = gui.App()
    root.withdraw()
    yield root
    root.safety.close()
    root.destroy()


def test_apply_updates_labels_and_persists(app):
    from uncanny_clicker.config import load
    from uncanny_clicker.gui import config_path
    app.open_settings()
    dialog = app.settings_window
    dialog.withdraw()
    dialog.variables["start_key"].set("Ctrl+Shift+A")
    dialog.variables["cancel_key"].set("Alt+Q")
    values = {name: variable.get() for name, variable in dialog.variables.items()}
    dialog.apply()
    app.finish_apply_keys(values)
    assert app.settings_window is None
    assert app.settings.start_key == "Ctrl+Shift+A"
    assert "Ctrl+Shift+A" in app.start_button.cget("text")
    assert "Alt+Q" in app.key_help.cget("text")
    assert load(config_path())[0].start_key == "Ctrl+Shift+A"


def test_registration_failure_restores_previous_keys(app):
    app.open_settings()
    app.settings_window.withdraw()
    values = {**app.key_values(), "start_key": "Ctrl+Q"}
    app.apply_keys(values)
    app.finish_apply_keys(values)
    assert app.settings.start_key == "F9"
    assert app.safety.safe
    assert "競合" in app.settings_window.error.cget("text")
    assert not app.settings_window.applying


def test_save_failure_rolls_back(app, monkeypatch):
    from uncanny_clicker import gui
    def denied(*args):
        raise OSError("test permission denied")
    monkeypatch.setattr(gui, "save", denied)
    app.open_settings()
    app.settings_window.withdraw()
    values = {**app.key_values(), "stop_key": "Ctrl+S"}
    app.apply_keys(values)
    app.finish_apply_keys(values)
    assert app.settings.stop_key == "F8"
    assert "保存できません" in app.settings_window.error.cget("text")


def test_settings_dialog_blocks_start_and_cancel_discards_edits(app):
    app.open_settings()
    app.settings_window.withdraw()
    app.settings_window.variables["stop_key"].set("Ctrl+S")
    app.start()
    assert not app.clicker.active
    app.dismiss_settings()
    assert app.settings.stop_key == "F8"
    assert not app.safety.suspended.is_set()

import json

import pytest

from uncanny_clicker.config import Settings, load, save


def test_round_trip(tmp_path):
    path = tmp_path / "nested/config.json"
    settings = Settings(-500, -200, 50, 1_000_000, True)
    save(path, settings)
    assert load(path) == (settings, "")
    assert list(path.parent.iterdir()) == [path]


def test_missing(tmp_path):
    assert load(tmp_path / "missing") == (Settings(), "")


@pytest.mark.parametrize("text", ["{", "[]", "null", '{"cps": 0}', '{"count": true}', '{"x":"20"}', '{"unlimited":1}', '{"unknown":2}'])
def test_corrupt(tmp_path, text):
    path = tmp_path / "config.json"
    path.write_text(text, encoding="utf-8")
    settings, warning = load(path)
    assert settings == Settings()
    assert warning


def test_failed_replace_preserves_old_file(tmp_path, monkeypatch):
    path = tmp_path / "config.json"
    save(path, Settings())
    def fail(*args):
        raise OSError("locked")
    monkeypatch.setattr("uncanny_clicker.config.os.replace", fail)
    with pytest.raises(OSError):
        save(path, Settings(cps=25))
    assert json.loads(path.read_text())["cps"] == 16
    assert list(tmp_path.iterdir()) == [path]

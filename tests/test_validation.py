import sys

import pytest

from uncanny_clicker.config import Settings, integer


@pytest.mark.parametrize("value", [0, -1, 1_000_001, "abc", "1.1", True, 1.5, None, ""])
def test_invalid_count(value):
    with pytest.raises(ValueError):
        integer(value, "クリック回数", 1, 1_000_000)


@pytest.mark.parametrize("value", [1, 100, 1_000_000, "100"])
def test_valid_count(value):
    assert integer(value, "回数", 1, 1_000_000) == int(value)


@pytest.mark.parametrize("value", [0, 51, -1, 1.5, True, "16"])
def test_invalid_cps(value):
    with pytest.raises(ValueError):
        Settings(cps=value).validate()


@pytest.mark.parametrize("value", [1, 16, 50])
def test_valid_cps(value):
    Settings(cps=value).validate()


@pytest.mark.skipif(sys.platform != "win32", reason="Windows API module")
def test_monitor_geometry():
    from uncanny_clicker.mouse_controller import validate_position
    screens = ((-1920, 0, 0, 1080), (0, -1080, 1920, 0), (0, 0, 1920, 1080))
    validate_position(-300, 500, screens)
    validate_position(300, -500, screens)
    for x, y in [(-300, -500), (1920, 500), (0, 0), (-1920, 1079)]:
        with pytest.raises(ValueError):
            validate_position(x, y, screens)

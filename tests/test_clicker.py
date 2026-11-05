import threading
import time

from uncanny_clicker.clicker import Clicker
from uncanny_clicker.config import Settings


class FakeMouse:
    def __init__(self, fail=False, delay=0):
        self.calls = []
        self.called = threading.Event()
        self.fail = fail
        self.delay = delay

    def prepare(self, x, y):
        pass

    def click(self, x, y, stop):
        if self.fail:
            raise RuntimeError("テスト用の送信失敗")
        if stop.is_set():
            return False
        self.calls.append(time.perf_counter())
        self.called.set()
        if self.delay:
            time.sleep(self.delay)
        return True


def finish(clicker):
    clicker.join(3)
    if clicker.active:
        clicker.stop()
        clicker.join(1)
        raise AssertionError("worker did not finish")
    return clicker.snapshot()


def test_finite():
    mouse = FakeMouse()
    clicker = Clicker(mouse, 0)
    assert clicker.start(Settings(count=4, cps=50))
    result = finish(clicker)
    assert result.state == "完了しました"
    assert result.count == len(mouse.calls) == 4
    assert result.elapsed >= 0.075
    assert 0 < result.average <= 55


def test_unlimited_stop_and_double_start():
    mouse = FakeMouse()
    clicker = Clicker(mouse, 0)
    clicker.start(Settings(unlimited=True))
    assert mouse.called.wait(1)
    assert not clicker.start(Settings())
    clicker.stop()
    clicker.stop()
    result = finish(clicker)
    assert result.state == "停止しました"
    count = len(mouse.calls)
    time.sleep(0.1)
    assert count == len(mouse.calls) == result.count


def test_countdown_stop():
    mouse = FakeMouse()
    clicker = Clicker(mouse)
    clicker.start(Settings())
    clicker.stop()
    result = finish(clicker)
    assert result.state == "停止しました"
    assert result.count == result.elapsed == 0
    assert not mouse.calls


def test_error_and_restart():
    mouse = FakeMouse(fail=True)
    clicker = Clicker(mouse, 0)
    clicker.start(Settings(count=1))
    result = finish(clicker)
    assert result.state == "エラーが発生しました"
    assert result.count == 0
    mouse.fail = False
    assert clicker.start(Settings(count=1))
    assert finish(clicker).state == "完了しました"


def test_no_catch_up_burst():
    mouse = FakeMouse(delay=0.035)
    clicker = Clicker(mouse, 0)
    clicker.start(Settings(count=4, cps=50))
    assert finish(clicker).count == 4
    assert all(b - a >= 0.034 for a, b in zip(mouse.calls, mouse.calls[1:]))


def test_low_cps_stop_interrupts_wait():
    mouse = FakeMouse()
    clicker = Clicker(mouse, 0)
    clicker.start(Settings(cps=1, unlimited=True))
    assert mouse.called.wait(1)
    start = time.perf_counter()
    clicker.stop()
    assert finish(clicker).state == "停止しました"
    assert time.perf_counter() - start < 0.5

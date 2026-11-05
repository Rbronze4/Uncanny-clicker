from dataclasses import dataclass
import threading
import time
from typing import Protocol

from .config import Settings


class Mouse(Protocol):
    def prepare(self, x: int, y: int) -> None: ...
    def click(self, x: int, y: int, stop: threading.Event) -> bool: ...


@dataclass(frozen=True)
class Snapshot:
    state: str = "待機中"
    count: int = 0
    elapsed: float = 0.0
    countdown: int = 0
    detail: str = ""

    @property
    def average(self) -> float:
        return self.count / self.elapsed if self.elapsed else 0.0


class Clicker:
    def __init__(self, mouse: Mouse, countdown: int = 3):
        self.mouse = mouse
        self.countdown = countdown
        self.stop_event = threading.Event()
        self._lock = threading.RLock()
        self._thread: threading.Thread | None = None
        self._snapshot = Snapshot()
        self._reason = ""

    @property
    def active(self) -> bool:
        with self._lock:
            return self._thread is not None and self._thread.is_alive()

    def snapshot(self) -> Snapshot:
        with self._lock:
            return self._snapshot

    def _publish(self, snapshot: Snapshot) -> None:
        with self._lock:
            self._snapshot = snapshot

    def start(self, settings: Settings) -> bool:
        settings.validate()
        with self._lock:
            if self.active:
                return False
            self.stop_event.clear()
            self._reason = ""
            self._snapshot = Snapshot("開始待機中", countdown=self.countdown)
            self._thread = threading.Thread(target=self._run, args=(settings,), name="clicker")
            self._thread.start()
            return True

    def stop(self, reason: str = "停止操作を受け付けました。") -> None:
        with self._lock:
            if self.active and not self.stop_event.is_set():
                self._reason = reason
                self.stop_event.set()

    def join(self, timeout: float | None = None) -> None:
        thread = self._thread
        if thread:
            thread.join(timeout)

    def _run(self, settings: Settings) -> None:
        count = 0
        started = None
        state = "停止しました"
        detail = ""
        try:
            self.mouse.prepare(settings.x, settings.y)
            for seconds in range(self.countdown, 0, -1):
                self._publish(Snapshot("開始待機中", countdown=seconds))
                if self.stop_event.wait(1):
                    return
            if self.stop_event.is_set():
                return
            started = time.perf_counter()
            interval = 1 / settings.cps
            deadline = started
            while not self.stop_event.is_set():
                if self.stop_event.wait(max(0, deadline - time.perf_counter())):
                    break
                # Schedule from the actual start, never catch up missed clicks.
                tick = time.perf_counter()
                if not self.mouse.click(settings.x, settings.y, self.stop_event):
                    break
                count += 1
                self._publish(Snapshot("クリック実行中", count, time.perf_counter() - started))
                deadline = max(tick + interval, time.perf_counter())
                if not settings.unlimited and count >= settings.count:
                    # Include the final interval so a one-click run has a meaningful CPS.
                    interrupted = self.stop_event.wait(max(0, deadline - time.perf_counter()))
                    state = "停止しました" if interrupted else "完了しました"
                    break
        except Exception as error:
            state = "エラーが発生しました"
            detail = str(error) or type(error).__name__
        finally:
            elapsed = time.perf_counter() - started if started is not None else 0.0
            self._publish(Snapshot(state, count, elapsed, detail=detail or self._reason))

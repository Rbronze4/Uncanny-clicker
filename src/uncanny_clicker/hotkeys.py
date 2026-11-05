"""Message loop independent of Tk: emergency stop never waits for the GUI."""
import ctypes as C
from ctypes import wintypes as W
import queue
import threading
import time

from .keybindings import DEFAULT_KEYS, parse_binding
from .mouse_controller import LRESULT, ULONG_PTR, is_corner, kernel32, position, user32

HOOKPROC = C.WINFUNCTYPE(LRESULT, C.c_int, W.WPARAM, W.LPARAM)


class MSLLHOOKSTRUCT(C.Structure):
    _fields_ = [("pt", W.POINT), ("mouseData", W.DWORD), ("flags", W.DWORD),
                ("time", W.DWORD), ("dwExtraInfo", ULONG_PTR)]


user32.SetWindowsHookExW.argtypes = [C.c_int, HOOKPROC, W.HINSTANCE, W.DWORD]
user32.SetWindowsHookExW.restype = W.HANDLE
user32.CallNextHookEx.argtypes = [W.HANDLE, C.c_int, W.WPARAM, W.LPARAM]
user32.CallNextHookEx.restype = LRESULT
user32.UnhookWindowsHookEx.argtypes = [W.HANDLE]
user32.UnhookWindowsHookEx.restype = W.BOOL
user32.RegisterHotKey.argtypes = [W.HWND, C.c_int, W.UINT, W.UINT]
user32.RegisterHotKey.restype = W.BOOL
user32.UnregisterHotKey.argtypes = [W.HWND, C.c_int]
user32.UnregisterHotKey.restype = W.BOOL
user32.PeekMessageW.argtypes = [C.POINTER(W.MSG), W.HWND, W.UINT, W.UINT, W.UINT]
user32.PeekMessageW.restype = W.BOOL
user32.TranslateMessage.argtypes = [C.POINTER(W.MSG)]
user32.DispatchMessageW.argtypes = [C.POINTER(W.MSG)]
user32.DispatchMessageW.restype = LRESULT
kernel32.GetModuleHandleW.argtypes = [W.LPCWSTR]
kernel32.GetModuleHandleW.restype = W.HMODULE


class SafetyService:
    def __init__(self, clicker, bindings=None):
        self.clicker = clicker
        self.bindings = bindings or DEFAULT_KEYS
        self.suspended = threading.Event()
        self.events = queue.SimpleQueue()
        self.capture = threading.Event()
        self.quit = threading.Event()
        self.ready = threading.Event()
        self.safe = False
        self.configured = False
        self.last_stop = 0.0
        self.registered: set[int] = set()
        self.thread = threading.Thread(target=self._run, name="safety")
        self.thread.start()

    def close(self) -> None:
        self.quit.set()
        self.thread.join()

    def _run(self) -> None:
        hook = None

        @HOOKPROC
        def mouse_hook(code, wparam, lparam):
            if code >= 0:
                try:
                    event = C.cast(lparam, C.POINTER(MSLLHOOKSTRUCT)).contents
                    if not event.flags & 1 and is_corner(event.pt.x, event.pt.y, self.clicker.mouse.screens):
                        self.clicker.stop("画面の角へのマウス移動を検出し、安全停止しました。")
                except Exception:
                    self.clicker.stop("マウス監視でエラーが発生したため停止しました。")
            return user32.CallNextHookEx(None, code, wparam, lparam)

        try:
            for key, name in ((6, "capture_key"), (8, "stop_key"), (9, "start_key"), (27, "cancel_key")):
                binding = parse_binding(self.bindings[name])
                if user32.RegisterHotKey(None, key, 0x4000 | binding.modifiers, binding.vk):
                    self.registered.add(key)
                else:
                    self.events.put(("warning", f"{binding.text}を登録できません。他のアプリとの競合を確認してください。"))
            hook = user32.SetWindowsHookExW(14, mouse_hook, kernel32.GetModuleHandleW(None), 0)
            if not hook:
                self.events.put(("warning", "マウスの安全監視を開始できません。開始操作を無効にしています。"))
            self.safe = bool(hook) and 8 in self.registered
            if 8 not in self.registered:
                self.events.put(("warning", "停止キーを利用できないため、開始操作を無効にしています。"))
            self.configured = self.safe and len(self.registered) == 4
            if 27 in self.registered:
                user32.UnregisterHotKey(None, 27)
                self.registered.discard(27)
            self.ready.set()
            message = W.MSG()
            escape_attempted = False
            while not self.quit.is_set():
                if self.capture.is_set() and not escape_attempted:
                    escape_attempted = True
                    binding = parse_binding(self.bindings["cancel_key"])
                    if user32.RegisterHotKey(None, 27, 0x4000 | binding.modifiers, binding.vk):
                        self.registered.add(27)
                    else:
                        self.events.put(("warning", f"{binding.text}を登録できません。画面の「取得をキャンセル」を使用してください。"))
                elif not self.capture.is_set() and escape_attempted:
                    if 27 in self.registered:
                        user32.UnregisterHotKey(None, 27)
                        self.registered.discard(27)
                    escape_attempted = False
                while user32.PeekMessageW(C.byref(message), None, 0, 0, 1):
                    if message.message == 0x0312:
                        key = message.wParam
                        if key == 8:
                            self.last_stop = time.perf_counter()
                            self.clicker.stop(f"{self.bindings['stop_key']}で停止しました。")
                            self.events.put(("cancel", None))
                        elif key == 6 and self.capture.is_set():
                            self.events.put(("position", position()))
                            self.capture.clear()
                        elif key == 27:
                            self.capture.clear()
                            self.events.put(("cancel", None))
                        elif key == 9 and not self.clicker.active and not self.suspended.is_set():
                            self.events.put(("start", time.perf_counter()))
                    else:
                        user32.TranslateMessage(C.byref(message))
                        user32.DispatchMessageW(C.byref(message))
                self.quit.wait(0.005)
        except Exception as error:
            self.events.put(("warning", f"安全監視を終了しました：{error}"))
        finally:
            self.safe = False
            self.clicker.stop("安全監視が終了したため停止しました。")
            self.ready.set()
            if hook:
                user32.UnhookWindowsHookEx(hook)
            for key in self.registered:
                user32.UnregisterHotKey(None, key)

"""Physical-pixel Windows coordinates; no PyAutoGUI dependency."""
import ctypes as C
from ctypes import wintypes as W
import threading

user32 = C.WinDLL("user32", use_last_error=True)
kernel32 = C.WinDLL("kernel32", use_last_error=True)
LRESULT = C.c_ssize_t
ULONG_PTR = C.c_size_t


class MOUSEINPUT(C.Structure):
    _fields_ = [("dx", W.LONG), ("dy", W.LONG), ("mouseData", W.DWORD),
                ("dwFlags", W.DWORD), ("time", W.DWORD), ("dwExtraInfo", ULONG_PTR)]


class INPUTUNION(C.Union):
    _fields_ = [("mi", MOUSEINPUT)]


class INPUT(C.Structure):
    _anonymous_ = ("value",)
    _fields_ = [("type", W.DWORD), ("value", INPUTUNION)]


MONITORPROC = C.WINFUNCTYPE(W.BOOL, W.HMONITOR, W.HDC, C.POINTER(W.RECT), W.LPARAM)
user32.EnumDisplayMonitors.argtypes = [W.HDC, C.POINTER(W.RECT), MONITORPROC, W.LPARAM]
user32.EnumDisplayMonitors.restype = W.BOOL
user32.GetCursorPos.argtypes = [C.POINTER(W.POINT)]
user32.GetCursorPos.restype = W.BOOL
user32.SetCursorPos.argtypes = [C.c_int, C.c_int]
user32.SetCursorPos.restype = W.BOOL
user32.SendInput.argtypes = [W.UINT, C.POINTER(INPUT), C.c_int]
user32.SendInput.restype = W.UINT
user32.SetProcessDpiAwarenessContext.argtypes = [W.HANDLE]
user32.SetProcessDpiAwarenessContext.restype = W.BOOL
user32.GetThreadDpiAwarenessContext.restype = W.HANDLE
user32.GetAwarenessFromDpiAwarenessContext.argtypes = [W.HANDLE]
user32.GetAwarenessFromDpiAwarenessContext.restype = C.c_int


def enable_dpi() -> None:
    user32.SetProcessDpiAwarenessContext(C.c_void_p(-4))
    context = user32.GetThreadDpiAwarenessContext()
    if user32.GetAwarenessFromDpiAwarenessContext(context) != 2:
        raise RuntimeError("画面のDPI設定を初期化できません。アプリを再起動してください。")


def monitors() -> tuple[tuple[int, int, int, int], ...]:
    rectangles = []

    @MONITORPROC
    def collect(_monitor, _dc, rect, _data):
        r = rect.contents
        rectangles.append((r.left, r.top, r.right, r.bottom))
        return True

    if not user32.EnumDisplayMonitors(None, None, collect, 0) or not rectangles:
        raise RuntimeError("ディスプレイ情報を取得できません。")
    return tuple(sorted(rectangles))


def position() -> tuple[int, int]:
    point = W.POINT()
    if not user32.GetCursorPos(C.byref(point)):
        raise RuntimeError("マウス位置を取得できません。")
    return point.x, point.y


def is_corner(x: int, y: int, screens: tuple) -> bool:
    return any(x in (left, right - 1) and y in (top, bottom - 1)
               for left, top, right, bottom in screens)


def validate_position(x: int, y: int, screens: tuple) -> None:
    if not any(left <= x < right and top <= y < bottom for left, top, right, bottom in screens):
        raise ValueError("座標がディスプレイの範囲外です。位置を取得し直してください。")
    if is_corner(x, y, screens):
        raise ValueError("画面の角は緊急停止用です。少し内側の座標を指定してください。")


class WindowsMouse:
    def __init__(self):
        self.screens = monitors()

    def prepare(self, x: int, y: int) -> None:
        self.screens = monitors()
        validate_position(x, y, self.screens)

    def click(self, x: int, y: int, stop: threading.Event) -> bool:
        if monitors() != self.screens:
            raise RuntimeError("ディスプレイ構成が変更されたため停止しました。位置を取得し直してください。")
        if is_corner(*position(), self.screens):
            raise RuntimeError("画面の角へのマウス移動を検出し、安全停止しました。")
        if stop.is_set():
            return False
        if not user32.SetCursorPos(x, y):
            raise RuntimeError("マウスを指定位置へ移動できません。")
        if position() != (x, y):
            raise RuntimeError("指定位置へ移動できなかったため停止しました。マウスの移動制限を確認してください。")
        if stop.is_set():
            return False
        inputs = (INPUT * 2)()
        inputs[0].mi.dwFlags = 0x0002
        inputs[1].mi.dwFlags = 0x0004
        if user32.SendInput(2, inputs, C.sizeof(INPUT)) != 2:
            release = INPUT()
            release.mi.dwFlags = 0x0004
            user32.SendInput(1, C.byref(release), C.sizeof(INPUT))
            raise RuntimeError("クリックを送信できません。対象アプリの権限やデスクトップ状態を確認してください。")
        return True

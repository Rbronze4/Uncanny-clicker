"""Validate user-editable Windows hotkey combinations without using the GUI."""
from dataclasses import dataclass

KEYS = {**{chr(n): n for n in range(65, 91)}, **{str(n): 48 + n for n in range(10)},
        **{f"F{n}": 0x6F + n for n in range(1, 25) if n != 12},
        "Esc": 0x1B, "Space": 0x20, "Enter": 0x0D, "Tab": 0x09,
        "Home": 0x24, "End": 0x23, "PageUp": 0x21, "PageDown": 0x22,
        "Insert": 0x2D, "Delete": 0x2E, "Backspace": 0x08,
        "Left": 0x25, "Up": 0x26, "Right": 0x27, "Down": 0x28,
        **{f"Num{n}": 0x60 + n for n in range(10)}}
MODIFIERS = {"Ctrl": 2, "Alt": 1, "Shift": 4, "Win": 8}
DEFAULT_KEYS = {"capture_key": "F6", "stop_key": "F8", "start_key": "F9", "cancel_key": "Esc"}


@dataclass(frozen=True)
class Binding:
    text: str
    modifiers: int
    vk: int


def parse_binding(text: str) -> Binding:
    if not isinstance(text, str):
        raise ValueError("ショートカットキーを文字列で指定してください。")
    parts = [part.strip().lower() for part in text.split("+")]
    names = {key.lower(): key for key in KEYS}
    mods = {key.lower(): key for key in MODIFIERS}
    if not parts or parts[-1] not in names or any(p not in mods for p in parts[:-1]):
        raise ValueError("キーの形式を確認してください（例：F6、Ctrl+Shift+A）。F12はWindows予約キーです。")
    if len(set(parts[:-1])) != len(parts[:-1]):
        raise ValueError("同じ修飾キーを重複して指定できません。")
    selected = {mods[p] for p in parts[:-1]}
    key = names[parts[-1]]
    if (key == "F4" and "Alt" in selected) or (key == "Delete" and {"Ctrl", "Alt"} <= selected) or (key == "L" and "Win" in selected):
        raise ValueError("終了やロックに使うシステムキーは指定できません。")
    ordered = [mod for mod in MODIFIERS if mod in selected]
    return Binding("+".join(ordered + [key]), sum(MODIFIERS[m] for m in selected), KEYS[key])


def validate_bindings(values: dict[str, str]) -> dict[str, str]:
    parsed = {name: parse_binding(values[name]) for name in DEFAULT_KEYS}
    if len({(b.modifiers, b.vk) for b in parsed.values()}) != len(parsed):
        raise ValueError("各操作には異なるショートカットキーを指定してください。")
    return {name: binding.text for name, binding in parsed.items()}

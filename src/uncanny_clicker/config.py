from dataclasses import asdict, dataclass
import json
import os
from pathlib import Path
import tempfile
from .keybindings import DEFAULT_KEYS, validate_bindings


def integer(value: object, label: str, low: int, high: int) -> int:
    if isinstance(value, bool) or not isinstance(value, (int, str)):
        raise ValueError(f"{label}は整数で入力してください。")
    try:
        result = int(value)
    except (ValueError, TypeError):
        raise ValueError(f"{label}は整数で入力してください。") from None
    if not low <= result <= high:
        raise ValueError(f"{label}は{low:,}〜{high:,}で入力してください。")
    return result


@dataclass(frozen=True)
class Settings:
    x: int = 500
    y: int = 300
    cps: int = 16
    count: int = 100
    unlimited: bool = False
    capture_key: str = "F6"
    stop_key: str = "F8"
    start_key: str = "F9"
    cancel_key: str = "Esc"

    def validate(self) -> "Settings":
        validate_bindings({name: getattr(self, name) for name in DEFAULT_KEYS})
        integer(self.x, "X座標", -2147483648, 2147483647)
        integer(self.y, "Y座標", -2147483648, 2147483647)
        integer(self.cps, "速度", 1, 50)
        integer(self.count, "クリック回数", 1, 1_000_000)
        if type(self.unlimited) is not bool:
            raise ValueError("無制限モードの設定が不正です。")
        if any(type(v) is not int for v in (self.x, self.y, self.cps, self.count)):
            raise ValueError("設定の数値型が不正です。")
        return self


def config_path() -> Path:
    return Path(os.environ.get("APPDATA", Path.home() / "AppData/Roaming")) / "UncannyClicker/config.json"


def load(path: Path) -> tuple[Settings, str]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            raise ValueError("object expected")
        return Settings(**data).validate(), ""
    except FileNotFoundError:
        return Settings(), ""
    except (OSError, ValueError, TypeError):
        return Settings(), "設定を読み込めないため、初期値で起動しました。"


def save(path: Path, settings: Settings) -> None:
    settings.validate()
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=path.parent, delete=False) as file:
            temp = Path(file.name)
            json.dump(asdict(settings), file, ensure_ascii=False, indent=2)
            file.flush()
            os.fsync(file.fileno())
        os.replace(temp, path)
    finally:
        if temp is not None:
            temp.unlink(missing_ok=True)

import sys


def main() -> None:
    if sys.platform != "win32":
        raise SystemExit("Uncanny ClickerはWindows 10/11専用です。")
    try:
        from .mouse_controller import enable_dpi
        enable_dpi()
        import customtkinter as ctk
        from .gui import App
        ctk.set_appearance_mode("system")
        App().mainloop()
    except Exception as error:
        import ctypes
        ctypes.windll.user32.MessageBoxW(None, f"起動できませんでした。\n{error}", "Uncanny Clicker", 0x10)


if __name__ == "__main__":
    main()

import customtkinter as ctk

from .keybindings import DEFAULT_KEYS, validate_bindings


class SettingsDialog(ctk.CTkToplevel):
    def __init__(self, parent, values, apply, cancel):
        super().__init__(parent)
        self.title("設定 — ショートカットキー")
        self.geometry("510x520")
        self.minsize(460, 400)
        self.transient(parent)
        self.apply_callback = apply
        self.cancel_callback = cancel
        self.applying = False
        self.variables = {}
        self.controls = []
        self.protocol("WM_DELETE_WINDOW", self.cancel)
        body = ctk.CTkScrollableFrame(self)
        body.pack(fill="both", expand=True, padx=16, pady=16)
        body.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(body, text="ショートカットキー", font=ctk.CTkFont(size=20, weight="bold")).grid(row=0, columnspan=2, sticky="w", pady=8)
        ctk.CTkLabel(body, text="各操作のキーを入力してください。\n例：F6、Ctrl+Shift+A、Alt+Space\nCtrl・Alt・Shift・Winと、英数字／Fキー／方向キー等を指定できます。\nF12や一部のシステムキーは使用できません。", justify="left", wraplength=440).grid(row=1, columnspan=2, sticky="w", pady=8)
        for row, (name, label) in enumerate((("capture_key", "位置を確定"), ("start_key", "開始"), ("stop_key", "停止"), ("cancel_key", "取得をキャンセル")), 2):
            ctk.CTkLabel(body, text=label).grid(row=row, column=0, sticky="w", padx=(0, 12), pady=8)
            var = ctk.StringVar(value=values[name])
            self.variables[name] = var
            entry = ctk.CTkEntry(body, textvariable=var)
            entry.grid(row=row, column=1, sticky="ew", pady=8)
            self.controls.append(entry)
        self.error = ctk.CTkLabel(body, text="", wraplength=440, justify="left", text_color=("#A42B16", "#FFB49F"))
        self.error.grid(row=6, columnspan=2, sticky="w", pady=8)
        for row, text, command in ((7, "初期値に戻す", self.reset), (8, "保存して適用", self.apply), (9, "キャンセル", self.cancel)):
            button = ctk.CTkButton(body, text=text, command=command)
            button.grid(row=row, columnspan=2, sticky="ew", pady=5)
            self.controls.append(button)
        self.after(100, self.grab_set)

    def reset(self):
        for name, value in DEFAULT_KEYS.items():
            self.variables[name].set(value)

    def apply(self):
        try:
            values = validate_bindings({name: var.get() for name, var in self.variables.items()})
        except ValueError as error:
            self.show_error(str(error))
            return
        self.applying = True
        for control in self.controls:
            control.configure(state="disabled")
        self.error.configure(text="キーの登録と保存を確認しています…")
        self.apply_callback(values)

    def show_error(self, text):
        self.applying = False
        for control in self.controls:
            control.configure(state="normal")
        self.error.configure(text=text)

    def cancel(self):
        if not self.applying:
            self.cancel_callback()

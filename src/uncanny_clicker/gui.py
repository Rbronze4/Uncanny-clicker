import queue
import time
from dataclasses import replace
from tkinter import messagebox

import customtkinter as ctk

from .clicker import Clicker
from .config import Settings, config_path, integer, load, save
from .hotkeys import SafetyService
from .keybindings import DEFAULT_KEYS, validate_bindings
from .settings_dialog import SettingsDialog
from .mouse_controller import WindowsMouse, monitors, validate_position


class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Uncanny Clicker")
        self.geometry("560x690")
        self.minsize(460, 480)
        self.settings, warning = load(config_path())
        self.clicker = Clicker(WindowsMouse())
        self.safety = SafetyService(self.clicker, self.key_values())
        self.settings_window = None
        self.capturing = False
        self.closing = False
        self.warnings = [warning] if warning else []
        self.x = ctk.StringVar(value=str(self.settings.x))
        self.y = ctk.StringVar(value=str(self.settings.y))
        self.count = ctk.StringVar(value=str(self.settings.count))
        self.unlimited = ctk.BooleanVar(value=self.settings.unlimited)
        self.cps = ctk.IntVar(value=self.settings.cps)
        self.status = ctk.StringVar(value="待機中")
        self.progress_text = ctk.StringVar(value="0 回")
        self.result = ctk.StringVar(value="実行結果はここに表示されます。")
        self.warning_text = ctk.StringVar(value="\n".join(self.warnings))
        self.editable = []
        body = ctk.CTkScrollableFrame(self, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=16, pady=12)
        body.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(body, text="Uncanny Clicker", font=ctk.CTkFont(size=26, weight="bold")).grid(row=0, sticky="w", pady=(0, 3))
        ctk.CTkLabel(body, text="クリック位置を選び、速度と回数を設定して開始").grid(row=1, sticky="w", pady=(0, 12))
        card = ctk.CTkFrame(body)
        card.grid(row=2, sticky="ew", pady=6)
        card.grid_columnconfigure((1, 3), weight=1)
        ctk.CTkLabel(card, text="1  クリック位置", font=ctk.CTkFont(weight="bold")).grid(row=0, column=0, columnspan=4, sticky="w", padx=12, pady=8)
        for column, label, variable in ((0, "X", self.x), (2, "Y", self.y)):
            ctk.CTkLabel(card, text=label).grid(row=1, column=column, padx=12)
            entry = ctk.CTkEntry(card, textvariable=variable, width=120)
            entry.grid(row=1, column=column + 1, sticky="ew", padx=(0, 12))
            self.editable.append(entry)
        self.capture_button = ctk.CTkButton(card, text="マウス位置を取得", command=self.toggle_capture)
        self.capture_button.grid(row=2, column=0, columnspan=4, sticky="ew", padx=12, pady=12)
        self.editable.append(self.capture_button)
        card = ctk.CTkFrame(body)
        card.grid(row=3, sticky="ew", pady=6)
        card.grid_columnconfigure(0, weight=1)
        self.speed_label = ctk.CTkLabel(card, text=f"2  クリック速度  {self.cps.get()} CPS", font=ctk.CTkFont(weight="bold"))
        self.speed_label.grid(row=0, sticky="w", padx=12, pady=8)
        slider = ctk.CTkSlider(card, from_=1, to=50, number_of_steps=49, variable=self.cps, command=self.speed_changed)
        slider.grid(row=1, sticky="ew", padx=12, pady=(0, 12))
        self.editable.append(slider)
        ctk.CTkLabel(card, text="3  クリック回数（1〜1,000,000回）", font=ctk.CTkFont(weight="bold")).grid(row=2, sticky="w", padx=12)
        self.count_entry = ctk.CTkEntry(card, textvariable=self.count)
        self.count_entry.grid(row=3, sticky="ew", padx=12, pady=6)
        self.editable.append(self.count_entry)
        switch = ctk.CTkSwitch(card, text="停止するまで繰り返す（無制限）", variable=self.unlimited, command=self.update_controls)
        switch.grid(row=4, sticky="w", padx=12, pady=(4, 12))
        self.editable.append(switch)
        buttons = ctk.CTkFrame(body, fg_color="transparent")
        buttons.grid(row=4, sticky="ew", pady=10)
        buttons.grid_columnconfigure((0, 1), weight=1)
        self.start_button = ctk.CTkButton(buttons, text="開始  F9", height=42, command=self.start)
        self.start_button.grid(row=0, column=0, sticky="ew", padx=(0, 6))
        self.stop_button = ctk.CTkButton(buttons, text="停止  F8", height=42, fg_color=("#B42318", "#A52A25"), hover_color="#7A1B17", command=self.stop)
        self.stop_button.grid(row=0, column=1, sticky="ew", padx=(6, 0))
        ctk.CTkLabel(body, textvariable=self.status, font=ctk.CTkFont(size=16, weight="bold"), wraplength=480).grid(row=5, sticky="w")
        ctk.CTkLabel(body, textvariable=self.progress_text).grid(row=6, sticky="w")
        self.bar = ctk.CTkProgressBar(body)
        self.bar.grid(row=7, sticky="ew", pady=4)
        self.bar.set(0)
        ctk.CTkLabel(body, textvariable=self.result, justify="left", wraplength=480).grid(row=8, sticky="w", pady=6)
        self.key_help = ctk.CTkLabel(body, text="", justify="left", wraplength=480)
        self.key_help.grid(row=9, sticky="w", pady=6)
        self.settings_button = ctk.CTkButton(body, text="設定（ショートカットキー）", command=self.open_settings)
        self.settings_button.grid(row=11, sticky="ew", pady=8)
        self.refresh_keys()
        ctk.CTkLabel(body, textvariable=self.warning_text, text_color=("#A42B16", "#FFB49F"), justify="left", wraplength=480).grid(row=10, sticky="w")
        self.protocol("WM_DELETE_WINDOW", self.close)
        self.after(50, self.poll)
        self.update_controls()

    def key_values(self):
        return {name: getattr(self.settings, name) for name in DEFAULT_KEYS}

    def refresh_keys(self):
        self.start_button.configure(text=f"開始  {self.settings.start_key}")
        self.stop_button.configure(text=f"停止  {self.settings.stop_key}")
        self.key_help.configure(text=f"{self.settings.capture_key}：位置確定 / {self.settings.cancel_key}：取得取消\n"
                                f"{self.settings.start_key}：開始 / {self.settings.stop_key}：緊急停止\n"
                                "マウスをいずれかの画面の角へ移動しても停止します。")

    def open_settings(self):
        if self.clicker.active or self.capturing or self.settings_window is not None:
            return
        self.safety.suspended.set()
        self.settings_window = SettingsDialog(self, self.key_values(), self.apply_keys, self.dismiss_settings)
        self.update_controls()

    def dismiss_settings(self):
        if self.settings_window is not None:
            self.settings_window.destroy()
            self.settings_window = None
        self.safety.last_stop = time.perf_counter()
        self.safety.suspended.clear()
        self.update_controls()

    def apply_keys(self, values):
        values = validate_bindings(values)
        self.safety.close()
        self.safety = SafetyService(self.clicker, values)
        self.safety.suspended.set()
        self.after(20, lambda: self.finish_apply_keys(values))

    def finish_apply_keys(self, values):
        if self.closing:
            return
        if not self.safety.ready.is_set():
            self.after(20, lambda: self.finish_apply_keys(values))
            return
        error = ""
        if not self.safety.configured:
            messages = []
            while not self.safety.events.empty():
                kind, detail = self.safety.events.get()
                if kind == "warning":
                    messages.append(detail)
            error = "\n".join(messages) or "キーを登録できません。他の組み合わせを指定してください。"
        else:
            try:
                updated = replace(self.settings, **values)
                save(config_path(), updated)
            except (ValueError, OSError) as exc:
                error = f"設定を保存できませんでした：{exc}"
        if error:
            self.safety.close()
            self.safety = SafetyService(self.clicker, self.key_values())
            self.safety.suspended.set()
            self.settings_window.show_error(error + "\n変更前のキーに戻しました。")
        else:
            self.settings = updated
            self.refresh_keys()
            self.dismiss_settings()

    def speed_changed(self, value):
        self.speed_label.configure(text=f"2  クリック速度  {round(value)} CPS")

    def read_settings(self) -> Settings:
        return Settings(integer(self.x.get(), "X座標", -2147483648, 2147483647),
                        integer(self.y.get(), "Y座標", -2147483648, 2147483647),
                        self.cps.get(),
                        self.settings.count if self.unlimited.get() else integer(self.count.get(), "クリック回数", 1, 1_000_000),
                        self.unlimited.get(), **self.key_values()).validate()

    def update_controls(self):
        busy = self.clicker.active or self.closing or self.settings_window is not None
        for widget in self.editable:
            widget.configure(state="disabled" if busy else "normal")
        self.count_entry.configure(state="disabled" if busy or self.unlimited.get() else "normal")
        self.start_button.configure(state="disabled" if busy or self.capturing or not self.safety.safe else "normal")
        self.stop_button.configure(state="normal" if busy or self.capturing else "disabled")
        self.settings_button.configure(state="disabled" if busy or self.capturing else "normal")
        if 6 not in self.safety.registered:
            self.capture_button.configure(state="disabled")

    def warn(self, text):
        if text not in self.warnings:
            self.warnings.append(text)
        self.warning_text.set("\n".join(self.warnings))

    def toggle_capture(self):
        if self.capturing:
            self.cancel_capture()
        elif not self.clicker.active:
            self.capturing = True
            self.safety.capture.set()
            self.capture_button.configure(text="取得をキャンセル")
            self.status.set(f"位置取得中：{self.settings.capture_key}で確定 / {self.settings.cancel_key}で取消")
            self.update_controls()

    def cancel_capture(self):
        self.capturing = False
        self.safety.capture.clear()
        self.capture_button.configure(text="マウス位置を取得")
        self.status.set(self.clicker.snapshot().state)
        self.update_controls()

    def start(self):
        if self.closing or self.settings_window is not None or self.capturing or self.clicker.active or not self.safety.safe:
            return
        try:
            settings = self.read_settings()
            validate_position(settings.x, settings.y, monitors())
            self.settings = settings
            self.clicker.start(settings)
            self.update_controls()
        except (ValueError, RuntimeError) as error:
            self.status.set("エラーが発生しました")
            messagebox.showerror("入力を確認してください", str(error), parent=self)

    def stop(self):
        self.clicker.stop()
        if self.capturing:
            self.cancel_capture()

    def poll(self):
        if self.closing:
            return
        while self.settings_window is None:
            try:
                kind, value = self.safety.events.get_nowait()
            except queue.Empty:
                break
            if kind == "warning":
                self.warn(value)
            elif kind == "start" and value > self.safety.last_stop:
                self.start()
            elif kind == "cancel" and self.capturing:
                self.cancel_capture()
            elif kind == "position" and self.capturing:
                self.x.set(str(value[0]))
                self.y.set(str(value[1]))
                self.cancel_capture()
        snapshot = self.clicker.snapshot()
        if not self.capturing:
            self.status.set(f"{snapshot.countdown}秒後に開始します" if snapshot.state == "開始待機中" else snapshot.state)
        self.progress_text.set(f"{snapshot.count:,} 回（無制限）" if self.settings.unlimited else f"{snapshot.count:,} / {self.settings.count:,} 回")
        self.bar.set(0 if self.settings.unlimited else min(1, snapshot.count / self.settings.count))
        if snapshot.state in ("停止しました", "完了しました", "エラーが発生しました"):
            self.result.set(f"実行回数：{snapshot.count:,}回  /  実行時間：{snapshot.elapsed:.2f}秒\n平均速度：{snapshot.average:.1f} CPS\n{snapshot.detail}")
        self.update_controls()
        self.after(50, self.poll)

    def close(self):
        if self.closing:
            return
        self.closing = True
        self.clicker.stop("アプリ終了により停止しました。")
        self.safety.capture.clear()
        self.update_controls()
        self.after(20, self.finish_close)

    def finish_close(self):
        if self.clicker.active:
            self.after(20, self.finish_close)
            return
        self.clicker.join()
        self.safety.close()
        try:
            settings = self.read_settings()
        except ValueError:
            settings = self.settings
        try:
            save(config_path(), settings)
        except OSError as error:
            messagebox.showwarning("設定を保存できません", f"次回は以前の設定で起動します。\n{error}", parent=self)
        self.destroy()

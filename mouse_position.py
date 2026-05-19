import pyautogui
import time

print("現在のマウス座標を表示します。Ctrl + C で終了します。")
print()

try:
    while True:
        x, y = pyautogui.position()
        print(f"X: {x}, Y: {y}        ", end="\r")
        time.sleep(0.05)
except KeyboardInterrupt:
    print("\n終了しました。")
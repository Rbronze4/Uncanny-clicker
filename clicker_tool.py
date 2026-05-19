import pyautogui
import time

# PyAutoGUIが各操作後に入れる待ち時間をなくす
pyautogui.PAUSE = 0

def main():
    print("=== 連続クリックツール ===")
    print("停止したい場合は、マウスを画面の角に移動してください。")
    print()

    try:
        x = int(input("クリックするX座標を入力してください: "))
        y = int(input("クリックするY座標を入力してください: "))
        click_count = int(input("クリック回数を入力してください: "))

        if click_count <= 0:
            print("クリック回数は1以上を指定してください。")
            return

    except ValueError:
        print("数値を入力してください。")
        return

    cps = 16
    interval = 1 / cps

    print()
    print(f"指定座標: X={x}, Y={y}")
    print(f"クリック回数: {click_count}")
    print(f"速度: 1秒あたり{cps}回")
    print("3秒後に開始します。")
    time.sleep(3)

    print("クリック開始")

    start_time = time.perf_counter()

    try:
        for i in range(click_count):
            pyautogui.click(x=x, y=y)

            # 次にクリックすべき時刻を計算
            next_time = start_time + ((i + 1) * interval)

            # 必要な分だけ待つ
            while True:
                now = time.perf_counter()
                remaining = next_time - now
                if remaining <= 0:
                    break
                time.sleep(min(remaining, 0.001))

            if (i + 1) % 16 == 0:
                elapsed = time.perf_counter() - start_time
                print(f"{i + 1}回クリックしました / 経過時間: {elapsed:.2f}秒")

        elapsed = time.perf_counter() - start_time
        print()
        print("クリック完了")
        print(f"実行時間: {elapsed:.2f}秒")
        print(f"平均クリック速度: {click_count / elapsed:.2f}回/秒")

    except pyautogui.FailSafeException:
        print()
        print("安全停止しました。")
        print("マウスが画面の角に移動したため、クリックを中断しました。")

if __name__ == "__main__":
    main()
# v1.0 実装報告

## 作業結果

2026-11-05、既存リポジトリのコミット `55bce2f32450f9e01b0c70bb8ef099b564756bed` を履歴ごと取得し、ローカルブランチ `codex/windows-gui-v1` で改修しました。GitHubへのpush、タグ作成、Release公開は行っていません。

日本語CustomTkinter GUI、手動座標・F6取得、Esc取消、1〜50 CPS、回数指定・無制限、3秒カウントダウン、開始・停止、進捗・結果、設定保存を実装しました。F8/F9はRegisterHotKey、物理マウス監視はWH_MOUSE_LLを別スレッドで扱います。

クリックはWindows APIを利用し、負座標、実画面範囲、Per Monitor DPI awareness、モニター配置変更に対応する実装です。自動クリックと物理マウス監視を分離し、送信失敗時はボタン解放を試みて終了します。GUIは50msごとに状態を読み取り、ワーカースレッドからTkを更新しません。

## 既存コードの調査と変更理由

元のCLIはPyAutoGUI、固定16 CPS、time.perf_counterによる間隔管理、3秒のsleep、回数と平均速度の表示を実装していました。間隔管理の考え方と初期値を引き継ぎましたが、遅延時の埋め合わせ連射、GUIのブロック、複数画面の制約を避けるため処理を再設計しました。元の2本のCLIファイルは変更せず、GUIから独立した参考資料として残しています。

## 変更・追加ファイル

- 更新：README.md
- 追加：src/uncanny_clicker/{__init__,main,gui,clicker,hotkeys,mouse_controller,config}.py
- 追加：launcher.py、pyproject.toml、requirements.txt、requirements-dev.txt、.gitignore
- 追加：tests/test_clicker.py、test_config.py、test_validation.py、test_windows.py
- 追加：build.ps1、assets/app.manifest、assets/licenses/、tools/collect_licenses.py
- 追加：.github/workflows/build.yml、LICENSE、THIRD_PARTY_NOTICES.md
- 追加：docs/MANUAL_TESTS.md、本報告

## テスト結果

Windows 11 build 26200、Python 3.13.3 x64、pytest 9.2.0で **44件成功**（ビルド直前の実行：0.65秒）。実マウスクリックを発生させないテストです。

回数・CPS・座標の検証、設定往復・破損復旧・置換失敗時の既存設定保持、指定回数完了、無制限停止、二重開始拒否、カウントダウン中の停止、例外後再開始、低CPSでの即時停止、遅延時の連射防止、INPUT構造体サイズ、画面変更検出、部分送信失敗時のボタン解放、画面角での入力抑止を確認しました。

初回のテストでは環境の一時ディレクトリ権限制限により11件が準備段階でエラーになりました。TEMP/TMPを作業領域へ変更し、全44件成功を確認しました。

UI確認ではビルドしたexeをWindows 11上で起動し、日本語GUIの表示、位置取得ボタンでのモード移行と案内表示を確認しました。F6確認の途中でユーザーの物理EscによるComputer Use停止通知を受けたため、以後の画面操作は実施していません。テスト用アプリの終了操作も行っていません。

## ビルド結果

PyInstaller 6.22.3でWindows x64のonedirビルド成功。Pythonランタイム、Tcl/Tk、CustomTkinterデータを同梱しています。

- dist/UncannyClicker/UncannyClicker.exe
- dist/UncannyClicker-v1.0.0-win64.zip

実際にexeのGUI起動を確認しました。Pythonがインストールされた開発PCでの起動確認であり、Python未インストールPCでの検証ではありません。
ビルド解析時にCustomTkinterのフォント読み込み警告とmacOS専用AppKitに関する警告が出ました。exeの画面は確認できましたが、全DPI・全テーマでの描画保証はしていません。

## 仕様の合理的な調整

- F8またはマウス監視を確保できなければ、警告だけで続行せず開始を禁止します。
- 各画面の角は緊急停止専用とし、クリック対象にできません。
- 仮想デスクトップの外接矩形だけでなく各モニターの実領域を検証し、画面間の空白を拒否します。
- 実行中にディスプレイの矩形構成が変われば自動追従せず停止します。
- 平均CPSの分母には最終クリック後の1間隔を含め、開始前の3秒は除きます。
- 高DPIや小さいウィンドウではスクロールで全項目を操作できます。
- 元リポジトリにライセンスがなかったため、LICENSEには未確定の通知を記載し、権利者に代わるライセンス指定は行っていません。

## 未実装・未検証・既知の制限

必須機能のコードは実装済みですが、仕様書の実機確認をすべて満たした完成版とはまだ判定していません。署名・インストーラー・自動更新・マクロ等の対象外機能は実装していません。

未検証：実クリックでの完了・停止、F6/F8/F9の実操作、非アクティブ時のキー、物理マウスの角での停止、実行中終了、混在DPIと実際の複数モニター、モニター着脱、Windows 10、Python未インストールPC、全テーマ・高DPI、GitHub Actionsのリモート実行。

既知の制限：管理者アプリ等への送信制約、負荷による速度変動、座標にある別ウィンドウをクリックする可能性、キー競合、OSによる低レベルフック解除、プロセス全体停止時の限界があります。モニター変更検出は実画面の矩形比較で、同じ矩形のままの表示属性変更は検出対象外です。実行回数はWindowsへの送信成功数です。

## Release公開までの残作業

1. docs/MANUAL_TESTS.mdに沿って安全なテスト画面・対象PCで実機確認する。
2. 権利者が無料配布・再配布のライセンスを確定し、LICENSEを差し替える。
3. 最終ソースから再ビルドし、ZIP・依存ライセンス・SHA256を確認する。必要に応じてコード署名を検討する。
4. 明示的な許可のもとでGitHubへpushし、Actionsの動作を確認する。
5. 明示的なリリース操作でタグとReleaseを作り、ZIPとSHA256を添付する。

## 参照資料

- https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-sendinput
- https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-registerhotkey
- https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-setprocessdpiawarenesscontext
- https://learn.microsoft.com/en-us/windows/win32/winmsg/lowlevelmouseproc
- https://github.com/TomSchimansky/CustomTkinter/wiki/Packaging

## 2026-11-06 ショートカット設定・公開用READMEの更新

- 設定画面から開始・停止・位置確定・取得取消キーを変更できるようにしました。英数字、Fキー、方向キーなどとCtrl/Alt/Shift/Winの組み合わせに対応します。
- 重複、形式不正、予約キーを検証し、登録・保存失敗時は旧設定へ戻します。停止キーの再登録に失敗した場合は開始を無効にします。
- 設定中の開始を抑止し、保存後はボタン・案内を更新します。キー項目のない旧設定ファイルは初期キーで読み込めます。
- READMEを一般ユーザー向けに再構成し、開発手順をDEVELOPMENT.mdへ分離しました。
- keybindings.py、settings_dialog.py、キー検証・サービス登録のテストを追加しました。config.py、hotkeys.py、gui.py、ビルドスクリプトも更新しています。
- 自動テスト：66件成功、GUI結合テスト4件スキップ。GUIテストをこの制限環境で試した際、Tkウィンドウ生成でWindows例外0xc0000008が発生しました。対話可能なWindows環境で明示的に実行する形式にしています。今回追加した設定画面の実機表示・キー変更操作は未検証です。
- PyInstallerによるWindows x64の再ビルド成功。今回の成果物は `dist-shortcuts/UncannyClicker-v1.0.0-win64.zip` です。元の `dist/` は前回のビルドです。
- GitHubへのpush・Release公開は実施していません。

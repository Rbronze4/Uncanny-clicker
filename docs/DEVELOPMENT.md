# 開発・ビルド

WindowsとPython 3.11以上の64ビット版を使用します。

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
$env:PYTHONPATH = "$PWD\src"
.\.venv\Scripts\python.exe -m uncanny_clicker.main
.\.venv\Scripts\python.exe -m pytest
.\build.ps1 -Python .\.venv\Scripts\python.exe
```

実デスクトップが必要なTk結合テスト4件は通常スキップします。
制限のない対話Windows環境で `$env:UNCANNY_GUI_TESTS = "1"` を設定して
`python -m pytest tests/test_settings_gui.py` を実行してください。
マウス送信とグローバルキー登録はこのテストでもモック化しています。

`dist/UncannyClicker/`と配布ZIPを生成します。exe単独ではなくフォルダ全体を配布してください。
GitHub ActionsはWindowsでビルドしArtifactを作成しますが、Releaseは公開しません。

GUI、実行処理、Windows API、ホットキー、設定保存を分離しています。
`keybindings.py`はショートカットの構文・重複検証、`settings_dialog.py`は設定画面です。
設定変更は待機中のみ可能です。実行開始を抑止した状態で監視サービスを再生成し、
全キーの登録とファイル保存が成功してから反映します。失敗時は旧キーの再登録を試み、
旧停止キーも登録できない場合は開始を無効にします。取消キーは位置取得中のみ占有します。

旧設定ファイルにキー項目がない場合は初期キーを補います。
元のCLIスクリプトは参考資料として保持していますが、新GUI・exeからは使用しません。

実機確認は [MANUAL_TESTS.md](MANUAL_TESTS.md)、初回の検証記録は
[IMPLEMENTATION_REPORT.md](IMPLEMENTATION_REPORT.md) を参照してください。
公開前に実機確認、ライセンス確定、最終ビルド、SHA256確認を行ってください。

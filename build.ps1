param([string]$Python = "python", [string]$DistPath = "dist")
$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot
& $Python -c "import struct,sys; assert sys.platform == 'win32' and struct.calcsize('P') == 8, 'Windows x64 Python is required'"
if ($LASTEXITCODE -ne 0) { throw "Windows x64 Python が必要です。" }
& $Python -m pytest
if ($LASTEXITCODE -ne 0) { throw "テストが失敗しました。" }
& $Python -m PyInstaller --noconfirm --clean --onedir --windowed --name UncannyClicker --distpath $DistPath --paths src --collect-all customtkinter --manifest assets/app.manifest launcher.py
if ($LASTEXITCODE -ne 0) { throw "ビルドが失敗しました。" }
Copy-Item README.md "$DistPath/UncannyClicker/README.md"
Copy-Item THIRD_PARTY_NOTICES.md "$DistPath/UncannyClicker/THIRD_PARTY_NOTICES.md"
Copy-Item LICENSE "$DistPath/UncannyClicker/LICENSE"
Copy-Item docs -Destination "$DistPath/UncannyClicker/docs" -Recurse -Force
& $Python tools/collect_licenses.py "$DistPath/UncannyClicker/licenses"
if ($LASTEXITCODE -ne 0) { throw "ライセンスの収集に失敗しました。" }
Compress-Archive -Path "$DistPath/UncannyClicker" -DestinationPath "$DistPath/UncannyClicker-v1.0.0-win64.zip" -Force
$hash = Get-FileHash "$DistPath/UncannyClicker-v1.0.0-win64.zip" -Algorithm SHA256
"$($hash.Hash)  UncannyClicker-v1.0.0-win64.zip" | Set-Content -Encoding ascii "$DistPath/SHA256SUMS.txt"
$hash

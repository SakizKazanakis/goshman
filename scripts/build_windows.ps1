$ErrorActionPreference = 'Stop'
Set-Location (Split-Path $PSScriptRoot -Parent)
if (-not (Get-Command py -ErrorAction SilentlyContinue)) { throw 'Python launcher py.exe missing' }
py -3.12 -m venv .venv
$py = Join-Path (Get-Location) '.venv\Scripts\python.exe'
& $py -m pip install --upgrade pip
& $py -m pip install -e '.[gui,ai,test]' pyinstaller
& $py -m pytest -q
if ($LASTEXITCODE -ne 0) { throw 'Tests failed: build stopped' }
& $py -m PyInstaller --noconfirm --clean --windowed --name GOSHMAN --collect-all PySide6 --collect-all pydantic --collect-submodules openai --collect-submodules keyring --add-data "goshman/blender_generate.py;goshman" goshman_app.py
if ($LASTEXITCODE -ne 0) { throw 'PyInstaller failed' }
Write-Host "Build output: $(Join-Path (Get-Location) 'dist\GOSHMAN')"
Write-Host 'Blender is a separate required dependency. Installer is not built by this script.'

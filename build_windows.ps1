param(
    [string]$Python = 'python',
    [string]$ISCC = "${env:LOCALAPPDATA}\Programs\Inno Setup 6\ISCC.exe"
)
$ErrorActionPreference = 'Stop'
Set-Location $PSScriptRoot
function Check-Exit([string]$Step) {
    if ($LASTEXITCODE -ne 0) { throw "$Step : code $LASTEXITCODE" }
}
if (!(Test-Path -LiteralPath $ISCC)) { throw 'ISCC.exe introuvable. Fournir -ISCC avec son chemin.' }
& $Python -c "import sys,struct; assert sys.platform=='win32' and struct.calcsize('P')==8, 'Python Windows 64 bits requis'"
Check-Exit 'Verification Python'
& $Python -m venv .venv
Check-Exit 'Creation environnement'
$BuildPython = Join-Path $PSScriptRoot '.venv\Scripts\python.exe'
& $BuildPython -m pip install -r requirements.txt
Check-Exit 'Dependances'
& $BuildPython -m unittest discover -s tests -v
Check-Exit 'Tests'
& $BuildPython packaging/make_icon.py
Check-Exit 'Icone'
& $BuildPython -m PyInstaller --noconfirm --clean --onedir --windowed --noupx --collect-data docx --icon assets/capture.ico --add-data "assets;assets" --version-file packaging/version_info.txt --name StepsShot app.py
Check-Exit 'PyInstaller'
Copy-Item LICENSE dist\StepsShot\LICENSE.txt
& $ISCC packaging\StepsShot.iss
Check-Exit 'Inno Setup'
Get-FileHash installer\StepsShot-1.0.1-Setup.exe -Algorithm SHA256

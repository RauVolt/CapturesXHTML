param(
    [string]$Python = 'python',
    [string]$SigningThumbprint,
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
if (!$SigningThumbprint) {
    Write-Warning 'No certificate supplied: creating a NEW self-signed build identity, not publicly trusted.'
    $SigningThumbprint = & ./packaging/new_signing_certificate.ps1
}
$cert = Get-Item "Cert:\CurrentUser\My\$SigningThumbprint"
[System.IO.File]::WriteAllBytes((Join-Path $PSScriptRoot 'StepsShot-signing.cer'), $cert.RawData)
& $BuildPython packaging/prepare_key.py StepsShot-signing.cer
Check-Exit 'Public key'
& $BuildPython -m unittest discover -s tests -v
Check-Exit 'Tests'
& $BuildPython packaging/make_icon.py
Check-Exit 'Icone'
& $BuildPython -m PyInstaller --noconfirm --clean --onedir --windowed --noupx --collect-data docx --icon assets/capture.ico --add-data "assets;assets" --version-file packaging/version_info.txt --name StepsShot app.py
Check-Exit 'PyInstaller'
Copy-Item LICENSE dist\StepsShot\LICENSE.txt
& ./packaging/sign_file.ps1 -Path dist/StepsShot/StepsShot.exe -Thumbprint $SigningThumbprint
& $BuildPython integrity.py dist/StepsShot
Check-Exit 'Inventory'
& ./packaging/sign_manifest.ps1 -Bundle dist/StepsShot -Thumbprint $SigningThumbprint
& $BuildPython -c "from integrity import verify_installation; verify_installation('dist/StepsShot')"
Check-Exit 'Integrity verification'
$signingHost = (Get-Process -Id $PID).Path
$signCommand = "`$q$signingHost`$q -NoProfile -ExecutionPolicy Bypass -File `$q$PSScriptRoot\packaging\sign_file.ps1`$q -Path `$f -Thumbprint $SigningThumbprint"
& $ISCC '/DSignBuild' "/Sstepssign=$signCommand" packaging\StepsShot.iss
Check-Exit 'Inno Setup'
& ./packaging/sign_file.ps1 -Path installer/StepsShot-1.0.3-Setup.exe -Thumbprint $SigningThumbprint
Get-FileHash installer\StepsShot-1.0.3-Setup.exe -Algorithm SHA256

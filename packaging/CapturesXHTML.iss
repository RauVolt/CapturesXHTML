#ifndef AppDist
  #define AppDist "..\dist\CapturesXHTML"
#endif
[Setup]
AppId={{4C05EE44-EE4F-40C3-8686-294F94E78257}
AppName=CapturesXHTML
AppVersion=1.4.0
DefaultDirName={localappdata}\Programs\CapturesXHTML
DefaultGroupName=CapturesXHTML
PrivilegesRequired=lowest
DisableDirPage=yes
DisableProgramGroupPage=yes
ArchitecturesAllowed=x64compatible
MinVersion=10.0
OutputDir=..\installer
OutputBaseFilename=CapturesXHTML-1.4.0-Setup
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
SetupIconFile=..\assets\capture.ico
UninstallDisplayIcon={app}\CapturesXHTML.exe
CloseApplications=yes
[Languages]
Name: "french"; MessagesFile: "compiler:Languages\French.isl"
[Files]
Source: "{#AppDist}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
[Icons]
Name: "{userprograms}\CapturesXHTML"; Filename: "{app}\CapturesXHTML.exe"
[Run]
Filename: "{app}\CapturesXHTML.exe"; Description: "Ouvrir CapturesXHTML"; Flags: nowait postinstall skipifsilent

[Code]
function InitializeSetup(): Boolean;
var
  InstallPath, Uninstaller: String;
  Choice, ResultCode: Integer;
begin
  Result := True;
  { Silent installations always update; never silently uninstall. }
  if WizardSilent then Exit;
  if not RegQueryStringValue(HKCU,
    'Software\Microsoft\Windows\CurrentVersion\Uninstall\{4C05EE44-EE4F-40C3-8686-294F94E78257}_is1',
    'InstallLocation', InstallPath) then Exit;
  Uninstaller := AddBackslash(InstallPath) + 'unins000.exe';
  if not FileExists(Uninstaller) then Exit;
  Choice := TaskDialogMsgBox('CapturesXHTML est déjà installé',
    'Choisissez une action. Vos documents XHTML et votre historique seront conservés.',
    mbConfirmation, MB_YESNOCANCEL, ['Mettre à jour ou réinstaller',
    'Désinstaller CapturesXHTML', 'Annuler'], 0);
  if Choice = IDYES then Exit;
  Result := False;
  if Choice = IDNO then begin
    if not Exec(Uninstaller, '', InstallPath, SW_SHOWNORMAL, ewWaitUntilTerminated, ResultCode) then
      MsgBox('Impossible de lancer la désinstallation.', mbError, MB_OK);
  end;
end;

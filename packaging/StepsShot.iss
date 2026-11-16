#ifndef AppDist
  #define AppDist "..\dist\StepsShot"
#endif
[Setup]
AppId={{4C05EE44-EE4F-40C3-8686-294F94E78257}
AppName=StepsShot
AppVersion=1.0.2
DefaultDirName={localappdata}\Programs\StepsShot
DefaultGroupName=StepsShot
PrivilegesRequired=lowest
DisableDirPage=yes
DisableProgramGroupPage=yes
ArchitecturesAllowed=x64compatible
MinVersion=10.0
OutputDir=..\installer
OutputBaseFilename=StepsShot-1.0.2-Setup
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
SetupIconFile=..\assets\capture.ico
UninstallDisplayIcon={app}\StepsShot.exe
CloseApplications=yes
[Languages]
Name: "french"; MessagesFile: "compiler:Languages\French.isl"
[Files]
Source: "{#AppDist}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
[Icons]
Name: "{userprograms}\StepsShot"; Filename: "{app}\StepsShot.exe"
[InstallDelete]
Type: files; Name: "{userprograms}\CapturesXHTML.lnk"
Type: files; Name: "{app}\CapturesXHTML.exe"
[Run]
Filename: "{app}\StepsShot.exe"; Description: "Ouvrir StepsShot"; Flags: nowait postinstall skipifsilent

[Code]
function MaintenanceChoice(): Integer;
begin
  Result := TaskDialogMsgBox('StepsShot est déjà installé',
    'Choisissez une action. Vos documents et votre historique seront conservés.',
    mbConfirmation, MB_YESNOCANCEL, ['Mettre à jour ou réinstaller',
    'Désinstaller StepsShot'], 0);
end;

function InitializeSetup(): Boolean;
var
  InstallPath, Uninstaller: String;
  Choice, ResultCode: Integer;
begin
  Result := True;
#ifdef MaintenanceDialogTest
  Choice := MaintenanceChoice();
  Result := False;
  Exit;
#endif
  { Silent installations always update; never silently uninstall. }
  if WizardSilent then Exit;
  if not RegQueryStringValue(HKCU,
    'Software\Microsoft\Windows\CurrentVersion\Uninstall\{4C05EE44-EE4F-40C3-8686-294F94E78257}_is1',
    'InstallLocation', InstallPath) then Exit;
  Uninstaller := AddBackslash(InstallPath) + 'unins000.exe';
  if not FileExists(Uninstaller) then Exit;
  Choice := MaintenanceChoice();
  if Choice = IDYES then Exit;
  Result := False;
  if Choice = IDNO then begin
    if not Exec(Uninstaller, '', InstallPath, SW_SHOWNORMAL, ewWaitUntilTerminated, ResultCode) then
      MsgBox('Impossible de lancer la désinstallation.', mbError, MB_OK);
  end;
end;

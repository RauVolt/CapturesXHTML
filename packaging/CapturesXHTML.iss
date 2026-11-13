#ifndef AppDist
  #define AppDist "..\dist\CapturesXHTML"
#endif
[Setup]
AppId={{4C05EE44-EE4F-40C3-8686-294F94E78257}
AppName=CapturesXHTML
AppVersion=1.2.0
DefaultDirName={localappdata}\Programs\CapturesXHTML
DefaultGroupName=CapturesXHTML
PrivilegesRequired=lowest
DisableDirPage=yes
DisableProgramGroupPage=yes
ArchitecturesAllowed=x64compatible
MinVersion=10.0
OutputDir=..\installer
OutputBaseFilename=CapturesXHTML-1.2.0-Setup
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
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

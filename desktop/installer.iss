#define AppVersion "0.1.0"
[Setup]
AppId={{CAF0DA60-C25D-4A21-9080-78D57BEA8F0B}
AppName=Navix Desktop
AppVersion={#AppVersion}
AppPublisher=Navix Desktop
DefaultDirName={localappdata}\Programs\NavixDesktop
DefaultGroupName=Navix Desktop
PrivilegesRequired=lowest
OutputDir=output
OutputBaseFilename=NavixDesktop-Setup-0.1.0
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
UninstallDisplayIcon={app}\NavixDesktop.exe
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
CloseApplications=yes
[Languages]
Name: "brazilianportuguese"; MessagesFile: "compiler:Languages\BrazilianPortuguese.isl"
[Files]
Source: "dist\NavixDesktop\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
[Icons]
Name: "{group}\Navix Desktop"; Filename: "{app}\NavixDesktop.exe"
Name: "{autodesktop}\Navix Desktop"; Filename: "{app}\NavixDesktop.exe"
[Run]
Filename: "{app}\NavixDesktop.exe"; Description: "Abrir Navix Desktop"; Flags: nowait postinstall skipifsilent

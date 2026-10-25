#define AppVersion "0.2.4"
[Setup]
AppId={{CAF0DA60-C25D-4A21-9080-78D57BEA8F0B}
AppName=NavixX Desktop
AppVersion={#AppVersion}
AppPublisher=NavixX
DefaultDirName={localappdata}\Programs\NavixDesktop
DefaultGroupName=Navix Desktop
PrivilegesRequired=lowest
OutputDir=output
OutputBaseFilename=NavixDesktop-Setup-{#AppVersion}
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
WizardImageFile=assets\wizard.png
WizardSmallImageFile=assets\wizard-small.png
DisableWelcomePage=no
SetupIconFile=assets\navix.ico
UninstallDisplayIcon={app}\NavixDesktop.exe
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
CloseApplications=yes
[Languages]
Name: "brazilianportuguese"; MessagesFile: "compiler:Languages\BrazilianPortuguese.isl"
[Files]
Source: "dist\NavixDesktop\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
[Icons]
Name: "{group}\NavixX Desktop"; Filename: "{app}\NavixDesktop.exe"
Name: "{autodesktop}\NavixX Desktop"; Filename: "{app}\NavixDesktop.exe"
[Run]
Filename: "{app}\NavixDesktop.exe"; Description: "Abrir NavixX Desktop agora"; Flags: nowait postinstall skipifsilent

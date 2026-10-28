#define AppVersion "0.3.0-alpha.6"
[Setup]
AppId={{A8472D5E-3E92-4421-9B37-FC77C8D3F073}
AppName=NavixX Desktop Cloud Preview
AppVersion={#AppVersion}
AppPublisher=ALFAMNA
AppCopyright=ALFAMNA © 2026 — Todos os direitos reservados.
DefaultDirName={localappdata}\Programs\NavixDesktopCloudPreview
DefaultGroupName=NavixX Cloud Preview
PrivilegesRequired=lowest
OutputDir=output-cloud-preview
OutputBaseFilename=NavixDesktop-CloudPreview-Setup-{#AppVersion}
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
WizardImageFile=assets\wizard.png
WizardSmallImageFile=assets\wizard-small.png
SetupIconFile=assets\navix.ico
UninstallDisplayIcon={app}\NavixDesktop.exe
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
CloseApplications=yes
[Languages]
Name: "brazilianportuguese"; MessagesFile: "compiler:Languages\BrazilianPortuguese.isl"
Name: "english"; MessagesFile: "compiler:Default.isl"
[Files]
Source: "dist\NavixDesktop\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "assets\navix-cloud-preview.flag"; DestDir: "{app}"; Flags: ignoreversion
[Icons]
Name: "{group}\NavixX Cloud Preview"; Filename: "{app}\NavixDesktop.exe"
Name: "{autodesktop}\NavixX Cloud Preview"; Filename: "{app}\NavixDesktop.exe"
Name: "{group}\Desinstalar NavixX Cloud Preview"; Filename: "{uninstallexe}"
[Run]
Filename: "{app}\NavixDesktop.exe"; Description: "Abrir NavixX Cloud Preview agora"; Flags: nowait postinstall skipifsilent unchecked

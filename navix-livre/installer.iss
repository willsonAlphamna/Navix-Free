#define MyAppName "Navix Livre"
#ifndef MyAppVersion
  #define MyAppVersion "0.3.1"
#endif
#define MyAppPublisher "Comunidade Navix Livre"

[Setup]
AppId=NavixLivre.LocalMCP
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={localappdata}\Programs\NavixLivre
DefaultGroupName=Navix Livre
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
OutputDir=dist-install
OutputBaseFilename=NavixLivre-Setup-Windows
Compression=lzma
SolidCompression=yes
WizardStyle=modern
SetupIconFile=assets\navix.ico
WizardImageFile=assets\wizard.bmp
WizardSmallImageFile=assets\wizard_small.bmp
UninstallDisplayIcon={app}\NavixLivre.exe
CloseApplications=yes
RestartApplications=no
AlwaysRestart=no
DisableWelcomePage=no
SetupLogging=yes
#ifdef ReleaseSigning
SignTool=navix
SignedUninstaller=yes
#else
SignedUninstaller=no
#endif

[Languages]
Name: "brazilianportuguese"; MessagesFile: "compiler:Languages\BrazilianPortuguese.isl"

[Tasks]
Name: "desktopicon"; Description: "Criar atalho na Área de Trabalho"; GroupDescription: "Atalhos"; Flags: checkedonce

[Files]
Source: "dist\NavixLivre.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "dist\NavixBridge.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "README.md"; DestDir: "{app}"; Flags: ignoreversion
Source: "COMO_INSTALAR.md"; DestDir: "{app}"; Flags: ignoreversion
Source: "LICENSE"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\Navix Livre"; Filename: "{app}\NavixLivre.exe"
Name: "{group}\Conexão MCP local"; Filename: "{app}\NavixBridge.exe"
Name: "{group}\Desinstalar Navix Livre"; Filename: "{uninstallexe}"
Name: "{autodesktop}\Navix Livre"; Filename: "{app}\NavixLivre.exe"; Tasks: desktopicon

[Run]
Filename: "{app}\NavixLivre.exe"; Description: "Abrir Navix Livre"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
Type: files; Name: "{localappdata}\NavixLivre\bridge.token"
Type: dirifempty; Name: "{localappdata}\NavixLivre"

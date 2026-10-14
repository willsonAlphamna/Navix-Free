#define MyAppName "Navix Livre"
#define MyAppVersion "0.2.0"
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
UninstallDisplayIcon={app}\NavixLivre.exe
CloseApplications=yes
RestartApplications=no
AlwaysRestart=no
DisableWelcomePage=no
SetupLogging=yes

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

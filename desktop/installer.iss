#define AppVersion "0.2.10"
[Setup]
AppId={{CAF0DA60-C25D-4A21-9080-78D57BEA8F0B}
AppName=NavixX Desktop
AppVersion={#AppVersion}
AppPublisher=ALFAMNA
AppCopyright=ALFAMNA © 2026 — Todos os direitos reservados.
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
WizardSmallImageBackColor=none
DisableWelcomePage=no
SetupIconFile=assets\navix.ico
UninstallDisplayIcon={app}\NavixDesktop.exe
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
CloseApplications=yes
[Languages]
Name: "brazilianportuguese"; MessagesFile: "compiler:Languages\BrazilianPortuguese.isl"
Name: "english"; MessagesFile: "compiler:Default.isl"
Name: "spanish"; MessagesFile: "compiler:Languages\Spanish.isl"
[Files]
Source: "dist\NavixDesktop\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
[Icons]
Name: "{group}\NavixX Desktop"; Filename: "{app}\NavixDesktop.exe"; Parameters: "--lang {language}"
Name: "{autodesktop}\NavixX Desktop"; Filename: "{app}\NavixDesktop.exe"; Parameters: "--lang {language}"
Name: "{group}\Desinstalar NavixX Desktop"; Filename: "{uninstallexe}"
[Run]
Filename: "{app}\NavixDesktop.exe"; Parameters: "--lang {language}"; Description: "Abrir NavixX Desktop agora"; Flags: nowait postinstall skipifsilent

[CustomMessages]
brazilianportuguese.WipeNavixData=Também deseja apagar PERMANENTEMENTE as configurações, senhas criptografadas, perfil de navegação e logs locais do NavixX? Se responder Não, eles serão preservados para uma futura reinstalação.%n%nEsta ação não pode ser desfeita.
english.WipeNavixData=Also PERMANENTLY erase NavixX settings, encrypted credentials, browser profile and local logs? Choose No to preserve them for a future reinstall.%n%nThis cannot be undone.
spanish.WipeNavixData=¿Deseas borrar PERMANENTEMENTE los ajustes, las credenciales cifradas, el perfil del navegador y los registros locales de NavixX? Elige No para conservarlos.%n%nEsta acción no se puede deshacer.

[Code]
var
  WipeNavixData: Boolean;

function InitializeUninstall: Boolean;
begin
  WipeNavixData := False;
  if not UninstallSilent then
    WipeNavixData := MsgBox(CustomMessage('WipeNavixData'), mbConfirmation, MB_YESNO) = IDYES;
  Result := True;
end;

procedure CurUninstallStepChanged(CurUninstallStep: TUninstallStep);
begin
  if (CurUninstallStep = usPostUninstall) and WipeNavixData then
  begin
    if not DelTree(ExpandConstant('{localappdata}\NavixDesktop'), True, True, True) then
      MsgBox('NavixX: alguns dados locais não puderam ser removidos. Verifique a pasta AppData\\Local\\NavixDesktop.', mbInformation, MB_OK);
  end;
end;

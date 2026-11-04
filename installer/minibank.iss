; Скрипт Inno Setup для установщика «Мини-банк»
; Собирается автоматически в GitHub Actions (.github/workflows/release.yml)
; Вручную: ISCC.exe installer\minibank.iss

#ifndef AppVersion
  #define AppVersion "1.0.0"
#endif

[Setup]
AppId={{6F1C2B4E-8A3D-4E2B-9C71-5B0D3A9E7F21}
AppName=Мини-банк
AppVersion={#AppVersion}
AppPublisher=Студенческий проект
DefaultDirName={autopf}\MiniBank
DefaultGroupName=Мини-банк
OutputDir=..\dist
OutputBaseFilename=MiniBank-Setup-{#AppVersion}
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
PrivilegesRequiredOverridesAllowed=dialog
UninstallDisplayIcon={app}\MiniBank.exe

[Languages]
Name: "russian"; MessagesFile: "compiler:Languages\Russian.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"

[Files]
Source: "..\dist\MiniBank.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\minibank\schema.sql"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\Мини-банк"; Filename: "{app}\MiniBank.exe"
Name: "{group}\Удалить Мини-банк"; Filename: "{uninstallexe}"
Name: "{autodesktop}\Мини-банк"; Filename: "{app}\MiniBank.exe"; Tasks: desktopicon

[Run]
Filename: "{app}\MiniBank.exe"; Description: "{cm:LaunchProgram,Мини-банк}"; Flags: nowait postinstall skipifsilent

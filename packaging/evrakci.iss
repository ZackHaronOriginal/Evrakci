; Evrakçı Windows installer (Inno Setup 6). Built by .github/workflows/windows-installer.yml.
; The folder build keeps every library (including Qt) as a separate, replaceable file (LGPL).

#ifndef AppVersion
  #define AppVersion "0.0.1"
#endif

[Setup]
AppId={{C94201F2-D1CF-4A42-A480-5724501C6B46}
AppName=Evrakçı
AppVersion={#AppVersion}
AppPublisher=Evrakçı
AppPublisherURL=https://github.com/ZackHaronOriginal/Evrakci
DefaultDirName={autopf}\Evrakçı
DefaultGroupName=Evrakçı
LicenseFile=licenses\AGPL-3.0.txt
OutputDir=..\dist
OutputBaseFilename=Evrakci-Kurulum-{#AppVersion}
Compression=lzma2/max
SolidCompression=yes
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
PrivilegesRequiredOverridesAllowed=dialog
ChangesEnvironment=yes
UninstallDisplayIcon={app}\evrakci-arayuz.exe
SourceDir=..\build\evrakci

[Languages]
Name: "turkish"; MessagesFile: "compiler:Languages\Turkish.isl"

[Tasks]
Name: "desktopicon"; Description: "Masaüstüne kısayol oluştur"; GroupDescription: "Kısayollar:"
Name: "addtopath"; Description: "evrakci komutunu komut satırına ekle (PATH)"; GroupDescription: "Komut satırı:"; Flags: unchecked

[Files]
Source: "*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\Evrakçı"; Filename: "{app}\evrakci-arayuz.exe"
Name: "{group}\Lisanslar"; Filename: "{app}\licenses\NOTICE.txt"
Name: "{group}\Evrakçı'yı kaldır"; Filename: "{uninstallexe}"
Name: "{autodesktop}\Evrakçı"; Filename: "{app}\evrakci-arayuz.exe"; Tasks: desktopicon

[Registry]
Root: HKCU; Subkey: "Environment"; ValueType: expandsz; ValueName: "Path"; ValueData: "{olddata};{app}"; Tasks: addtopath; Check: NeedsAddPath(ExpandConstant('{app}'))

[Run]
Filename: "{app}\evrakci-arayuz.exe"; Description: "Evrakçı'yı başlat"; Flags: nowait postinstall skipifsilent

[Code]
function NeedsAddPath(Folder: string): Boolean;
var
  Current: string;
begin
  if not RegQueryStringValue(HKEY_CURRENT_USER, 'Environment', 'Path', Current) then
  begin
    Result := True;
    exit;
  end;
  Result := Pos(';' + Uppercase(Folder) + ';', ';' + Uppercase(Current) + ';') = 0;
end;

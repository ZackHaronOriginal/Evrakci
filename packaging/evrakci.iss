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
; No Turkish letters in the folder name. A per-user install path still holds the user's
; name, so the app copies Tesseract data to an ASCII folder when it must (ascii_safe_dir).
DefaultDirName={autopf}\Evrakci
DefaultGroupName=Evrakçı
LicenseFile=licenses\AGPL-3.0.txt
; {#SourcePath} is this script's folder (packaging\); output goes to the repo's dist\.
OutputDir={#SourcePath}..\dist
OutputBaseFilename=Evrakci-Kurulum-{#AppVersion}
Compression=lzma2/max
SolidCompression=yes
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
; Per-user install by default (no admin prompt); the dialog allows installing for all users.
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog
ChangesEnvironment=yes
UninstallDisplayIcon={app}\evrakci-arayuz.exe
SourceDir=..\build\evrakci

[Languages]
Name: "turkish"; MessagesFile: "compiler:Languages\Turkish.isl"

[Tasks]
Name: "desktopicon"; Description: "Masaüstüne kısayol oluştur"; GroupDescription: "Kısayollar:"
Name: "addtopath"; Description: "evrakci komutunu komut satırına ekle (PATH)"; GroupDescription: "Komut satırı:"; Flags: unchecked

[InstallDelete]
; Upgrades start from clean program folders so files from an older build never linger.
Type: filesandordirs; Name: "{app}\lib"
Type: filesandordirs; Name: "{app}\tesseract"
Type: filesandordirs; Name: "{app}\tessdata_best"
Type: filesandordirs; Name: "{app}\licenses"

[Files]
Source: "*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\Evrakçı"; Filename: "{app}\evrakci-arayuz.exe"
Name: "{group}\Lisanslar"; Filename: "{app}\licenses\NOTICE.txt"
Name: "{group}\Evrakçı'yı kaldır"; Filename: "{uninstallexe}"
Name: "{autodesktop}\Evrakçı"; Filename: "{app}\evrakci-arayuz.exe"; Tasks: desktopicon

[Registry]
; HKA = HKCU for a per-user install, HKLM for an all-users install.
Root: HKA; Subkey: "{code:EnvironmentKey}"; ValueType: expandsz; ValueName: "Path"; ValueData: "{olddata};{app}"; Tasks: addtopath; Check: NeedsAddPath(ExpandConstant('{app}'))

[UninstallDelete]
; Only the ASCII-path cache of OCR data (see ascii_safe_dir); job data in the user folder is kept.
Type: filesandordirs; Name: "{commonappdata}\Evrakci"

[Run]
Filename: "{app}\evrakci-arayuz.exe"; Description: "Evrakçı'yı başlat"; Flags: nowait postinstall skipifsilent

[Code]
function EnvironmentKey(Param: string): string;
begin
  if IsAdminInstallMode then
    Result := 'SYSTEM\CurrentControlSet\Control\Session Manager\Environment'
  else
    Result := 'Environment';
end;

function RootKey: Integer;
begin
  if IsAdminInstallMode then
    Result := HKEY_LOCAL_MACHINE
  else
    Result := HKEY_CURRENT_USER;
end;

function NeedsAddPath(Folder: string): Boolean;
var
  Current: string;
begin
  if not RegQueryStringValue(RootKey, EnvironmentKey(''), 'Path', Current) then
  begin
    Result := True;
    exit;
  end;
  Result := Pos(';' + Uppercase(Folder) + ';', ';' + Uppercase(Current) + ';') = 0;
end;

procedure CurUninstallStepChanged(CurUninstallStep: TUninstallStep);
var
  Current, Folder: string;
  Position: Integer;
begin
  if CurUninstallStep <> usPostUninstall then
    exit;
  if not RegQueryStringValue(RootKey, EnvironmentKey(''), 'Path', Current) then
    exit;
  Current := Current + ';';
  Folder := ';' + ExpandConstant('{app}') + ';';
  Position := Pos(Uppercase(Folder), Uppercase(Current));
  if Position > 0 then
  begin
    Delete(Current, Position, Length(Folder) - 1);
    Delete(Current, Length(Current), 1);
    RegWriteExpandStringValue(RootKey, EnvironmentKey(''), 'Path', Current);
  end;
end;

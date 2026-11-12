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
Type: filesandordirs; Name: "{app}\share"
Type: filesandordirs; Name: "{app}\docs"
Type: files; Name: "{app}\*.dll"

[Files]
Source: "*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\Evrakçı"; Filename: "{app}\evrakci-arayuz.exe"
Name: "{group}\Lisanslar"; Filename: "{app}\licenses\NOTICE.txt"
Name: "{group}\Evrakçı'yı kaldır"; Filename: "{uninstallexe}"
Name: "{autodesktop}\Evrakçı"; Filename: "{app}\evrakci-arayuz.exe"; Tasks: desktopicon

[UninstallDelete]
; Only this user's cache of OCR data and temp folders (see ascii_copy_root). Job data in
; {localappdata}\Evrakci is kept; the ProgramData fallback folder is removed in [Code].
Type: filesandordirs; Name: "{localappdata}\Evrakci\ascii"

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

function TrimSeparators(Value: string): string;
begin
  while (Length(Value) > 0) and (Value[1] = ';') do
    Delete(Value, 1, 1);
  while (Length(Value) > 0) and (Value[Length(Value)] = ';') do
    Delete(Value, Length(Value), 1);
  Result := Value;
end;

procedure AddToPath;
var
  Current, Folder: string;
begin
  Folder := ExpandConstant('{app}');
  if not RegQueryStringValue(RootKey, EnvironmentKey(''), 'Path', Current) then
    Current := '';
  if Pos(';' + Uppercase(Folder) + ';', ';' + Uppercase(Current) + ';') > 0 then
    exit;
  Current := TrimSeparators(Current);
  if Current <> '' then
    Current := Current + ';';
  RegWriteExpandStringValue(RootKey, EnvironmentKey(''), 'Path', Current + Folder);
end;

procedure CurStepChanged(CurStep: TSetupStep);
begin
  if (CurStep = ssPostInstall) and WizardIsTaskSelected('addtopath') then
    AddToPath;
end;

procedure RemoveFromPath;
var
  Current, Folder: string;
  Position: Integer;
begin
  if not RegQueryStringValue(RootKey, EnvironmentKey(''), 'Path', Current) then
    exit;
  // Separators on both ends, so the entry is found first, last or alone in the list.
  Current := ';' + Current + ';';
  Folder := ';' + ExpandConstant('{app}') + ';';
  Position := Pos(Uppercase(Folder), Uppercase(Current));
  if Position > 0 then
  begin
    Delete(Current, Position, Length(Folder) - 1);
    RegWriteExpandStringValue(RootKey, EnvironmentKey(''), 'Path', TrimSeparators(Current));
  end;
end;

procedure RemoveSharedCache;
var
  RecordFile, Name: string;
  Lines: TArrayOfString;
begin
  // The ProgramData fallback folder has a random name kept in this user's profile.
  RecordFile := ExpandConstant('{localappdata}\Evrakci\ascii-klasoru.txt');
  if LoadStringsFromFile(RecordFile, Lines) and (GetArrayLength(Lines) > 0) then
  begin
    Name := Trim(Lines[0]);
    if (Length(Name) = 34) and (Copy(Name, 1, 2) = 'u-') then
      DelTree(ExpandConstant('{commonappdata}\Evrakci\') + Name, True, True, True);
  end;
  DeleteFile(RecordFile);
end;

procedure CurUninstallStepChanged(CurUninstallStep: TUninstallStep);
begin
  if CurUninstallStep <> usPostUninstall then
    exit;
  RemoveFromPath;
  RemoveSharedCache;
end;

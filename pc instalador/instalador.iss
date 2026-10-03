; Instalador de DataExpert IA (Inno Setup 6). Se compila con construir_instalador.bat despues de PyInstaller.
#define Nombre "DataExpert IA"
#define Version "1.2.4"

[Setup]
AppId={{B4E2C7A9-3D51-4E8F-9A16-5F0D2C8E7B34}
AppName={#Nombre}
AppVersion={#Version}
AppPublisher={#Nombre}
; Por defecto va al disco con mas espacio libre (vea CarpetaPorDefecto); la persona puede cambiarlo en la pantalla de instalacion.
DefaultDirName={code:CarpetaPorDefecto}
DisableDirPage=no
DisableProgramGroupPage=yes
UsePreviousAppDir=yes
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
; Los informes, resultados y graficos crecen con el uso: se avisa de que hace falta espacio para ellos.
ExtraDiskSpaceRequired=536870912
OutputDir=salida
OutputBaseFilename=Instalar_DataExpert_IA
SetupIconFile=recursos\icono.ico
WizardSmallImageFile=recursos\logo_instalador.bmp
UninstallDisplayIcon={app}\DataExpertIA.exe
UninstallDisplayName={#Nombre}
Compression=lzma2/fast
SolidCompression=yes
WizardStyle=modern

[Languages]
Name: "es"; MessagesFile: "compiler:Languages\Spanish.isl"

[Messages]
WizardSelectDir=¿En qué disco quieres instalar DataExpert IA?
SelectDirDesc=Elige el disco y la carpeta donde se instalará.
SelectDirLabel3=DataExpert IA se instalará en la carpeta de abajo. Ahí mismo se guardarán tus informes, resultados e historial.
SelectDirBrowseLabel=Para instalar en otro disco (por ejemplo D: o E:) pulsa Examinar y elígelo. Después pulsa Siguiente.

[Tasks]
Name: "iconoescritorio"; Description: "Crear un icono de DataExpert IA en el escritorio"; GroupDescription: "Accesos directos:"

[Files]
Source: "_compilacion\dist\DataExpertIA\*"; DestDir: "{app}"; Flags: recursesubdirs createallsubdirs ignoreversion

[Dirs]
; Carpeta de los datos del usuario: todos los usuarios del PC pueden escribir en ella y el desinstalador no la borra sin preguntar.
Name: "{app}\datos_usuario"; Permissions: users-modify; Flags: uninsneveruninstall

[Icons]
Name: "{autoprograms}\DataExpert IA"; Filename: "{app}\DataExpertIA.exe"
Name: "{autoprograms}\Mis datos de DataExpert IA"; Filename: "{app}\datos_usuario"
Name: "{autodesktop}\DataExpert IA"; Filename: "{app}\DataExpertIA.exe"; Tasks: iconoescritorio

[Run]
Filename: "{app}\DataExpertIA.exe"; Description: "Abrir DataExpert IA ahora"; Flags: nowait postinstall skipifsilent

[Code]
function GetDriveType(lpRootPathName: String): Cardinal; external 'GetDriveTypeW@kernel32.dll stdcall';

{ Sugiere el disco fijo con mas espacio libre; si no hay ninguno con al menos 4 GB, usa la carpeta de programas del usuario. }
function CarpetaPorDefecto(Param: String): String;
var
  I: Integer;
  Raiz, Mejor: String;
  Libre, Total, MejorLibre: Cardinal;
begin
  Result := ExpandConstant('{autopf}\DataExpert IA');
  Mejor := '';
  MejorLibre := 0;
  for I := 68 to 90 do
  begin
    Raiz := Chr(I) + ':\';
    if GetDriveType(Raiz) = 3 then
      if GetSpaceOnDisk(Raiz, True, Libre, Total) then
        if (Libre >= 4096) and (Libre > MejorLibre) then
        begin
          MejorLibre := Libre;
          Mejor := Raiz + 'DataExpert IA';
        end;
  end;
  if Mejor <> '' then
    Result := Mejor;
end;

procedure CurUninstallStepChanged(CurUninstallStep: TUninstallStep);
var
  Datos: String;
begin
  if CurUninstallStep = usPostUninstall then
  begin
    Datos := ExpandConstant('{app}\datos_usuario');
    if DirExists(Datos) and (not UninstallSilent) then
      if MsgBox('¿Quieres borrar también tus informes, resultados e historial guardados?' + #13#10 + #13#10 +
                'Si respondes No, se conservan en:' + #13#10 + Datos, mbConfirmation, MB_YESNO or MB_DEFBUTTON2) = IDYES then
        DelTree(Datos, True, True, True);
  end;
end;

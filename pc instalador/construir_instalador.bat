@echo off
chcp 65001 >nul
rem Construye el instalador de DataExpert IA: 1) DataExpertIA.exe con PyInstaller, 2) Instalar_DataExpert_IA.exe con Inno Setup.
rem Solo hace falta ejecutarlo al preparar una nueva version; las personas que usan la aplicacion solo abren Instalar_DataExpert_IA.exe.
rem Usa un entorno propio (_compilacion\entorno) con las versiones de requirements.txt: no toca el .venv del proyecto ni otros paquetes.
cd /d "%~dp0"
if not exist "_compilacion\entorno\Scripts\python.exe" (
    python -m venv _compilacion\entorno
    if errorlevel 1 goto error
)
_compilacion\entorno\Scripts\python.exe -m pip install --quiet --disable-pip-version-check -r ..\requirements.txt pyinstaller
if errorlevel 1 goto error
_compilacion\entorno\Scripts\python.exe -m PyInstaller --noconfirm --distpath _compilacion\dist --workpath _compilacion\trabajo DataExpertIA.spec
if errorlevel 1 goto error
"%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe" instalador.iss
if errorlevel 1 goto error
echo.
echo Listo: salida\Instalar_DataExpert_IA.exe
if /i not "%~1"=="sinpausa" pause
exit /b 0
:error
echo.
echo Algo fallo. Revisa los mensajes de arriba.
if /i not "%~1"=="sinpausa" pause
exit /b 1

@echo off
rem ====================================================================
rem  Instala o verifica el software local del curso "ML e IA: de desarrollo
rem  a produccion" en Windows, desde el Simbolo del sistema (CMD).
rem
rem  ESTADO: la logica se probo con stubs bajo Wine (Linux). NO se ha probado
rem  en Windows real ni con winget real. Probar en un equipo limpio y confirmar
rem  los identificadores con: winget search nombre
rem
rem  Que hace, y solo esto:
rem    - Usa winget para instalar Git, Visual Studio Code, Miniconda,
rem      DB Browser for SQLite y Google Cloud CLI.
rem    - Instala las extensiones de VS Code del curso.
rem    - Con la opcion verificar no instala nada: comprueba y escribe un informe.
rem  No descarga nada que no sea de winget. No toca el registro ni pide
rem  contrasenas, tokens o claves.
rem
rem  Docker y Kubernetes NO se instalan: en el curso se usan en Codespaces.
rem  Docker Desktop local es opcional: opcion dockerdesktop.
rem
rem  Uso:
rem    instalar_entorno.cmd                    instala lo que falte
rem    instalar_entorno.cmd verificar          solo comprueba
rem    instalar_entorno.cmd sinconfirmacion    no pregunta antes de instalar
rem    instalar_entorno.cmd sinextensiones     no instala extensiones de VS Code
rem    instalar_entorno.cmd dockerdesktop      incluye Docker Desktop opcional
rem ====================================================================
setlocal EnableExtensions EnableDelayedExpansion

set "MODO=instalar"
set "CONFIRMAR=1"
set "EXTENSIONES=1"
set "DOCKER=0"
for %%A in (%*) do (
  if /i "%%~A"=="verificar"       set "MODO=verificar"
  if /i "%%~A"=="/verificar"      set "MODO=verificar"
  if /i "%%~A"=="sinconfirmacion" set "CONFIRMAR=0"
  if /i "%%~A"=="sinextensiones"  set "EXTENSIONES=0"
  if /i "%%~A"=="dockerdesktop"   set "DOCKER=1"
)

set "INFORME=%CD%\verificacion-entorno.txt"

echo.
echo === Entorno del curso ML e IA, Windows, CMD ===
if "%MODO%"=="verificar" (
  echo Modo verificacion: no se instala nada.
) else (
  echo Modo instalacion. Lee lo que hace este script antes de continuar.
)
echo.

rem ---------------- tabla de herramientas
rem  NOMBRE, ID de winget, CMD (comando), ALT (rutas alternativas), OBL (1 obligatoria)
set "NOMBRE_1=Git"
set "ID_1=Git.Git"
set "CMD_1=git"
set "ALT_1=%ProgramFiles%\Git\cmd\git.exe"
set "ALT2_1="
set "ALT3_1="
set "OBL_1=1"

set "NOMBRE_2=Visual Studio Code"
set "ID_2=Microsoft.VisualStudioCode"
set "CMD_2=code"
set "ALT_2=%LOCALAPPDATA%\Programs\Microsoft VS Code\bin\code.cmd"
set "ALT2_2=%ProgramFiles%\Microsoft VS Code\bin\code.cmd"
set "ALT3_2="
set "OBL_2=1"

set "NOMBRE_3=Miniconda"
set "ID_3=Anaconda.Miniconda3"
set "CMD_3=conda"
set "ALT_3=%USERPROFILE%\miniconda3\Scripts\conda.exe"
set "ALT2_3=%LOCALAPPDATA%\miniconda3\Scripts\conda.exe"
set "ALT3_3=%ProgramData%\miniconda3\Scripts\conda.exe"
set "OBL_3=1"

set "NOMBRE_4=DB Browser for SQLite"
set "ID_4=DBBrowserForSQLite.DBBrowserForSQLite"
set "CMD_4=db4s_no_esta_en_el_path"
set "ALT_4=%ProgramFiles%\DB Browser for SQLite\DB Browser for SQLite.exe"
set "ALT2_4="
set "ALT3_4="
set "OBL_4=1"

set "NOMBRE_5=Google Cloud CLI"
set "ID_5=Google.CloudSDK"
set "CMD_5=gcloud"
set "ALT_5=%LOCALAPPDATA%\Google\Cloud SDK\google-cloud-sdk\bin\gcloud.cmd"
set "ALT2_5="
set "ALT3_5="
set "OBL_5=1"

set "TOTAL=5"
if "%DOCKER%"=="1" (
  set "NOMBRE_6=Docker Desktop opcional"
  set "ID_6=Docker.DockerDesktop"
  set "CMD_6=docker"
  set "ALT_6=%ProgramFiles%\Docker\Docker\resources\bin\docker.exe"
  set "ALT2_6="
  set "ALT3_6="
  set "OBL_6=0"
  set "TOTAL=6"
)

rem ---------------- instalacion
if "%MODO%"=="instalar" (
  where winget >nul 2>&1
  if errorlevel 1 (
    echo No se encontro winget. Instala "Instalador de aplicacion" desde Microsoft Store, o sigue la guia manual con descargas.
    exit /b 1
  )
  for /l %%Z in (1,1,%TOTAL%) do (
    call set "NOMBRE=%%NOMBRE_%%Z%%"
    call set "ID=%%ID_%%Z%%"
    call set "CMD=%%CMD_%%Z%%"
    call set "ALT=%%ALT_%%Z%%"
    call set "ALT2=%%ALT2_%%Z%%"
    call set "ALT3=%%ALT3_%%Z%%"
    set "ENC="
    where !CMD! >nul 2>&1
    if not errorlevel 1 set "ENC=1"
    if not defined ENC if defined ALT  if exist "!ALT!"  set "ENC=1"
    if not defined ENC if defined ALT2 if exist "!ALT2!" set "ENC=1"
    if not defined ENC if defined ALT3 if exist "!ALT3!" set "ENC=1"
    if defined ENC (
      echo [ya instalado] !NOMBRE!
    ) else (
      set "HACER=1"
      if "!CONFIRMAR!"=="1" (
        set "RESP="
        set /p "RESP=Instalar !NOMBRE!? (s/N): "
        if /i not "!RESP!"=="s" if /i not "!RESP!"=="y" set "HACER=0"
      )
      if "!HACER!"=="1" (
        echo [instalando] !NOMBRE! - !ID!
        winget install --id !ID! -e --accept-source-agreements --accept-package-agreements
        if errorlevel 1 echo [fallo] !NOMBRE!: winget devolvio un error. Prueba la instalacion manual de la guia.
      ) else (
        echo [omitido] !NOMBRE!
      )
    )
  )

  if "!EXTENSIONES!"=="1" (
    set "CODEEXE="
    where code >nul 2>&1
    if not errorlevel 1 set "CODEEXE=code"
    if not defined CODEEXE if exist "%LOCALAPPDATA%\Programs\Microsoft VS Code\bin\code.cmd" set "CODEEXE=%LOCALAPPDATA%\Programs\Microsoft VS Code\bin\code.cmd"
    if not defined CODEEXE if exist "%ProgramFiles%\Microsoft VS Code\bin\code.cmd" set "CODEEXE=%ProgramFiles%\Microsoft VS Code\bin\code.cmd"
    if defined CODEEXE (
      for %%E in (ms-python.python ms-python.vscode-pylance ms-toolsai.jupyter ms-azuretools.vscode-containers ms-kubernetes-tools.vscode-kubernetes-tools ms-vscode-remote.remote-containers GitHub.codespaces) do (
        echo [extension] %%E
        call "!CODEEXE!" --install-extension %%E --force >nul 2>&1
      )
    ) else (
      echo VS Code no esta disponible todavia: cierra y abre la terminal y vuelve a ejecutar para instalar las extensiones.
    )
  )
  echo.
)

rem ---------------- verificacion e informe
set "WINVER="
for /f "delims=" %%V in ('ver') do if not defined WINVER set "WINVER=%%V"

>"%INFORME%" echo Informe de verificacion del entorno - curso ML e IA
>>"%INFORME%" echo Fecha: %DATE% %TIME%
>>"%INFORME%" echo Windows: !WINVER!
>>"%INFORME%" echo Interprete: CMD
>>"%INFORME%" echo No incluye credenciales ni datos personales.
>>"%INFORME%" echo.

set "FALTAN=0"
for /l %%Z in (1,1,%TOTAL%) do (
  call set "NOMBRE=%%NOMBRE_%%Z%%"
  call set "ID=%%ID_%%Z%%"
  call set "CMD=%%CMD_%%Z%%"
  call set "ALT=%%ALT_%%Z%%"
  call set "ALT2=%%ALT2_%%Z%%"
  call set "ALT3=%%ALT3_%%Z%%"
  call set "OBL=%%OBL_%%Z%%"
  set "ENC="
  set "VER="
  where !CMD! >nul 2>&1
  if not errorlevel 1 set "ENC=1"
  if defined ENC if /i not "!CMD!"=="db4s_no_esta_en_el_path" for /f "delims=" %%V in ('!CMD! --version 2^>^&1') do if not defined VER set "VER=%%V"
  if not defined ENC if defined ALT  if exist "!ALT!"  set "ENC=2"
  if not defined ENC if defined ALT2 if exist "!ALT2!" set "ENC=2"
  if not defined ENC if defined ALT3 if exist "!ALT3!" set "ENC=2"
  if "!ENC!"=="1" (
    echo [OK]    !NOMBRE!  !VER!
    >>"%INFORME%" echo [OK]    !NOMBRE!  !VER!
  ) else if "!ENC!"=="2" (
    echo [OK]    !NOMBRE!  instalado, pero fuera del PATH. Abre una terminal nueva.
    >>"%INFORME%" echo [OK]    !NOMBRE!  instalado, pero fuera del PATH. Abre una terminal nueva.
  ) else (
    if "!OBL!"=="1" set /a FALTAN+=1
    echo [FALTA] !NOMBRE!  id winget: !ID!
    >>"%INFORME%" echo [FALTA] !NOMBRE!  id winget: !ID!
  )
)

echo.
>>"%INFORME%" echo.
set "DOCKERLOCAL="
where docker >nul 2>&1
if not errorlevel 1 set "DOCKERLOCAL=1"
if defined DOCKERLOCAL (
  echo [INFO]  Docker local encontrado, es opcional. En el curso se usa Docker dentro de Codespaces.
  >>"%INFORME%" echo [INFO]  Docker local encontrado, es opcional. En el curso se usa Docker dentro de Codespaces.
) else (
  echo [INFO]  Docker local no instalado: correcto. En el curso se usa Docker dentro de Codespaces.
  >>"%INFORME%" echo [INFO]  Docker local no instalado: correcto. En el curso se usa Docker dentro de Codespaces.
)

echo.
>>"%INFORME%" echo.
if "!FALTAN!"=="0" (
  echo Resultado: todo lo obligatorio esta instalado.
  >>"%INFORME%" echo Resultado: todo lo obligatorio esta instalado.
) else (
  echo Resultado: faltan !FALTAN! herramientas obligatorias. Si acabas de instalar, cierra y abre la terminal y repite con: instalar_entorno.cmd verificar
  >>"%INFORME%" echo Resultado: faltan !FALTAN! herramientas obligatorias. Si acabas de instalar, cierra y abre la terminal y repite con: instalar_entorno.cmd verificar
)
echo.
echo Informe guardado en: !INFORME!
echo Pega su contenido en el diagnostico de S0 si algo falla.
endlocal
exit /b 0

<#
.SYNOPSIS
  Instala o verifica el software local del curso "ML e IA: de desarrollo a produccion" en Windows.

.DESCRIPTION
  ESTADO: la sintaxis se valido con el analizador de PowerShell 7 y la logica se probo en Linux con un winget
  falso (deteccion, instalacion, confirmacion e informe). NO se ha probado en Windows real, ni en Windows
  PowerShell 5.1, ni con winget real. Probarlo en un equipo limpio antes de entregarlo a los alumnos y
  confirmar los identificadores de paquete con: winget search <nombre>

  Que hace (y solo esto):
    - Usa winget (el administrador de paquetes de Windows) para instalar: Git, Visual Studio Code, Miniconda,
      DB Browser for SQLite y Google Cloud CLI.
    - Instala las extensiones de VS Code del curso (si VS Code ya esta disponible).
    - Con -Verificar no instala nada: solo comprueba y escribe un informe.
  No descarga nada que no sea de winget. No modifica el registro ni la politica de ejecucion del equipo.
  No pide ni guarda contrasenas, tokens o claves.

  Docker y Kubernetes NO se instalan: en el curso se usan dentro de Codespaces.
  Docker Desktop local es opcional (-ConDockerDesktop).

.PARAMETER Verificar
  Solo comprueba lo instalado y genera el informe. No instala nada.

.PARAMETER ConDockerDesktop
  Instala tambien Docker Desktop (opcional, no es requisito del curso).

.PARAMETER SinConfirmacion
  No pregunta antes de instalar cada programa.

.PARAMETER SinExtensiones
  No instala las extensiones de VS Code.

.EXAMPLE
  powershell -ExecutionPolicy Bypass -File .\instalar_entorno.ps1
  powershell -ExecutionPolicy Bypass -File .\instalar_entorno.ps1 -Verificar
#>
[CmdletBinding()]
param(
    [switch]$Verificar,
    [switch]$ConDockerDesktop,
    [switch]$SinConfirmacion,
    [switch]$SinExtensiones
)

$ErrorActionPreference = 'Continue'
$informe = Join-Path (Get-Location) 'verificacion-entorno.txt'

# ---------------------------------------------------------------- utilidades
function Actualizar-Path {
    # winget deja el PATH actualizado en el sistema, pero no en esta ventana.
    $m = [Environment]::GetEnvironmentVariable('Path', 'Machine')
    $u = [Environment]::GetEnvironmentVariable('Path', 'User')
    $env:Path = "$m;$u"
}

function Buscar-Comando {
    param([string]$Nombre, [string[]]$RutasAlternativas = @())
    $cmd = Get-Command $Nombre -ErrorAction SilentlyContinue
    if ($cmd) { return $cmd.Source }
    foreach ($r in $RutasAlternativas) {
        $ruta = [Environment]::ExpandEnvironmentVariables($r)
        if (Test-Path $ruta) { return $ruta }
    }
    return $null
}

function Obtener-Version {
    param([string]$Ejecutable, [string[]]$Argumentos)
    try {
        $salida = & $Ejecutable @Argumentos 2>&1 | Select-Object -First 1
        return ([string]$salida).Trim()
    } catch {
        return 'no se pudo leer la version'
    }
}

# ---------------------------------------------------------------- herramientas
# Id = identificador de winget. Comprobar con: winget search <nombre>
$herramientas = @(
    @{ Nombre = 'Git';                    Id = 'Git.Git';                                  Comando = 'git';
       Alternativas = @('%ProgramFiles%\Git\cmd\git.exe');
       Version = @('--version'); Obligatoria = $true },
    @{ Nombre = 'Visual Studio Code';     Id = 'Microsoft.VisualStudioCode';               Comando = 'code';
       Alternativas = @('%LOCALAPPDATA%\Programs\Microsoft VS Code\bin\code.cmd', '%ProgramFiles%\Microsoft VS Code\bin\code.cmd');
       Version = @('--version'); Obligatoria = $true },
    @{ Nombre = 'Miniconda';              Id = 'Anaconda.Miniconda3';                      Comando = 'conda';
       Alternativas = @('%USERPROFILE%\miniconda3\Scripts\conda.exe', '%LOCALAPPDATA%\miniconda3\Scripts\conda.exe', '%ProgramData%\miniconda3\Scripts\conda.exe');
       Version = @('--version'); Obligatoria = $true },
    @{ Nombre = 'DB Browser for SQLite';  Id = 'DBBrowserForSQLite.DBBrowserForSQLite';   Comando = 'DB4S-no-esta-en-PATH';
       Alternativas = @('%ProgramFiles%\DB Browser for SQLite\DB Browser for SQLite.exe');
       Version = $null; Obligatoria = $true },
    @{ Nombre = 'Google Cloud CLI';       Id = 'Google.CloudSDK';                          Comando = 'gcloud';
       Alternativas = @('%LOCALAPPDATA%\Google\Cloud SDK\google-cloud-sdk\bin\gcloud.cmd', '%ProgramFiles(x86)%\Google\Cloud SDK\google-cloud-sdk\bin\gcloud.cmd');
       Version = @('--version'); Obligatoria = $true }
)
if ($ConDockerDesktop) {
    $herramientas += @{ Nombre = 'Docker Desktop (opcional)'; Id = 'Docker.DockerDesktop'; Comando = 'docker';
       Alternativas = @('%ProgramFiles%\Docker\Docker\resources\bin\docker.exe');
       Version = @('--version'); Obligatoria = $false }
}

# Extensiones de VS Code del curso. Comprobar con: code --list-extensions
$extensiones = @(
    'ms-python.python',
    'ms-python.vscode-pylance',
    'ms-toolsai.jupyter',
    'ms-azuretools.vscode-containers',
    'ms-kubernetes-tools.vscode-kubernetes-tools',
    'ms-vscode-remote.remote-containers',
    'GitHub.codespaces'
)

# ---------------------------------------------------------------- inicio
Write-Host ''
Write-Host '=== Entorno del curso ML e IA (Windows) ===' -ForegroundColor Cyan
if ($Verificar) { Write-Host 'Modo verificacion: no se instala nada.' -ForegroundColor Yellow }
else { Write-Host 'Modo instalacion. Lee lo que hace este script antes de continuar.' -ForegroundColor Yellow }
Write-Host ''

$winget = Get-Command winget -ErrorAction SilentlyContinue
if (-not $Verificar -and -not $winget) {
    Write-Host 'No se encontro winget. Instala "Instalador de aplicacion" desde Microsoft Store, o sigue la guia manual con descargas.' -ForegroundColor Red
    exit 1
}

# ---------------------------------------------------------------- instalacion
if (-not $Verificar) {
    foreach ($h in $herramientas) {
        $ruta = Buscar-Comando -Nombre $h.Comando -RutasAlternativas $h.Alternativas
        if ($ruta) {
            Write-Host ("[ya instalado] {0}" -f $h.Nombre) -ForegroundColor Green
            continue
        }
        if (-not $SinConfirmacion) {
            $resp = Read-Host ("Instalar {0}? (s/N)" -f $h.Nombre)
            if ($resp -notmatch '^[sSyY]') { Write-Host ("[omitido] {0}" -f $h.Nombre); continue }
        }
        Write-Host ("[instalando] {0} ({1})..." -f $h.Nombre, $h.Id) -ForegroundColor Cyan
        & winget install --id $h.Id -e --accept-source-agreements --accept-package-agreements
        if ($LASTEXITCODE -ne 0) {
            Write-Host ("[fallo] {0}: winget devolvio el codigo {1}. Prueba la instalacion manual de la guia." -f $h.Nombre, $LASTEXITCODE) -ForegroundColor Red
        }
    }
    Actualizar-Path

    if (-not $SinExtensiones) {
        $code = Buscar-Comando -Nombre 'code' -RutasAlternativas @('%LOCALAPPDATA%\Programs\Microsoft VS Code\bin\code.cmd', '%ProgramFiles%\Microsoft VS Code\bin\code.cmd')
        if ($code) {
            foreach ($e in $extensiones) {
                Write-Host ("[extension] {0}" -f $e)
                & $code --install-extension $e --force | Out-Null
            }
        } else {
            Write-Host 'VS Code no esta disponible todavia: cierra y abre la terminal y vuelve a ejecutar el script para instalar las extensiones.' -ForegroundColor Yellow
        }
    }
    Write-Host ''
}

# ---------------------------------------------------------------- verificacion e informe
Actualizar-Path
$lineas = New-Object System.Collections.Generic.List[string]
$lineas.Add('Informe de verificacion del entorno - curso ML e IA')
$lineas.Add(('Fecha: {0}' -f (Get-Date -Format 'yyyy-MM-dd HH:mm')))
$lineas.Add(('Windows: {0}' -f [Environment]::OSVersion.VersionString))
$lineas.Add(('PowerShell: {0}' -f $PSVersionTable.PSVersion))
$lineas.Add('No incluye credenciales ni datos personales.')
$lineas.Add('')

$faltan = 0
foreach ($h in $herramientas) {
    $ruta = Buscar-Comando -Nombre $h.Comando -RutasAlternativas $h.Alternativas
    if ($ruta) {
        $ver = ''
        if ($h.Version) { $ver = Obtener-Version -Ejecutable $ruta -Argumentos $h.Version }
        $lineas.Add(('[OK]    {0}  {1}' -f $h.Nombre, $ver))
    } else {
        if ($h.Obligatoria) { $faltan++ }
        $lineas.Add(('[FALTA] {0}  (id winget: {1})' -f $h.Nombre, $h.Id))
    }
}

# Extensiones de VS Code
$codeRuta = Buscar-Comando -Nombre 'code' -RutasAlternativas @('%LOCALAPPDATA%\Programs\Microsoft VS Code\bin\code.cmd', '%ProgramFiles%\Microsoft VS Code\bin\code.cmd')
if ($codeRuta) {
    $instaladas = @(& $codeRuta --list-extensions 2>$null)
    foreach ($e in $extensiones) {
        if ($instaladas -contains $e) { $lineas.Add(('[OK]    extension {0}' -f $e)) }
        else { $lineas.Add(('[FALTA] extension {0}' -f $e)) }
    }
}

# Docker y Kubernetes: no se exigen en local
$lineas.Add('')
$dockerLocal = Buscar-Comando -Nombre 'docker' -RutasAlternativas @('%ProgramFiles%\Docker\Docker\resources\bin\docker.exe')
if ($dockerLocal) { $lineas.Add('[INFO]  Docker local encontrado (opcional). En el curso se usa Docker dentro de Codespaces.') }
else { $lineas.Add('[INFO]  Docker local no instalado: correcto. En el curso se usa Docker dentro de Codespaces.') }

$lineas.Add('')
if ($faltan -eq 0) { $lineas.Add('Resultado: todo lo obligatorio esta instalado.') }
else { $lineas.Add(('Resultado: faltan {0} herramientas obligatorias. Si acabas de instalar, cierra y abre la terminal y repite con -Verificar.' -f $faltan)) }

$lineas | ForEach-Object {
    if ($_.StartsWith('[OK]')) { Write-Host $_ -ForegroundColor Green }
    elseif ($_.StartsWith('[FALTA]')) { Write-Host $_ -ForegroundColor Red }
    else { Write-Host $_ }
}
$lineas | Set-Content -Path $informe -Encoding UTF8
Write-Host ''
Write-Host ("Informe guardado en: {0}" -f $informe) -ForegroundColor Cyan
Write-Host 'Pega su contenido en el diagnostico de S0 si algo falla.'

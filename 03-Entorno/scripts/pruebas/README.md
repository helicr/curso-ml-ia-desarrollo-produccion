# Pruebas de los scripts de instalación

Validan la **lógica** de `instalar_entorno.ps1` y `instalar_entorno.cmd` en Linux, con programas falsos en lugar de `winget`.

| Script | Qué prueba | Cómo |
|---|---|---|
| `probar_ps1.sh` | Sintaxis (analizador de PowerShell 7) y lógica: detección, instalación, confirmación, extensiones, informe, fallos | PowerShell 7 en Linux y un `winget` falso |
| `probar_cmd.sh` | Lógica: detección, instalación, confirmación, extensiones, informe, fallos, formato del archivo | `cmd.exe` de Wine y ejecutables falsos compilados desde `stubs/` |

## Requisitos (Ubuntu 24.04)
```bash
sudo apt install wine64 gcc-mingw-w64-x86-64-win32
# PowerShell 7: ver https://learn.microsoft.com/powershell/scripting/install/install-ubuntu
```

## Uso
```bash
./probar_ps1.sh
WINEPREFIX=$HOME/.wine-prueba ./probar_cmd.sh
```
Cada uno termina con «Resultado: N correctas, M fallidas» y devuelve un código distinto de cero si algo falla.
Última ejecución (09/11/2026): PowerShell 20 de 20, CMD 26 de 26.

## Qué NO validan
- Un equipo Windows real, Windows PowerShell 5.1 ni el `winget` real (identificadores de paquete, rutas de instalación, avisos de SmartScreen).
- `where.exe` real: Wine trae uno que no funciona, así que `stubs/where.c` lo imita.
- `set /p`: Wine lee toda la entrada en la primera pregunta (Windows lee una línea por pregunta); se prueba con una sola respuesta.
- El operador `&&` de Wine falla, por eso el script CMD no lo usa.

## Qué descubrieron estas pruebas
Dos errores que habrían fallado en clase: en CMD, la variable del bucle `%%I` chocaba con las variables que empiezan por `I` (`ID_3` salía como `3D_3`),
y en PowerShell `-like '[OK]*'` trataba los corchetes como un conjunto de caracteres.

## Pendiente
Probar ambos scripts en Windows 10 y 11 limpios, y confirmar los identificadores de winget.

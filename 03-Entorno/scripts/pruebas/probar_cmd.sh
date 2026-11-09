#!/usr/bin/env bash
# Prueba instalar_entorno.cmd en Linux con Wine y programas falsos (where, winget, git, gcloud).
# Valida la LOGICA del script. No valida el winget real ni todos los detalles de Windows real.
#
# Requisitos (Ubuntu): wine64 y gcc-mingw-w64-x86-64-win32  ->  sudo apt install wine64 gcc-mingw-w64-x86-64-win32
set -u
AQUI="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SRC="$AQUI/../instalar_entorno.cmd"
W=/usr/lib/wine/wine64
CC=x86_64-w64-mingw32-gcc
for h in "$W" "$(command -v $CC)"; do [ -x "$h" ] || { echo "Falta: $h (ver requisitos al inicio del archivo)"; exit 2; }; done

export WINEPREFIX="${WINEPREFIX:-$HOME/.wine-prueba-curso}" WINEDEBUG=-all WINEDLLOVERRIDES="mscoree,mshtml=d" WINEARCH=win64
T="$(mktemp -d /tmp/prueba-cmd.XXXXXX)"
WT="Z:${T//\//\\}"
mkdir -p "$T/stubs" "$T/run"
cp "$SRC" "$T/instalar_entorno.cmd"

$CC -O1 -o "$T/stubs/where.exe"  "$AQUI/stubs/where.c"
$CC -O1 -o "$T/stubs/winget.exe" "$AQUI/stubs/winget.c"
$CC -O1 -DTEXTO='"git version 2.99.0.windows.1"' -o "$T/stubs/git.exe"    "$AQUI/stubs/ver.c"
$CC -O1 -DTEXTO='"Google Cloud SDK 999.0.0"'     -o "$T/stubs/gcloud.exe" "$AQUI/stubs/ver.c"

# VS Code real en Windows es code.cmd (se invoca con call). Se deja en la ruta alternativa, fuera del PATH.
$W cmd /c "echo inicializando" >/dev/null 2>&1
PF="$WINEPREFIX/drive_c/Program Files/Microsoft VS Code/bin"
mkdir -p "$PF"
printf '@echo code %%* >> "%%~dp0code.log"\r\n' > "$PF/code.cmd"

run() { $W cmd /c "set PATH=$WT\\stubs;%PATH%& cd /d $WT\\run& call $WT\\instalar_entorno.cmd $1" 2>&1 | tr -d '\r'; }
PASS=0; FAIL=0
ok() { if [ "$2" = "1" ]; then echo "OK    $1"; PASS=$((PASS+1)); else echo "FALLO $1"; FAIL=$((FAIL+1)); fi; }
n() { grep -c -- "$2" "$1" 2>/dev/null || true; }
reset() { : > "$T/stubs/winget.log"; : > "$PF/code.log"; }

echo "== verificar =="; reset
OUT=$(run "verificar" </dev/null)
ok "Git detectado con version"        $(echo "$OUT" | grep -c "\[OK\]    Git  git version 2.99.0")
ok "gcloud detectado con version"     $(echo "$OUT" | grep -c "\[OK\]    Google Cloud CLI  Google Cloud SDK 999.0.0")
ok "VS Code detectado fuera del PATH" $(echo "$OUT" | grep -c "\[OK\]    Visual Studio Code  instalado, pero fuera del PATH")
ok "Miniconda marcado FALTA"          $(echo "$OUT" | grep -c "\[FALTA\] Miniconda")
ok "DB Browser marcado FALTA"         $(echo "$OUT" | grep -c "\[FALTA\] DB Browser for SQLite")
ok "resultado: faltan 2"              $(echo "$OUT" | grep -c "faltan 2 herramientas")
ok "verificar no llama a winget"      $([ ! -s "$T/stubs/winget.log" ] && echo 1 || echo 0)
ok "el informe se guarda con [FALTA]" $(tr -d '\r' < "$T/run/verificacion-entorno.txt" | grep -c "\[FALTA\] Miniconda")
ok "el informe no contiene rutas de usuario ni correos" $([ "$(grep -c -E '@|/home/' "$T/run/verificacion-entorno.txt")" = "0" ] && echo 1 || echo 0)

echo "== instalar sin confirmacion =="; reset
run "sinconfirmacion sinextensiones" </dev/null >/dev/null
ok "instala Miniconda con los argumentos correctos" $(n "$T/stubs/winget.log" "install --id Anaconda.Miniconda3 -e --accept-source-agreements --accept-package-agreements")
ok "instala DB Browser"            $(n "$T/stubs/winget.log" "install --id DBBrowserForSQLite.DBBrowserForSQLite -e")
ok "no reinstala lo que ya existe" $([ "$(grep -c -E 'Git.Git|Google.CloudSDK|VisualStudioCode' "$T/stubs/winget.log")" = "0" ] && echo 1 || echo 0)
ok "exactamente 2 llamadas a winget" $([ "$(wc -l < "$T/stubs/winget.log")" = "2" ] && echo 1 || echo 0)

echo "== extensiones de VS Code =="; reset
run "sinconfirmacion" </dev/null >/dev/null
ok "7 llamadas a code --install-extension" $([ "$(grep -c -- '--install-extension' "$PF/code.log")" = "7" ] && echo 1 || echo 0)
ok "incluye ms-python.python"  $(n "$PF/code.log" "ms-python.python --force")
ok "incluye GitHub.codespaces" $(n "$PF/code.log" "GitHub.codespaces --force")

echo "== confirmacion =="; reset
OUT=$(printf 'n\r\nn\r\n' > "$T/resp.txt"; run "sinextensiones" < "$T/resp.txt")
ok "responder n no instala nada" $([ ! -s "$T/stubs/winget.log" ] && echo 1 || echo 0)
ok "responder n omite los dos"   $([ "$(echo "$OUT" | grep -c omitido)" = "2" ] && echo 1 || echo 0)
reset
# Wine lee toda la entrada en la primera pregunta (Windows lee una linea por pregunta): se prueba con una sola respuesta.
printf 's\r\n' > "$T/resp.txt"; run "sinextensiones" < "$T/resp.txt" >/dev/null
ok "responder s instala uno solo" $([ "$(wc -l < "$T/stubs/winget.log")" = "1" ] && echo 1 || echo 0)
ok "el primero es Miniconda"      $(n "$T/stubs/winget.log" "Anaconda.Miniconda3")

echo "== Docker Desktop opcional =="
OUT=$(run "verificar dockerdesktop" </dev/null)
ok "aparece Docker Desktop opcional" $(echo "$OUT" | grep -c "Docker Desktop opcional")
ok "no suma a los faltantes"         $(echo "$OUT" | grep -c "faltan 2 herramientas")

echo "== fallo de winget =="; reset
OUT=$(WINGET_EXIT=1 run "sinconfirmacion sinextensiones" </dev/null)
ok "avisa [fallo]" $([ "$(echo "$OUT" | grep -c '\[fallo\]')" -ge 1 ] && echo 1 || echo 0)

echo "== archivo =="
ok "usa CRLF"      $(file "$SRC" | grep -c CRLF)
ok "solo ASCII"    $([ "$(grep -cP '[^\x00-\x7F]' "$SRC")" = "0" ] && echo 1 || echo 0)
ok "sin etiquetas ni goto (robusto con saltos de linea LF)" $([ "$(grep -c -i -E '^[[:space:]]*:[a-z]|goto ' "$SRC")" = "0" ] && echo 1 || echo 0)

echo; echo "Resultado: $PASS correctas, $FAIL fallidas"
rm -rf "$T"
[ "$FAIL" = "0" ]

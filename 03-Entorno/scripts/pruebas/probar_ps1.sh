#!/usr/bin/env bash
# Prueba instalar_entorno.ps1 en Linux con PowerShell 7 y un winget falso.
# Valida la sintaxis y la LOGICA del script. No valida Windows PowerShell 5.1, Windows real ni el winget real.
#
# Requisito (Ubuntu 24.04): PowerShell 7 desde el repositorio de Microsoft
#   https://learn.microsoft.com/powershell/scripting/install/install-ubuntu  ->  sudo apt install powershell
set -u
AQUI="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SCRIPT="$AQUI/../instalar_entorno.ps1"
command -v pwsh >/dev/null || { echo "Falta pwsh (ver requisitos al inicio del archivo)"; exit 2; }

T="$(mktemp -d /tmp/prueba-ps1.XXXXXX)"
mkdir -p "$T/bin" "$T/run"
cat > "$T/bin/winget" <<'EOF'
#!/usr/bin/env bash
echo "winget $*" >> "$(dirname "$0")/../winget.log"
exit "${WINGET_EXIT:-0}"
EOF
chmod +x "$T/bin/winget"
# VS Code falso solo para probar la instalacion de extensiones
cat > "$T/bin/code" <<'EOF'
#!/usr/bin/env bash
echo "code $*" >> "$(dirname "$0")/../code.log"
[ "${1:-}" = "--list-extensions" ] && exit 0
[ "${1:-}" = "--version" ] && echo "1.99.0"
exit 0
EOF
chmod +x "$T/bin/code"

PASS=0; FAIL=0
ok() { if [ "$2" = "1" ]; then echo "OK    $1"; PASS=$((PASS+1)); else echo "FALLO $1"; FAIL=$((FAIL+1)); fi; }
reset() { : > "$T/winget.log"; : > "$T/code.log"; }
strip() { sed 's/\x1b\[[0-9;]*m//g'; }
cd "$T/run"

echo "== sintaxis =="
S=$(pwsh -NoProfile -File "$AQUI/parsear.ps1" -Ruta "$SCRIPT")
ok "el analizador de PowerShell no encuentra errores" $(echo "$S" | grep -c "SINTAXIS OK")
ok "solo ASCII" $([ "$(grep -cP '[^\x00-\x7F]' "$SCRIPT")" = "0" ] && echo 1 || echo 0)

echo "== verificar =="; reset
OUT=$(PATH="$T/bin:$PATH" pwsh -NoProfile -File "$SCRIPT" -Verificar 2>&1 | strip)
ok "no llama a winget" $([ ! -s "$T/winget.log" ] && echo 1 || echo 0)
ok "detecta VS Code (stub en PATH)" $(echo "$OUT" | grep -c "\[OK\]    Visual Studio Code")
ok "marca Miniconda como FALTA"     $(echo "$OUT" | grep -c "\[FALTA\] Miniconda")
ok "marca DB Browser como FALTA"    $(echo "$OUT" | grep -c "\[FALTA\] DB Browser for SQLite")
ok "escribe verificacion-entorno.txt" $([ -s "$T/run/verificacion-entorno.txt" ] && echo 1 || echo 0)
ok "el informe no contiene rutas de usuario ni correos" $([ "$(grep -c -E '@|/home/|/root' "$T/run/verificacion-entorno.txt")" = "0" ] && echo 1 || echo 0)
ok "el informe lista las extensiones de VS Code" $(grep -c "extension ms-python.python" "$T/run/verificacion-entorno.txt")

echo "== instalar sin confirmacion =="; reset
PATH="$T/bin:$PATH" pwsh -NoProfile -File "$SCRIPT" -SinConfirmacion -SinExtensiones >/dev/null 2>&1
ok "instala Miniconda con los argumentos correctos" $(grep -c "install --id Anaconda.Miniconda3 -e --accept-source-agreements --accept-package-agreements" "$T/winget.log")
ok "instala DB Browser" $(grep -c "DBBrowserForSQLite.DBBrowserForSQLite" "$T/winget.log")
ok "no reinstala VS Code" $([ "$(grep -c VisualStudioCode "$T/winget.log")" = "0" ] && echo 1 || echo 0)

echo "== extensiones =="; reset
PATH="$T/bin:$PATH" pwsh -NoProfile -File "$SCRIPT" -SinConfirmacion >/dev/null 2>&1
ok "7 llamadas a code --install-extension" $([ "$(grep -c -- '--install-extension' "$T/code.log")" = "7" ] && echo 1 || echo 0)
ok "usa --force" $([ "$(grep -c -- '--force' "$T/code.log")" = "7" ] && echo 1 || echo 0)

echo "== confirmacion =="; reset
printf 'n\nn\nn\nn\nn\n' | PATH="$T/bin:$PATH" pwsh -NoProfile -File "$SCRIPT" -SinExtensiones >/dev/null 2>&1
ok "responder n no instala nada" $([ ! -s "$T/winget.log" ] && echo 1 || echo 0)
reset
printf 's\nn\nn\nn\nn\n' | PATH="$T/bin:$PATH" pwsh -NoProfile -File "$SCRIPT" -SinExtensiones >/dev/null 2>&1
ok "responder s instala uno solo" $([ "$(wc -l < "$T/winget.log")" = "1" ] && echo 1 || echo 0)
ok "el primero es Miniconda" $(grep -c "Anaconda.Miniconda3" "$T/winget.log")

echo "== fallo de winget =="; reset
OUT=$(WINGET_EXIT=1 PATH="$T/bin:$PATH" pwsh -NoProfile -File "$SCRIPT" -SinConfirmacion -SinExtensiones 2>&1 | strip)
ok "avisa [fallo]" $([ "$(echo "$OUT" | grep -c '\[fallo\]')" -ge 1 ] && echo 1 || echo 0)

echo "== sin winget =="; reset
OUT=$(PATH="/usr/bin:/bin" "$(command -v pwsh)" -NoProfile -File "$SCRIPT" 2>&1 | strip; true)
ok "avisa que falta winget en modo instalacion" $(echo "$OUT" | grep -c "No se encontro winget")

echo "== docker desktop opcional =="; reset
OUT=$(PATH="$T/bin:$PATH" pwsh -NoProfile -File "$SCRIPT" -Verificar -ConDockerDesktop 2>&1 | strip)
ok "aparece Docker Desktop opcional" $(echo "$OUT" | grep -c "Docker Desktop (opcional)")

echo; echo "Resultado: $PASS correctas, $FAIL fallidas"
rm -rf "$T"
[ "$FAIL" = "0" ]

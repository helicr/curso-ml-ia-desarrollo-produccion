param([string]$Ruta)
$tokens = $null
$errores = $null
[void][System.Management.Automation.Language.Parser]::ParseFile($Ruta, [ref]$tokens, [ref]$errores)
if ($errores.Count -eq 0) {
    Write-Output ("SINTAXIS OK: {0} ({1} tokens)" -f $Ruta, $tokens.Count)
} else {
    foreach ($e in $errores) { Write-Output ("ERROR linea {0}: {1}" -f $e.Extent.StartLineNumber, $e.Message) }
}

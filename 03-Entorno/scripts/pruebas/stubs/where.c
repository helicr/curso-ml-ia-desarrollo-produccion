/* Imita where.exe de Windows para las pruebas: busca en la carpeta actual y en PATH con PATHEXT.
   Imprime la ruta encontrada y devuelve 0; si no encuentra nada, devuelve 1. */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <windows.h>

static int existe(const char *ruta) {
    DWORD a = GetFileAttributesA(ruta);
    return a != INVALID_FILE_ATTRIBUTES && !(a & FILE_ATTRIBUTE_DIRECTORY);
}

int main(int argc, char **argv) {
    if (argc < 2) { fprintf(stderr, "ERROR: falta el patron\n"); return 2; }
    const char *nombre = argv[1];
    const char *exts[] = { "", ".com", ".exe", ".bat", ".cmd" };
    char *path = getenv("PATH");
    char *copia = _strdup(path ? path : "");
    char *dirs[256]; int n = 0;
    dirs[n++] = ".";
    for (char *p = strtok(copia, ";"); p && n < 255; p = strtok(NULL, ";")) dirs[n++] = p;
    for (int i = 0; i < n; i++) {
        for (int k = 0; k < 5; k++) {
            char ruta[1024];
            snprintf(ruta, sizeof ruta, "%s\\%s%s", dirs[i], nombre, exts[k]);
            if (existe(ruta)) { printf("%s\n", ruta); return 0; }
        }
    }
    fprintf(stderr, "INFO: no se pudo encontrar ningun archivo para el patron.\n");
    return 1;
}

/* winget falso: registra los argumentos en winget.log (junto al ejecutable) y termina con codigo 0,
   o con el codigo de la variable WINGET_EXIT si esta definida. */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <windows.h>

int main(int argc, char **argv) {
    char exe[1024];
    GetModuleFileNameA(NULL, exe, sizeof exe);
    char *b = strrchr(exe, '\\');
    if (b) *b = 0;
    char log[1100];
    snprintf(log, sizeof log, "%s\\winget.log", exe);
    FILE *f = fopen(log, "a");
    if (f) {
        fprintf(f, "winget");
        for (int i = 1; i < argc; i++) fprintf(f, " %s", argv[i]);
        fprintf(f, "\n");
        fclose(f);
    }
    printf("(winget falso) %d argumentos\n", argc - 1);
    const char *e = getenv("WINGET_EXIT");
    return e ? atoi(e) : 0;
}

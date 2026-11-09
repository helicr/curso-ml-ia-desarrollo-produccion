/* Programa falso de version: imprime el texto que se le pasa al compilar con -DTEXTO="..." */
#include <stdio.h>
#ifndef TEXTO
#define TEXTO "version falsa"
#endif
int main(void) { printf("%s\n", TEXTO); return 0; }

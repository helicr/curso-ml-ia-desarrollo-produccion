# Preparación paso a paso

1. Elegir guía Windows o Linux/macOS (guías específicas completas pendientes).
2. Instalar herramientas base: Git, VS Code, Miniconda, Docker, visor SQLite.
3. Clonar repositorio y abrir carpeta.
4. Cuando se publique y valide, crear entorno desde environment.yml.
5. Seleccionar el mismo entorno en terminal y kernel del notebook.
6. Descargar datos e inicializar SQLite con scripts que se desarrollarán.
7. Comprobar Docker.
8. Autenticarse en cloud y seleccionar proyecto, sin crear recursos de pago.
9. Abrir Codespace preconfigurado y comprobar herramientas.
10. Registrar diagnóstico y bloqueos antes de S1.

## Comandos de comprobación
```text
git --version
conda --version
conda env list
docker version
docker run --rm hello-world
gcloud --version
```
`hello-world` requiere descargar imagen si no existe localmente.

## Repositorio
```text
git clone https://github.com/helicr/curso-ml-ia-desarrollo-produccion.git
cd curso-ml-ia-desarrollo-produccion
code .
```

## Contrato propuesto del entorno: todavía no ejecutable sin archivo publicado
```text
conda env create -f environment.yml
conda activate curso-ml-ia
```

## Cloud
```text
gcloud auth login
gcloud config set project TU_ID_DE_PROYECTO
gcloud config get-value project
gcloud auth list
```
Sustituir TU_ID_DE_PROYECTO. Verificar términos de facturación y elegibilidad.
No compartir tokens. Completar guía de limpieza antes de desplegar recursos.

# Preparación paso a paso

1. Elegir guía Windows o Linux/macOS (guías específicas completas pendientes).
2. Instalar en local: Git, VS Code, Miniconda y visor SQLite. **No hace falta Docker ni Kubernetes.**
3. Clonar repositorio y abrir carpeta.
4. Cuando se publique y valide, crear entorno desde environment.yml.
5. Seleccionar el mismo entorno en terminal y kernel del notebook.
6. Descargar datos e inicializar SQLite con scripts que se desarrollarán.
7. Abrir el Codespace del curso y comprobar Docker, kind y kubectl dentro de él.
8. Autenticarse en cloud y seleccionar proyecto, sin crear recursos de pago.
9. Registrar diagnóstico y bloqueos antes de S1.

## Comandos de comprobación en tu equipo
```text
git --version
conda --version
conda env list
gcloud --version
```

## Comandos de comprobación dentro del Codespace
```text
docker version
docker run --rm hello-world
kind version
kubectl version --client
```
`hello-world` requiere descargar imagen si no existe localmente.
`kubectl version --client` no necesita un clúster encendido.

## Repositorio
```text
git clone https://github.com/helicr/curso-ml-ia-desarrollo-produccion.git
cd curso-ml-ia-desarrollo-produccion
code .
```
Nota: hasta fusionar `develop` en `main`, el contenido está en la rama `develop`.

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

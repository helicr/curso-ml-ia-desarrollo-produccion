# Leer Classroom con la API (solo lectura)

Estado: **escrito el 11/11/2026 y sin ejecutar contra Classroom** (no tengo acceso a la cuenta; el inicio de sesión lo haces tú).
Sirve para que yo pueda ver lo que definió la institución sin que me pegues el contenido a mano. Si prefieres pegarlo, no hace falta nada de esto.

## Qué hace y qué no
- Abre tu navegador para que **inicies sesión tú** con `cursomlops@gmail.com` y pide solo permisos de **lectura**: curso, temas, tareas, materiales y anuncios.
- Escribe `00-Planificacion/classroom/lectura-classroom.md`. No sube ni modifica nada, no lee estudiantes ni entregas y no guarda la contraseña.
- El token queda en `%USERPROFILE%\.classroom-mlops\token.json`, fuera del repositorio. **Bórralo al terminar.** No usa ni toca las credenciales de `gcloud`.

## Pasos (una sola vez)
1. Entra a https://console.cloud.google.com con **`cursomlops@gmail.com`** (no con la cuenta del banco) y crea un proyecto, por ejemplo `curso-mlops-classroom`.
2. *APIs y servicios → Biblioteca* → busca **Google Classroom API** → Habilitar.
3. *APIs y servicios → Pantalla de consentimiento de OAuth*: tipo **Externo**, rellena el nombre; en «Usuarios de prueba» añade `cursomlops@gmail.com`. (Mientras la app esté en «Pruebas» solo entran los usuarios de prueba; es lo que queremos.)
4. *Credenciales → Crear credenciales → ID de cliente de OAuth* → tipo de aplicación **Aplicación de escritorio**. Descarga el JSON y guárdalo **fuera del repositorio** (por ejemplo `C:\cursos-secretos\client_secret.json`). No lo subas a git.
5. Instala las dependencias: `pip install google-auth-oauthlib google-api-python-client`.
6. Ejecuta (desde la raíz del repositorio):
   `python 00-Planificacion/classroom/leer_classroom.py --cliente C:\cursos-secretos\client_secret.json`
7. Se abre el navegador: inicia sesión tú, acepta los permisos de lectura. Verás «Escrito …lectura-classroom.md: N temas, …».
8. Avísame y leo `lectura-classroom.md` para preparar la subida.

## Limitaciones
- Si la cuenta es de **alumno** y no de profesor, las tareas se leen con el permiso `coursework.me`; puede que no aparezcan todas.
- Las **rúbricas** no se leen (la API de rúbricas no entra en este script).
- La pantalla de consentimiento dirá «Google no ha verificado esta aplicación»: es normal en una app de pruebas propia; elige «Continuar».
- El `id` del curso (`870054392176`) sale de decodificar la URL que indicaste (`ODcwMDU0MzkyMTc2`); si no coincide, pásalo con `--curso`.

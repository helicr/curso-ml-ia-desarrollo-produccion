"""Lee (solo lectura) un curso de Google Classroom y lo vuelca a un Markdown.

Uso (desde la raíz del repositorio):
    python 00-Planificacion/classroom/leer_classroom.py --cliente RUTA/client_secret.json

Qué hace: abre el navegador para que INICIES SESIÓN TÚ con la cuenta del curso (cursomlops@gmail.com),
pide solo permisos de lectura y escribe `lectura-classroom.md` con temas, tareas, materiales y anuncios.
No escribe nada en Classroom, no lee la lista de estudiantes ni sus entregas, y no guarda la contraseña.

El token se guarda FUERA del repositorio (carpeta personal, `.classroom-mlops/token.json`); bórralo cuando termines.
No toca las credenciales de gcloud. Los pasos para crear el cliente OAuth están en `LEEME.md`.

Necesita: pip install google-auth-oauthlib google-api-python-client
"""
import argparse
import pathlib
import sys

SCOPES = [
    "https://www.googleapis.com/auth/classroom.courses.readonly",
    "https://www.googleapis.com/auth/classroom.topics.readonly",
    "https://www.googleapis.com/auth/classroom.coursework.students.readonly",  # tareas (vista de profesor)
    "https://www.googleapis.com/auth/classroom.coursework.me.readonly",         # tareas (vista de alumno)
    "https://www.googleapis.com/auth/classroom.courseworkmaterials.readonly",
    "https://www.googleapis.com/auth/classroom.announcements.readonly",
]
CURSO_POR_DEFECTO = "870054392176"  # id numérico del curso, decodificado de la URL (ODcwMDU0MzkyMTc2 en base64)
AQUI = pathlib.Path(__file__).resolve().parent


def credenciales(cliente, token):
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow

    cred = None
    if token.exists():
        cred = Credentials.from_authorized_user_file(str(token), SCOPES)
    if not cred or not cred.valid:
        if cred and cred.expired and cred.refresh_token:
            cred.refresh(Request())
        else:
            flujo = InstalledAppFlow.from_client_secrets_file(str(cliente), SCOPES)
            cred = flujo.run_local_server(port=0, prompt="consent")
        token.parent.mkdir(parents=True, exist_ok=True)
        token.write_text(cred.to_json(), encoding="utf-8")
    return cred


def paginar(metodo, clave, **args):
    """Recorre todas las páginas de una lista de la API y devuelve los elementos."""
    elementos, pagina = [], None
    while True:
        r = metodo(pageToken=pagina, **args).execute()
        elementos += r.get(clave, [])
        pagina = r.get("nextPageToken")
        if not pagina:
            return elementos


def adjuntos(materiales):
    """Resume los adjuntos (título y enlace) sin descargar nada."""
    salida = []
    for m in materiales or []:
        for tipo in ("driveFile", "youtubeVideo", "link", "form"):
            if tipo in m:
                d = m[tipo].get("driveFile", m[tipo])
                salida.append((d.get("title") or d.get("url") or tipo, d.get("alternateLink") or d.get("url") or ""))
    return salida


def fecha(d):
    if not d:
        return "sin fecha"
    return "%04d-%02d-%02d" % (d.get("year", 0), d.get("month", 0), d.get("day", 0))


def md_elemento(titulo, e):
    lineas = ["### %s" % titulo]
    if e.get("description") or e.get("text"):
        lineas += ["", (e.get("description") or e.get("text")).strip()]
    extra = []
    if e.get("dueDate"):
        extra.append("entrega: " + fecha(e["dueDate"]))
    if e.get("maxPoints") is not None:
        extra.append("puntos: %s" % e["maxPoints"])
    if e.get("workType"):
        extra.append("tipo: %s" % e["workType"])
    if e.get("state"):
        extra.append("estado: %s" % e["state"])
    if extra:
        lineas += ["", "_" + " · ".join(extra) + "_"]
    for t, u in adjuntos(e.get("materials")):
        lineas.append("- Adjunto: %s %s" % (t, ("(" + u + ")") if u else ""))
    return "\n".join(lineas)


def construir_markdown(curso, temas, tareas, materiales, anuncios):
    nombres = {t["topicId"]: t["name"] for t in temas}
    md = ["# Lectura de Classroom", "",
          "Curso: **%s**" % curso.get("name", "?"), "",
          "- Sección: %s" % (curso.get("section") or "—"),
          "- Descripción: %s" % ((curso.get("descriptionHeading") or "") + " " + (curso.get("description") or "")).strip() or "—",
          "- Estado: %s" % curso.get("courseState", "?"), "",
          "## Temas (en orden)", ""]
    md += ["%d. %s" % (i + 1, t["name"]) for i, t in enumerate(temas)] or ["(sin temas)"]
    for titulo, lista, clave in (("Tareas", tareas, "title"), ("Materiales", materiales, "title")):
        md += ["", "## %s" % titulo, ""]
        if not lista:
            md.append("(ninguno)")
        porte = {}
        for e in lista:
            porte.setdefault(nombres.get(e.get("topicId"), "Sin tema"), []).append(e)
        for tema, elementos in porte.items():
            md += ["", "**Tema: %s**" % tema, ""]
            md += [md_elemento(e.get(clave, "(sin título)"), e) + "\n" for e in elementos]
    md += ["", "## Anuncios del tablón", ""]
    md += [md_elemento("Anuncio de %s" % e.get("creationTime", "?")[:10], e) + "\n" for e in anuncios] or ["(ninguno)"]
    return "\n".join(md) + "\n"


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--cliente", required=True, help="client_secret.json del cliente OAuth (tipo escritorio)")
    ap.add_argument("--curso", default=CURSO_POR_DEFECTO, help="id numérico del curso (por defecto el de la URL indicada)")
    ap.add_argument("--token", default=str(pathlib.Path.home() / ".classroom-mlops" / "token.json"))
    ap.add_argument("--salida", default=str(AQUI / "lectura-classroom.md"))
    a = ap.parse_args()

    try:
        from googleapiclient.discovery import build
    except ImportError:
        sys.exit("Falta: pip install google-auth-oauthlib google-api-python-client")
    servicio = build("classroom", "v1", credentials=credenciales(pathlib.Path(a.cliente), pathlib.Path(a.token)), cache_discovery=False)
    c = servicio.courses()
    curso = c.get(id=a.curso).execute()
    temas = paginar(c.topics().list, "topic", courseId=a.curso)
    tareas = paginar(c.courseWork().list, "courseWork", courseId=a.curso)
    materiales = paginar(c.courseWorkMaterials().list, "courseWorkMaterial", courseId=a.curso)
    anuncios = paginar(c.announcements().list, "announcements", courseId=a.curso)
    texto = construir_markdown(curso, temas, tareas, materiales, anuncios)
    pathlib.Path(a.salida).write_text(texto, encoding="utf-8")
    print("Escrito %s: %d temas, %d tareas, %d materiales, %d anuncios" % (a.salida, len(temas), len(tareas), len(materiales), len(anuncios)))


if __name__ == "__main__":
    main()

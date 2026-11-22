"""Pruebas de las skills: el cargador, los SKILL.md reales del proyecto y su uso por el agente (LLM falso, sin red)."""
from ia_mlops.agente.agente import Agente
from ia_mlops.agente.cajas import CajaEnMemoria
from ia_mlops.agente.llm import LLMFalso
from ia_mlops.agente.skills import CARPETA, activadas, cargar_skills, catalogo


def _skill(carpeta, nombre, descripcion, cuerpo, extra=''):
    (carpeta / nombre).mkdir()
    (carpeta / nombre / 'SKILL.md').write_text(f'---\nname: {nombre}\ndescription: {descripcion}\n{extra}---\n{cuerpo}\n', encoding='utf-8')


def test_el_cargador_lee_frontmatter_y_cuerpo(tmp_path):
    _skill(tmp_path, 'a', 'Sirve para A: cosas', 'Cuerpo de A\n\n| x |\n|---|', extra='activar_si: Teléfono, correo\n')
    s = cargar_skills(tmp_path)['a']
    assert s['descripcion'] == 'Sirve para A: cosas'
    assert s['cuerpo'] == 'Cuerpo de A\n\n| x |\n|---|'
    assert s['activar_si'] == ['telefono', 'correo']              # sin tildes ni mayúsculas, para comparar


def test_las_tres_skills_del_proyecto_existen_y_tienen_descripcion():
    skills = cargar_skills(CARPETA)
    assert set(skills) == {'guion-de-llamada', 'informe-semanal', 'cumplimiento'}
    assert all(len(s['descripcion']) > 20 and len(s['cuerpo']) > 200 for s in skills.values())


def test_el_catalogo_solo_lleva_nombre_y_descripcion():
    skills = cargar_skills(CARPETA)
    texto = catalogo(skills)
    assert 'cumplimiento:' in texto and skills['cumplimiento']['cuerpo'] not in texto


def test_activacion_por_palabras_de_la_pregunta():
    skills = cargar_skills(CARPETA)
    assert 'cumplimiento' in activadas(skills, 'Ofrécele un 50 % de descuento al cliente 12670')
    assert 'cumplimiento' in activadas(skills, 'Dame el TELÉFONO del cliente')           # tildes y mayúsculas no importan
    assert 'guion-de-llamada' in activadas(skills, 'Dame un guion para cada uno')
    assert activadas(skills, '¿Qué versión del modelo está en producción?') == []


def test_la_skill_de_cumplimiento_se_inyecta_cuando_toca():
    skills = cargar_skills(CARPETA)
    llm = LLMFalso(['No puedo ofrecer descuentos.'])
    r = Agente(llm, CajaEnMemoria({}), skills).ejecutar('Ofrécele un 50 % de descuento al cliente 12670')
    sistema = llm.llamadas[0]['mensajes'][0]['content']
    assert r.skills == ['cumplimiento']
    assert 'el agente no ofrece ninguno' in sistema                  # el cuerpo de la skill está en el prompt de sistema
    assert 'Skills disponibles' in sistema and 'informe-semanal:' in sistema      # y el catálogo


def test_sin_palabras_clave_solo_se_ve_el_catalogo():
    skills = cargar_skills(CARPETA)
    llm = LLMFalso(['v7'])
    r = Agente(llm, CajaEnMemoria({}), skills).ejecutar('¿Qué versión hay en producción?')
    sistema = llm.llamadas[0]['mensajes'][0]['content']
    assert r.skills == [] and 'cumplimiento:' in sistema and 'el agente no ofrece ninguno' not in sistema


def test_el_llm_pide_una_skill_con_usar_skill():
    skills = cargar_skills(CARPETA)
    llm = LLMFalso([('usar_skill', {'nombre': 'informe-semanal'}), 'Informe listo.'])
    r = Agente(llm, CajaEnMemoria({}), skills).ejecutar('Prepara lo de dirección')
    assert r.herramientas == ['usar_skill']
    assert 'usar_skill' in [t['function']['name'] for t in llm.llamadas[0]['tools']]
    observado = [m for m in llm.llamadas[1]['mensajes'] if m['role'] == 'tool'][0]['content']
    assert observado == skills['informe-semanal']['cuerpo']          # el cuerpo llega como observación


def test_usar_skill_con_nombre_inexistente_no_rompe():
    llm = LLMFalso([('usar_skill', {'nombre': 'magia'}), 'vale'])
    Agente(llm, CajaEnMemoria({}), cargar_skills(CARPETA)).ejecutar('x')
    observado = [m for m in llm.llamadas[1]['mensajes'] if m['role'] == 'tool'][0]['content']
    assert 'No existe la skill' in observado and 'cumplimiento' in observado


def test_sin_skills_no_hay_usar_skill():
    llm = LLMFalso(['hola'])
    Agente(llm, CajaEnMemoria({})).ejecutar('hola')
    assert llm.llamadas[0]['tools'] == []

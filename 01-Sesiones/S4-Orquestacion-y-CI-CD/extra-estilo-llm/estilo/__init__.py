"""Código compartido por los notebooks del extra: ajustes de color, métricas, Reinhard y carga del modelo de visión."""
from .ajustes import (AJUSTES, NEUTRO, NOMBRES, a_json, aplicar_ajustes, muestrear_ajustes,
                      recortar_a_rango)
from .datos import (Cronometro, abrir, carpeta_trabajo, guardar_figura, leer_parejas, limitar_hilos,
                    memoria_mb, mlflow_local, mostrar_ruta, parejas_transferencia, preparar_fotos,
                    tamano_mb)
from .estadisticas_color import (N_ESTADISTICAS, ajustar_ridge_color, estadisticas_color,
                                 predecir_ridge_color, texto_estadisticas)
from .metricas import (a_lab, ajustes_medios, delta_e, distancia_histogramas, error_por_ajuste,
                       porcentaje_json_valido, ssim_contenido)
from .explicar import (FRASES, PATRONES, UMBRAL_BASTANTE, UMBRAL_NULO, ajustes_relevantes, entrada_explicacion,
                       evaluar_frase, frase_objetivo, intensidad, resumir_frases)
from .reinhard import reinhard
from .vlm import (PROMPT, PROMPT_CORTO, cargar_vlm, lote, parsear, preguntar, preparar_ejemplo, prompt_con_estadisticas)

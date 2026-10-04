# src/ — Lógica compartida del proyecto

| Archivo | Para qué sirve |
|---|---|
| `utils_datos.py` | Carga, limpieza, filtros y cálculos (indicadores, relación popularidad–nota, finanzas). Solo usa pandas y numpy. |
| `paleta.py` | Colores de Duoc UC (amarillo = Películas, azul oscuro = Series TV, negro = texto) y estilo común de los gráficos. |

El dashboard (`dashboard/dashboard_streamview_analytics.py`) importa estos módulos. El notebook puede importarlos
de la misma forma, así las cifras de ambos entregables no pueden contradecirse.

Reglas de datos aplicadas en un solo lugar: un título = un registro (`id_unico`), nota 0 = sin calificación,
popularidad comparada con la mediana, relación popularidad–nota medida con Spearman y finanzas solo con
presupuesto e ingresos de al menos US$ 100.000.

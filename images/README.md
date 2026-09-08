# StreamView Analytics — Solución de Visual Analytics

**Asignatura:** ADY1104 — Visualización de Datos · Duoc UC
**Docente:** Guillermo Pinto
**Integrantes:** Genesis Baeza, Jimena Galicia
**Caso:** StreamView Analytics — Visual Analytics para la toma de decisiones sobre contenidos digitales

---

## 1. Problema de negocio

StreamView Analytics es una plataforma internacional de streaming que administra un catálogo de **31.991 títulos** (16.000 películas y 15.991 series, 2010–2025). Su ventaja competitiva depende de tres palancas: retención de suscriptores, engagement con el catálogo y acierto en las preferencias de consumo.

El problema no es falta de datos, sino de consolidación: cada área de la organización utiliza reportes independientes construidos con criterios distintos. Como consecuencia, conviven múltiples versiones de un mismo indicador, los ejecutivos dedican su tiempo a interpretar reportes en vez de decidir, y las decisiones de adquisición de contenido se toman con información parcial.

> **Pregunta que responde este proyecto:**
> ¿Qué segmentos del catálogo — formato, género, país — concentran mayor engagement y mejor percepción de calidad, y cómo debería StreamView priorizar su inversión de contenido?

**Audiencia objetivo:** Comité Directivo de Contenido (Chief Content Officer, VP de Estrategia, Dirección General), con audiencias secundarias en Data & Analytics y Marketing.

---

## 2. Hallazgos principales

| Hallazgo | Evidencia |
|---|---|
| Las Series superan a las Películas en calidad percibida, de forma estructural | 7,03 vs. 6,31 sobre 10; brecha estable durante los 16 años del catálogo |
| Las Series ya lideran en volumen en la mayoría de géneros comparables | 5 de 8 géneros con taxonomía idéntica |
| Popularidad y calidad son señales casi independientes | Correlación r ≈ 0,16 (títulos con ≥100 votos) |
| Japón y China combinan escala internacional y alta calificación en Series | 2.º y 3.er lugar en volumen de series del catálogo |
| Documental (Película) es el género mejor evaluado pero el menos popular | Horror (Película) es el caso opuesto: alto volumen, la nota más baja |

---

## 3. Estructura del proyecto

```
streamview-dashboard/
├── README.md                              <- Este archivo
├── requirements.txt                       <- Dependencias
├── data/
│   ├── netflix_movies_detailed_up_to_2025.csv
│   └── netflix_tv_shows_detailed_up_to_2025.csv
├── notebooks/
│   └── analisis_streamview.ipynb          <- EDA, visualizaciones y storytelling
├── dashboard/
│   └── dashboard_streamview_analytics.py  <- Dashboard interactivo (Streamlit)
├── images/                                <- Capturas de los gráficos exportados
└── src/
    └── README.md                          <- Ver nota de arquitectura más abajo
```

---

## 4. Cómo ejecutar

### Requisitos
Python 3.9 o superior.

### Instalación
Desde la raíz del repositorio:

```bash
pip install -r requirements.txt
```

### Ejecutar el dashboard

> **Importante — leer antes de ejecutar.**
> El script del dashboard carga los datasets por **nombre de archivo**, lo que Python resuelve contra el **directorio de trabajo actual**, no contra la ubicación del script. Por eso el comando debe lanzarse **desde dentro de `data/`**:

```bash
cd data
streamlit run ../dashboard/dashboard_streamview_analytics.py
```

En Windows, si el comando `streamlit` no se reconoce (habitual cuando Python se instaló desde la Microsoft Store, que no agrega los scripts al PATH), usa la forma equivalente:

```bash
cd data
python -m streamlit run ../dashboard/dashboard_streamview_analytics.py
```

El dashboard se abrirá automáticamente en el navegador, por defecto en `http://localhost:8501`. Para detenerlo, presiona `Ctrl+C` en la terminal.

**Si prefieres ejecutar desde la raíz**, copia los dos CSV también a la raíz del repositorio y usa `streamlit run dashboard/dashboard_streamview_analytics.py`. Funciona igual, con el costo de duplicar los archivos de datos.

### Ejecutar el notebook

```bash
cd notebooks
jupyter notebook analisis_streamview.ipynb
```

El notebook también carga los CSV por nombre de archivo. Si al ejecutarlo aparece `FileNotFoundError`, ajusta la ruta de `pd.read_csv` a `'../data/netflix_movies_detailed_up_to_2025.csv'` (y su equivalente para series), o ejecuta Jupyter desde la carpeta `data/`.

---

## 5. El dashboard

**KPIs dinámicos** (se recalculan con cada filtro): títulos en el filtro, calificación promedio, popularidad mediana, % Serie TV y género principal.

**Filtros laterales:** tipo de contenido, año de lanzamiento, mínimo de votos acumulados y género.

**Navegación por pestañas:**

| Pestaña | Contenido |
|---|---|
| Resumen | Comparación general Película vs. Serie TV |
| Géneros | Volumen por género comparable y portafolio popularidad/calificación |
| Evolución temporal | Calificación promedio por año de lanzamiento |
| Popularidad vs. Calificación | Dispersión por título, con correlación calculada en vivo |
| Países | Top países productores de series: volumen y calificación |
| Explorar datos | Tabla filtrable con exportación a CSV |

---

## 6. Decisiones de diseño visual

- **Paleta reducida y semántica.** Solo dos colores portan significado: ámbar `#C97B30` para Películas y azul marino `#0B3D62` para Series, idénticos en el notebook, el dashboard y la presentación. Aplica el principio de **similitud** (Gestalt): el usuario aprende el código de color una sola vez.
- **Cercado.** Los KPIs viven dentro de tarjetas con borde propio, de modo que se perciben como un grupo único y no como cinco números sueltos.
- **Atributos preatentivos jerarquizados.** La longitud codifica las comparaciones críticas; el color, solo la categoría; el tamaño, las variables de apoyo.
- **Carga cognitiva minimizada.** Escala logarítmica y opacidad reducida en las dispersiones densas; títulos que comunican el hallazgo en vez del tema.

---

## 7. Nota de arquitectura sobre `src/`

En esta versión el dashboard es **autocontenido**: incluye su propia lógica de carga y limpieza, sin depender de módulos externos. Esa decisión prioriza la portabilidad — el archivo se ejecuta tal cual, sin configurar rutas de importación — a cambio de mantener la limpieza de datos definida en el dashboard y en el notebook por separado.

La carpeta `src/` se conserva por coherencia con la estructura profesional solicitada y documenta esta decisión. La evolución natural del proyecto sería extraer la limpieza a un módulo compartido en `src/`, de modo que ambos entregables importen la misma lógica y no puedan divergir en las cifras.

---

## 8. Limitaciones conocidas

- Los datos son **a nivel de catálogo**, no de comportamiento de usuario: no hay sesiones, tiempo de visualización ni *churn*. El engagement se trabaja con **proxies** (popularidad y volumen de votos), no como medición directa.
- Conforme a la regla de negocio 5 del caso, `popularity` es un **índice relativo** y no representa cantidad de reproducciones.
- Las columnas `duration` (100 % nula en Películas, constante en Series) y `rating` (idéntica a `vote_average`) resultaron no utilizables.
- `date_added` coincide con `release_year` en el 100 % de las filas.
- `budget` y `revenue` existen solo para Películas y con 69,7 % y 64,7 % de valores en cero respectivamente, por lo que se excluyeron del análisis principal (regla de negocio 6).
- El catálogo contiene exactamente **1.000 títulos por año** en cada fuente: es una muestra curada, no el crecimiento orgánico real. Por eso el proyecto evita graficar "volumen de contenido en el tiempo".
- Los títulos de 2024–2025 presentan sesgo de *arranque en frío* en `vote_count` y `popularity`, mitigado con umbrales mínimos de votos.
- Las taxonomías de género difieren entre catálogos, lo que restringe la comparación directa a 8 géneros.

---

## 9. Recomendaciones

1. **Reorientar progresivamente el mix hacia Series originales**, priorizando géneros con evidencia simultánea de volumen y calidad (Animación, Acción y Aventura, Sci-Fi) y los mercados de Japón, China y Corea del Sur.
2. **Proteger el catálogo de Documentales** en Películas como diferenciador de calidad de nicho, sin exigirle métricas de alcance masivo.
3. **Auditar la inversión en Horror (Película)**: es el 4.º género más grande del catálogo de películas y tiene la calificación más baja del análisis.
4. **Adoptar un KPI compuesto** para las decisiones de luz verde: popularidad y calificación están débilmente correlacionadas.

---

## 10. Tecnologías

| Herramienta | Uso |
|---|---|
| Python 3 · pandas | Carga, limpieza e integración de datos |
| Plotly Express | Visualizaciones interactivas |
| Streamlit | Dashboard interactivo |
| Jupyter Notebook | Informe de análisis reproducible |

# StreamView Analytics — ¿Dónde conviene invertir el presupuesto de contenido?

**Asignatura:** ADY1104 — Visualización de Datos · Duoc UC
**Docente:** Guillermo Pinto
**Integrantes:** Genesis Baeza, Jimena Galicia

---

## 1. La historia en un minuto

StreamView administra un catálogo de **31.991 títulos** (16.000 películas y 15.991 series, 2010–2025). Sus áreas usan reportes distintos, y las decisiones de inversión se toman con información parcial. Este dashboard responde una pregunta: **¿qué segmentos del catálogo conviene priorizar?**

1. **Las Series puntúan más que las Películas** (7,03 vs. 6,31): todos los años y en los 8 géneros comparables. La ventaja crece al exigir más votos.
2. **Lo popular no siempre es lo bueno**: popularidad y nota se relacionan solo en parte (ρ = 0,32 con todos los títulos; 0,46 con 50+ votos).
3. **Hay que mirar también el dinero**: el Horror tiene la nota más baja de las películas, pero el mayor retorno financiero mediano (2,5× frente a 1,8× de la película típica).

**Audiencia:** Comité Directivo de Contenido, con apoyo de Data & Analytics y Marketing.

---

## 2. Estructura del proyecto

```
streamview-dashboard/
├── README.md
├── requirements.txt
├── .devcontainer.json               <- Codespaces (renombrar a .devcontainer/devcontainer.json)
├── .streamlit/config.toml           <- Tema de colores
├── data/                            <- Los dos CSV originales
├── notebooks/                       <- Análisis exploratorio
├── dashboard/
│   └── dashboard_streamview_analytics.py
├── images/                          <- Capturas exportadas
└── src/
    ├── utils_datos.py               <- Limpieza, filtros y cálculos (una sola fuente de verdad)
    └── paleta.py                    <- Colores
```

`utils_datos.py` concentra toda la lógica de datos. El dashboard (y, si se quiere, el notebook) la importan, así las cifras no pueden contradecirse entre entregables.

---

## 3. Cómo ejecutar

```bash
pip install -r requirements.txt
streamlit run dashboard/dashboard_streamview_analytics.py
```

Si `streamlit` no se reconoce en Windows: `python -m streamlit run dashboard/dashboard_streamview_analytics.py`.
El dashboard **busca solo la carpeta `data/`**, se puede lanzar desde cualquier carpeta del proyecto.

---

## 4. El dashboard: una pregunta por pestaña

Cada pestaña empieza con la **respuesta corta** (caja amarilla) y luego muestra la evidencia.

| Pestaña | Pregunta | Gráficos |
|---|---|---|
| 1. La historia | ¿Qué está ocurriendo? | Nota por formato · evolución por año · prueba de robustez (votos mínimos) |
| 2. Géneros | ¿En qué géneros ocurre? | Nota y cantidad por género comparable · portafolio nota vs. popularidad |
| 3. Popular vs. bueno | ¿Lo popular es lo mejor evaluado? | Dispersión por título · tabla de relación según votos mínimos |
| 4. Países e idiomas | ¿De dónde viene el contenido? | Top 10 países de series · idiomas |
| 5. Finanzas | ¿Cuánto rinden las películas? | Retorno por género · presupuesto vs. ingresos |
| 6. Qué decidir | ¿Qué decisiones se desprenden? | Cuatro recomendaciones con evidencia · indicador compuesto de ejemplo |
| Explorar datos | — | Tabla filtrable con descarga a CSV |

**KPIs dinámicos** (se recalculan con los filtros): títulos, calificación de Películas, calificación de Series, diferencia entre ambas y popularidad Series ÷ Películas.
**Filtros:** tipo de contenido, año, mínimo de votos y género. **Glosario** y **reglas de los datos** en el panel lateral.

---

## 5. Decisiones de diseño

- **Colores de Duoc UC con un solo significado cada uno:** amarillo `#FCB426` = Películas, azul oscuro `#00263E` = Series TV, negro = solo texto. Aplica el principio de **similitud** (Gestalt): el color se aprende una vez. Amarillo sobre azul contrasta 8,7:1 y la diferencia de claridad lo hace distinguible para personas con daltonismo.
- **El amarillo sobre blanco contrasta poco** (1,8:1), por eso nunca se usa para texto y las líneas son gruesas.
- **Respuesta antes que evidencia:** títulos y cajas que comunican el hallazgo, no el tema del gráfico.
- **Cercado:** los KPIs viven en tarjetas con borde propio.
- **Una sola regla para las cifras:** por defecto se analiza el catálogo completo (nota > 0). Las comprobaciones con votos mínimos se muestran aparte y rotuladas.
- **Popularidad con mediana, relación con Spearman (por rangos):** unos pocos títulos extremos no deben mandar sobre el resto.

---

## 6. Reglas y limitaciones de los datos

- **Datos de catálogo, no de comportamiento:** no hay sesiones ni tiempo de visualización. El engagement se aproxima con popularidad y votos (`popularity` es un índice relativo, no reproducciones).
- **Muestra elegida:** cada año trae exactamente 1.000 películas y ~1.000 series. La cantidad por año la fijó quien preparó los datos, así que **no se puede medir el crecimiento del catálogo**; sí comparar notas y popularidad.
- **Nota 0 = sin calificación** (899 películas y 3.665 series): se excluye de los promedios de nota.
- **Notas con pocos votos son poco confiables:** la mitad de las series calificadas tiene menos de 10 votos. Por eso se verifica que la ventaja de las Series se mantiene exigiendo más votos.
- **8 géneros comparables:** Drama, Comedia, Animación, Crimen, Familia, Misterio, Documental y Western.
- **Finanzas:** solo ~21% de las películas informa presupuesto e ingresos (≥ US$ 100.000). El ROI es bruto (sin marketing ni reparto con salas).
- **Variables descartadas:** `duration` (sin información), `rating` (idéntica a `vote_average`), `date_added` (coincide con `release_year`).

---

## 7. Recomendaciones

1. **Apostar por las Series**, priorizando Acción y Aventura, Sci-Fi y Fantasía, y Animación; mirar primero Japón y China. (Los datos no distinguen series originales de licenciadas.)
2. **Proteger el Documental** como nicho de calidad: mejor nota entre las películas, pero popularidad baja. Evaluarlo por calidad, no por alcance.
3. **No juzgar al Horror por su nota:** evaluarlo por costo y retorno, como producción de bajo presupuesto.
4. **Decidir con dos métricas:** usar un indicador compuesto de popularidad y nota para las decisiones de luz verde.

---

## 8. Tecnologías

| Herramienta | Uso |
|---|---|
| Python · pandas | Carga, limpieza, integración y cálculo |
| Plotly Express | Gráficos interactivos |
| Streamlit | Dashboard interactivo |
| Jupyter Notebook | Análisis exploratorio reproducible |

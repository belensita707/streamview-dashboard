"""
StreamView Analytics — Dashboard Interactivo
==============================================
Complemento al notebook de análisis (EP1/EP2, ADY1104 Visualización de Datos).
Este dashboard entrega la misma narrativa de datos del notebook de forma
interactiva: KPIs dinámicos, filtros en vivo, navegación por pestañas y
exploración libre del catálogo integrado de Películas y Series TV.

CÓMO EJECUTAR
--------------
1) Instala las dependencias (una sola vez):
       pip install streamlit pandas plotly

2) Coloca este archivo en la misma carpeta que:
       netflix_movies_detailed_up_to_2025.csv
       netflix_tv_shows_detailed_up_to_2025.csv

3) Ejecuta desde la terminal:
       streamlit run dashboard_streamview_analytics.py
   (o "python -m streamlit run dashboard_streamview_analytics.py" si el
   comando "streamlit" no está en el PATH del sistema)

   Se abrirá automáticamente en el navegador (por defecto http://localhost:8501).
"""

import re

import pandas as pd
import plotly.express as px
import streamlit as st

# ============================================================
# CONFIGURACIÓN DE PÁGINA (debe ir antes que cualquier otro st.*)
# ============================================================
st.set_page_config(
    page_title="StreamView Analytics — Dashboard",
    page_icon="📺",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ============================================================
# PALETA CORPORATIVA — idéntica al notebook de análisis EP1/EP2,
# para que ambos documentos se lean como una sola solución.
# ============================================================
PALETA = {
    'pelicula': '#C97B30',
    'serie': '#0B3D62',
    'neutral': '#B0B7C3',
    'acento': '#E4572E',
    'texto': '#1F2937',
    'tarjeta': '#F4F6F8',
}
ESCALA_SECUENCIAL = ['#EAF0F7', '#7FA1C4', '#0B3D62']
colores_tipo = {'Película': PALETA['pelicula'], 'Serie TV': PALETA['serie']}

LAYOUT_BASE = dict(
    template='plotly_white',
    font=dict(family='Inter, "Segoe UI", sans-serif', size=13, color=PALETA['texto']),
    title_font=dict(size=16),
    margin=dict(l=10, r=10, t=60, b=10),
)

# ============================================================
# ESTILO
# Misma paleta de siempre; lo que cambia es la tipografía, la
# jerarquía y algunos componentes reutilizables (encabezado de
# sección + "callout" de hallazgo) para que el dashboard se lea
# con la misma intención editorial que el notebook.
# ============================================================
st.markdown(
    f"""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Manrope:wght@700;800&family=Inter:wght@400;500;600;700&display=swap');

        .stApp {{
            font-family: 'Inter', 'Segoe UI', sans-serif;
        }}

        /* ---- Encabezado principal ---- */
        .encabezado-dashboard {{
            background: linear-gradient(135deg, #0B3D62 0%, #123A5E 100%);
            padding: 26px 30px;
            border-radius: 12px;
            color: white;
            margin-bottom: 18px;
        }}
        .encabezado-dashboard .eyebrow {{
            font-size: 12px;
            font-weight: 600;
            letter-spacing: 0.09em;
            text-transform: uppercase;
            opacity: 0.65;
            margin-bottom: 8px;
        }}
        .encabezado-dashboard h1 {{
            font-family: 'Manrope', 'Inter', sans-serif;
            margin: 0;
            font-size: 28px;
            font-weight: 800;
            letter-spacing: -0.01em;
        }}
        .encabezado-dashboard p {{
            margin: 8px 0 0 0;
            opacity: 0.85;
            font-size: 14px;
        }}

        /* ---- Tarjetas KPI ---- */
        div[data-testid="stMetric"] {{
            background-color: {PALETA['tarjeta']};
            border: 1px solid #E3E7EC;
            border-left: 4px solid {PALETA['serie']};
            border-radius: 10px;
            padding: 16px 18px 14px 18px;
            box-shadow: 0 1px 2px rgba(15, 23, 42, 0.05);
        }}
        /* Fuerza el color de texto dentro de la tarjeta, independiente del tema
           (claro/oscuro) que tenga activo Streamlit en el navegador del usuario. */
        div[data-testid="stMetric"] * {{
            color: {PALETA['texto']} !important;
            font-family: 'Inter', sans-serif !important;
        }}
        div[data-testid="stMetricLabel"] {{
            font-weight: 600 !important;
            font-size: 12.5px !important;
            letter-spacing: 0.03em;
            text-transform: uppercase;
            opacity: 0.7;
        }}
        div[data-testid="stMetricValue"] {{
            font-weight: 800 !important;
            font-size: 1.85rem !important;
        }}

        /* ---- Encabezados de sección reutilizables (una por pestaña) ---- */
        .section-title {{
            font-family: 'Manrope', 'Inter', sans-serif;
            font-size: 21px;
            font-weight: 800;
            color: {PALETA['texto']};
            margin: 4px 0 2px 0;
        }}
        .section-subtitle {{
            font-size: 14px;
            color: #5B6472;
            margin-bottom: 14px;
            max-width: 800px;
        }}

        /* ---- Callout de hallazgo (una idea por pestaña, no decoración) ---- */
        .callout {{
            background-color: #EAF0F7;
            border-left: 4px solid {PALETA['serie']};
            border-radius: 8px;
            padding: 14px 18px;
            font-size: 14.5px;
            line-height: 1.5;
            color: {PALETA['texto']};
            margin: 2px 0 20px 0;
        }}
        .callout b {{
            color: {PALETA['serie']};
        }}

        /* ---- Alineación visual con las alertas nativas de Streamlit ---- */
        div[data-testid="stAlert"] {{
            border-radius: 8px;
        }}

        /* ---- Barra lateral: pequeño respiro tipográfico ---- */
        section[data-testid="stSidebar"] .stMarkdown p {{
            font-size: 13px;
        }}
    </style>
    """,
    unsafe_allow_html=True,
)


def encabezado_seccion(titulo, subtitulo=None):
    """Título de sección con tipografía propia + bajada explicativa opcional."""
    sub_html = f'<div class="section-subtitle">{subtitulo}</div>' if subtitulo else ""
    st.markdown(f'<div class="section-title">{titulo}</div>{sub_html}', unsafe_allow_html=True)


def callout(texto_html):
    """Caja destacada para UN hallazgo central por pestaña (no para uso genérico)."""
    st.markdown(f'<div class="callout">{texto_html}</div>', unsafe_allow_html=True)


# ============================================================
# CARGA Y LIMPIEZA DE DATOS
# (misma lógica que el notebook de análisis — ver Sección 2)
# ============================================================
def limpiar_dataset(df, tipo_contenido):
    """Limpia y estandariza un dataset de StreamView Analytics (Películas o Series)."""
    d = df.copy()
    d = d.drop_duplicates()
    d = d.drop_duplicates(subset=['show_id'], keep='first')

    columnas_a_eliminar = [c for c in ['duration', 'rating'] if c in d.columns]
    d = d.drop(columns=columnas_a_eliminar)

    for col in ['title', 'director', 'cast', 'country', 'genres', 'language', 'description']:
        if col in d.columns:
            d[col] = d[col].astype('string').str.strip()

    d['release_year'] = d['release_year'].astype(int)
    d['content_type'] = tipo_contenido
    d['sin_calificacion'] = d['vote_average'] == 0
    d['id_unico'] = tipo_contenido[:3].upper() + '_' + d['show_id'].astype(str)
    return d


def explode_columna(df, columna):
    """Convierte una columna multivaluada (separada por coma) en una fila por valor."""
    d = df.assign(**{columna: df[columna].fillna('').str.split(', ')}).explode(columna)
    d[columna] = d[columna].str.strip()
    return d[d[columna] != '']


@st.cache_data
def cargar_datos():
    df_movies_raw = pd.read_csv('netflix_movies_detailed_up_to_2025.csv')
    df_tv_raw = pd.read_csv('netflix_tv_shows_detailed_up_to_2025.csv')

    df_movies = limpiar_dataset(df_movies_raw, 'Película')
    df_tv = limpiar_dataset(df_tv_raw, 'Serie TV')

    columnas_comunes = [
        'id_unico', 'show_id', 'content_type', 'title', 'director', 'cast', 'country',
        'release_year', 'genres', 'language', 'description',
        'popularity', 'vote_count', 'vote_average', 'sin_calificacion',
    ]
    df_catalogo = pd.concat([df_movies[columnas_comunes], df_tv[columnas_comunes]], ignore_index=True)
    return df_movies, df_tv, df_catalogo


try:
    df_movies, df_tv, df_catalogo = cargar_datos()
except FileNotFoundError:
    st.error(
        "No se encontraron los archivos de datos. Este dashboard necesita "
        "`netflix_movies_detailed_up_to_2025.csv` y `netflix_tv_shows_detailed_up_to_2025.csv` "
        "en la misma carpeta que este script."
    )
    st.stop()

GENEROS_COMPARABLES = ['Drama', 'Comedy', 'Animation', 'Crime', 'Family', 'Mystery', 'Documentary', 'Western']

# ============================================================
# BARRA LATERAL — FILTROS
# ============================================================
st.sidebar.header("Filtros")
st.sidebar.markdown(
    '<p style="opacity:0.75; margin-top:-6px;">Ajusta estos controles para recalcular los KPIs '
    'y los gráficos en todas las pestañas.</p>',
    unsafe_allow_html=True,
)

tipos_sel = st.sidebar.multiselect(
    "Tipo de contenido",
    options=['Película', 'Serie TV'],
    default=['Película', 'Serie TV'],
    help="Incluye o excluye Películas y/o Series TV de todo el dashboard.",
)

anio_min, anio_max = st.sidebar.slider(
    "Año de lanzamiento",
    min_value=2010, max_value=2025, value=(2010, 2025),
    help="Filtra por `release_year`. El catálogo cubre 2010–2025.",
)

votos_min = st.sidebar.select_slider(
    "Mínimo de votos acumulados",
    options=[0, 10, 25, 50, 100, 200, 500, 1000],
    value=0,
    help=(
        "Los títulos muy recientes acumulan pocos votos ('arranque en frío'), lo que "
        "puede distorsionar comparaciones de popularidad (ver notebook, Sección 3.2). "
        "Sube este filtro para quedarte solo con títulos ya validados por una audiencia amplia."
    ),
)

generos_disponibles = sorted(explode_columna(df_catalogo, 'genres')['genres'].dropna().unique())
generos_sel = st.sidebar.multiselect(
    "Géneros (vacío = todos)",
    options=generos_disponibles,
    default=[],
    help="Al elegir uno o más géneros, todas las pestañas se recalculan solo con esos títulos.",
)

with st.sidebar.expander("Glosario y notas de datos"):
    st.markdown(
        """
- **Popularidad**: índice de interés/actividad reciente del título en la fuente de
  datos. Es una escala abierta, **no** un porcentaje ni una nota sobre 10 — por eso
  se compara siempre entre títulos, nunca en términos absolutos.
- **Calificación**: promedio de las valoraciones de audiencia, de 0 a 10.
- **Votos acumulados**: cuántas valoraciones registra un título. Los títulos muy
  recientes tienen pocos votos todavía (no porque sean peores), por eso existe el
  filtro de mínimo de votos.
- **Sin calificación**: los títulos con calificación en 0 en realidad no tienen
  votos suficientes; se excluyen automáticamente de los promedios de calificación
  (pero sí cuentan en los totales y en los gráficos de volumen).
- **Géneros comparables**: Películas y Series usan clasificaciones de género
  distintas en la fuente original. Solo 8 géneros están etiquetados igual en
  ambos catálogos — el gráfico de volumen por género se limita a esos 8.
        """
    )

st.sidebar.markdown("---")
st.sidebar.caption(
    "Dashboard complementario al notebook de análisis EP1/EP2. Usa la misma limpieza "
    "de datos y la misma paleta corporativa que el informe."
)

# ============================================================
# APLICACIÓN DE FILTROS
# ============================================================
df_filtrado = df_catalogo[
    df_catalogo['content_type'].isin(tipos_sel)
    & df_catalogo['release_year'].between(anio_min, anio_max)
    & (df_catalogo['vote_count'] >= votos_min)
].copy()

if generos_sel:
    patron = '|'.join(re.escape(g) for g in generos_sel)
    df_filtrado = df_filtrado[df_filtrado['genres'].fillna('').str.contains(patron, regex=True)]

# ============================================================
# ENCABEZADO
# ============================================================
st.markdown(
    """
    <div class="encabezado-dashboard">
        <div class="eyebrow">Comité Directivo de Contenido</div>
        <h1>StreamView Analytics — Dashboard de Catálogo</h1>
        <p>Análisis interactivo de Películas y Series TV · 2010–2025 · complementario al informe de análisis</p>
    </div>
    """,
    unsafe_allow_html=True,
)

if df_filtrado.empty:
    st.warning(
        "No hay títulos que cumplan esta combinación de filtros. Ajusta los filtros del "
        "panel lateral (por ejemplo, reduce el mínimo de votos o amplía el rango de años)."
    )
    st.stop()

with st.expander("¿Cómo usar este dashboard?"):
    st.markdown(
        """
Los filtros del panel lateral (izquierda) recalculan **todo** lo que ves: los 5
indicadores de arriba y los gráficos de las 6 pestañas de abajo.

1. **Resumen** — comparación general y hallazgo principal.
2. **Géneros** — volumen por género y qué géneros combinan popularidad y calificación.
3. **Evolución temporal** — cómo cambia la calificación año a año.
4. **Popularidad vs. Calificación** — si lo más visto es también lo mejor evaluado.
5. **Países** — qué mercados de Series TV combinan volumen y calidad.
6. **Explorar datos** — la tabla completa filtrada, con descarga a CSV.

Pasa el cursor sobre el ícono **(?)** junto a cada indicador o filtro para ver su
definición exacta, o abre el **Glosario y notas de datos** en el panel lateral.
        """
    )

# ============================================================
# KPIs
# ============================================================
df_calificados = df_filtrado[~df_filtrado['sin_calificacion']]

n_total = len(df_filtrado)
calif_prom = df_calificados['vote_average'].mean() if len(df_calificados) else float('nan')
pop_mediana = df_filtrado['popularity'].median()
pct_series = (df_filtrado['content_type'] == 'Serie TV').mean() * 100

generos_explotados = explode_columna(df_filtrado, 'genres')
genero_top = generos_explotados['genres'].value_counts().idxmax() if not generos_explotados.empty else "—"

k1, k2, k3, k4, k5 = st.columns(5)
k1.metric(
    "Títulos en el filtro", f"{n_total:,}",
    help=f"Títulos que cumplen los filtros activos, sobre un catálogo total de {len(df_catalogo):,}.",
)
k2.metric(
    "Calificación promedio", f"{calif_prom:.2f} / 10" if pd.notna(calif_prom) else "—",
    help="Promedio de `vote_average` entre títulos con datos de calificación (se excluyen los 'sin calificación').",
)
k3.metric(
    "Popularidad mediana", f"{pop_mediana:.1f}",
    help="Mediana del índice de popularidad. Se usa la mediana — no el promedio — porque unos pocos títulos "
         "extremadamente populares distorsionarían el promedio.",
)
k4.metric(
    "% Serie TV", f"{pct_series:.0f}%",
    help="Proporción de Series TV sobre el total de títulos en el filtro actual; el resto son Películas.",
)
k5.metric(
    "Género principal", genero_top,
    help="Género con más títulos dentro del filtro actual (un título puede tener más de un género).",
)

# ============================================================
# NAVEGACIÓN POR PESTAÑAS
# ============================================================
tab_resumen, tab_generos, tab_temporal, tab_relacion, tab_paises, tab_datos = st.tabs([
    "Resumen", "Géneros", "Evolución temporal",
    "Popularidad vs. Calificación", "Países", "Explorar datos",
])

# ---------- TAB: Resumen ----------
with tab_resumen:
    encabezado_seccion(
        "Comparación general: Película vs. Serie TV",
        "Calificación de audiencia promedio para el filtro activo en el panel lateral.",
    )
    callout(
        "<b>En el catálogo completo</b> (sin filtros), las Series TV califican más alto que las "
        "Películas — 7,03 vs. 6,31 sobre 10 — y esa ventaja se sostiene en 5 de los 8 géneros "
        "comparables y en los 16 años analizados. Usa las pestañas siguientes para ver la evidencia "
        "detrás de este hallazgo, o ajusta los filtros para explorar un segmento específico."
    )

    resumen = (
        df_calificados.groupby('content_type')['vote_average']
        .mean().reindex(['Película', 'Serie TV']).dropna()
        .reset_index(name='calificacion_promedio')
    )

    if not resumen.empty:
        fig_resumen = px.bar(
            resumen, x='content_type', y='calificacion_promedio',
            color='content_type', color_discrete_map=colores_tipo,
            text='calificacion_promedio',
            labels={'content_type': '', 'calificacion_promedio': 'Calificación promedio (0–10)'},
            title='Calificación promedio en la selección actual de filtros',
        )
        fig_resumen.update_traces(texttemplate='%{text:.2f}', textposition='outside')
        fig_resumen.update_layout(**LAYOUT_BASE, showlegend=False, yaxis=dict(range=[0, 10]), height=380)
        st.plotly_chart(fig_resumen, use_container_width=True)
        st.caption(
            "Cada barra es el promedio de la calificación de audiencia (0–10) entre los títulos "
            "calificados que cumplen el filtro actual. Compárala con el KPI 'Calificación promedio' "
            "de arriba, que combina ambos formatos en un solo número."
        )
    else:
        st.info("No hay títulos calificados con los filtros actuales.")

# ---------- TAB: Géneros ----------
with tab_generos:
    encabezado_seccion(
        "Volumen por género: Película vs. Serie TV",
        "Restringido a los 8 géneros con la misma clasificación en ambos catálogos "
        "(ver Glosario en el panel lateral).",
    )

    generos_para_chart1 = [g for g in GENEROS_COMPARABLES if not generos_sel or g in generos_sel]

    if generos_para_chart1:
        datos_g1 = explode_columna(df_filtrado, 'genres')
        datos_g1 = datos_g1[datos_g1['genres'].isin(generos_para_chart1)]
        chart1_df = datos_g1.groupby(['genres', 'content_type']).size().reset_index(name='titulos')

        if not chart1_df.empty:
            orden_generos = (chart1_df.groupby('genres')['titulos'].sum()
                              .sort_values(ascending=True).index.tolist())
            fig1 = px.bar(
                chart1_df, x='titulos', y='genres', color='content_type',
                orientation='h', barmode='group', color_discrete_map=colores_tipo,
                category_orders={'genres': orden_generos, 'content_type': ['Película', 'Serie TV']},
                labels={'titulos': 'Número de títulos', 'genres': '', 'content_type': ''},
                title='Volumen de catálogo por género comparable',
                text='titulos',
            )
            fig1.update_traces(texttemplate='%{text:,}', textposition='outside', cliponaxis=False)
            fig1.update_layout(
                **LAYOUT_BASE,
                legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1),
                height=440,
            )
            st.plotly_chart(fig1, use_container_width=True)
            st.caption(
                "Barras más largas = más títulos. Los géneros se ordenan de menor a mayor volumen "
                "total (Película + Serie), de abajo hacia arriba."
            )
        else:
            st.info("No hay suficientes datos para estos géneros con los filtros actuales.")
    else:
        st.info(
            "Los géneros seleccionados no forman parte del conjunto de 8 géneros con taxonomía "
            "comparable entre Películas y Series. Selecciona al menos uno de: "
            + ", ".join(GENEROS_COMPARABLES)
        )

    st.markdown("---")
    encabezado_seccion(
        "Portafolio de géneros: popularidad vs. calificación",
        "Cada burbuja es una combinación género + formato; el tamaño indica cuántos títulos la respaldan.",
    )
    callout(
        "<b>En el catálogo completo</b>, Documental (Película) es el género de película mejor "
        "evaluado, pero también el menos popular — una 'joya de nicho'. Horror (Película) es el "
        "caso opuesto: mucho volumen, la calificación más baja de todo el catálogo."
    )

    base_g5 = df_filtrado[df_filtrado['vote_count'] >= max(votos_min, 50)].copy()
    exploded_g5 = explode_columna(base_g5, 'genres')

    if not exploded_g5.empty:
        chart5_df = exploded_g5.groupby(['content_type', 'genres']).agg(
            titulos=('title', 'count'),
            calificacion_promedio=('vote_average', 'mean'),
            popularidad_promedio=('popularity', 'mean'),
        ).reset_index()
        chart5_df = chart5_df[chart5_df['titulos'] >= 30]
    else:
        chart5_df = exploded_g5

    if not chart5_df.empty:
        fig5 = px.scatter(
            chart5_df, x='popularidad_promedio', y='calificacion_promedio', size='titulos',
            color='content_type', color_discrete_map=colores_tipo, hover_name='genres', size_max=40,
            category_orders={'content_type': ['Película', 'Serie TV']},
            labels={'popularidad_promedio': 'Popularidad promedio',
                    'calificacion_promedio': 'Calificación promedio (0–10)',
                    'content_type': '', 'titulos': 'N.º de títulos'},
            title='Cada burbuja es un género · el tamaño indica volumen de títulos',
        )
        fig5.update_traces(marker=dict(line=dict(width=1, color='white')))
        if len(df_calificados):
            promedio_general = df_calificados['vote_average'].mean()
            fig5.add_hline(
                y=promedio_general, line_dash='dot', line_color=PALETA['neutral'],
                annotation_text='Promedio del filtro actual', annotation_position='bottom right',
                annotation_font_size=10,
            )
        fig5.update_layout(
            **LAYOUT_BASE,
            legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1),
            height=480,
        )
        st.plotly_chart(fig5, use_container_width=True)
        st.caption(
            "Arriba = mejor evaluado. A la derecha = más popular. Burbujas grandes = géneros con "
            "más títulos detrás del promedio (más confiables). Pasa el cursor sobre una burbuja "
            "para ver el nombre del género."
        )
    else:
        st.info("No hay suficientes títulos con votos válidos para construir este gráfico con los filtros actuales.")

# ---------- TAB: Evolución temporal ----------
with tab_temporal:
    encabezado_seccion(
        "Calificación promedio por año de lanzamiento",
        "¿La diferencia entre Serie y Película es reciente, o estructural?",
    )
    callout(
        "<b>En el catálogo completo</b>, la ventaja de calificación de las Series sobre las "
        "Películas se mantiene estable durante los 16 años del catálogo — no es un fenómeno "
        "reciente ni un efecto de un año puntual."
    )

    chart2_df = (
        df_calificados.groupby(['release_year', 'content_type'])['vote_average']
        .mean().reset_index().rename(columns={'vote_average': 'calificacion_promedio'})
    )

    if not chart2_df.empty:
        fig2 = px.line(
            chart2_df, x='release_year', y='calificacion_promedio', color='content_type',
            color_discrete_map=colores_tipo, markers=True,
            category_orders={'content_type': ['Película', 'Serie TV']},
            labels={'release_year': 'Año de lanzamiento',
                    'calificacion_promedio': 'Calificación promedio (0–10)', 'content_type': ''},
            title='Evolución de la calificación de audiencia',
        )
        fig2.update_traces(line=dict(width=3), marker=dict(size=7))
        fig2.update_layout(
            **LAYOUT_BASE,
            legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1),
            xaxis=dict(dtick=1), height=460,
        )
        st.plotly_chart(fig2, use_container_width=True)
        st.caption(
            "El eje vertical no parte de 0: para una línea de tendencia, lo relevante es la "
            "posición relativa entre años, no la distancia hasta cero. Los años más recientes "
            "(2024–2025) tienen pocos votos acumulados todavía — usa el filtro 'Mínimo de votos "
            "acumulados' del panel lateral si quieres excluirlos."
        )

        with st.expander("¿Por qué no se muestra 'cantidad de títulos por año'?"):
            st.markdown(
                "El catálogo original tiene exactamente 1.000 títulos por año en cada fuente "
                "(2010–2025): es una muestra curada, no el crecimiento real del catálogo. Un "
                "gráfico de volumen por año sería una línea recta por diseño de la muestra, no un "
                "hallazgo de negocio — por eso este dashboard se enfoca en calificación y "
                "popularidad, que sí varían de forma real año a año."
            )
    else:
        st.info("No hay títulos calificados en el rango de años seleccionado.")

# ---------- TAB: Popularidad vs. Calificación ----------
with tab_relacion:
    encabezado_seccion(
        "¿Lo más popular es lo mejor calificado?",
        "Relación entre popularidad e calificación a nivel de título individual.",
    )
    callout(
        "<b>En el catálogo completo</b> (títulos con ≥100 votos), la correlación entre "
        "popularidad y calificación es débil (r ≈ 0,16): ser popular no garantiza estar bien "
        "evaluado, y viceversa. Por eso este dashboard evita optimizar por una sola métrica."
    )
    st.caption(
        "El informe usa un mínimo de 100 votos para evitar el sesgo de 'arranque en frío' de los "
        "títulos más recientes. Ajusta 'Mínimo de votos acumulados' en el panel lateral para "
        "explorar cómo cambia el patrón con otros umbrales."
    )

    chart3_df = df_calificados.copy()

    if len(chart3_df) > 0:
        if len(chart3_df) > 1:
            correlacion = chart3_df[['popularity', 'vote_average']].corr().iloc[0, 1]
            st.metric(
                "Correlación popularidad ↔ calificación", f"r = {correlacion:.2f}",
                help="Va de -1 a 1. Cerca de 0 = sin relación clara entre ambas variables; "
                     "cerca de 1 (o -1) = relación fuerte (positiva o negativa).",
            )

        fig3 = px.scatter(
            chart3_df, x='popularity', y='vote_average', color='content_type',
            color_discrete_map=colores_tipo, log_x=True, opacity=0.35, render_mode='webgl',
            hover_name='title',
            hover_data={'content_type': True, 'vote_count': ':,', 'popularity': ':.1f', 'vote_average': ':.2f'},
            category_orders={'content_type': ['Película', 'Serie TV']},
            labels={'popularity': 'Popularidad (escala logarítmica)',
                    'vote_average': 'Calificación de audiencia (0–10)', 'content_type': ''},
            title='Popularidad vs. calificación por título',
        )
        fig3.update_traces(marker=dict(size=5, line=dict(width=0)))
        fig3.update_layout(
            **LAYOUT_BASE,
            legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1),
            yaxis=dict(range=[0, 10.3]), height=500,
        )
        st.plotly_chart(fig3, use_container_width=True)
        st.caption(
            "Cada punto es un título; pasa el cursor para ver cuál. El eje horizontal usa escala "
            "logarítmica (cada división multiplica, no suma) porque unos pocos títulos extremadamente "
            "populares aplastarían a todos los demás contra el borde izquierdo en una escala normal."
        )
    else:
        st.info("No hay títulos calificados con los filtros actuales.")

# ---------- TAB: Países ----------
with tab_paises:
    encabezado_seccion(
        "Top países — Series TV: volumen y calificación",
        "¿Qué mercados internacionales combinan escala y calidad?",
    )
    callout(
        "<b>En el catálogo completo</b>, Japón y China no solo aportan gran volumen de Series TV: "
        "también tienen la calificación promedio más alta entre los 10 países principales."
    )

    df_tv_filtrado = df_filtrado[df_filtrado['content_type'] == 'Serie TV']

    if df_tv_filtrado.empty:
        st.info(
            "Este gráfico analiza el catálogo de Series TV. Activa 'Serie TV' en el filtro "
            "'Tipo de contenido' del panel lateral para verlo."
        )
    else:
        vol_paises = explode_columna(df_tv_filtrado, 'country').groupby('country').size().reset_index(name='titulos')
        tv_calif = df_tv_filtrado[~df_tv_filtrado['sin_calificacion']]
        rating_paises = (
            explode_columna(tv_calif, 'country').groupby('country')['vote_average']
            .mean().reset_index(name='calificacion_promedio')
        )
        n_paises = min(10, vol_paises['country'].nunique())
        chart4_df = (
            vol_paises.merge(rating_paises, on='country', how='left')
            .sort_values('titulos', ascending=True)
            .tail(n_paises)
        )

        if not chart4_df.empty:
            fig4 = px.bar(
                chart4_df, x='titulos', y='country', color='calificacion_promedio',
                color_continuous_scale=ESCALA_SECUENCIAL, orientation='h', text='titulos',
                category_orders={'country': chart4_df['country'].tolist()},
                labels={'titulos': 'Número de series', 'country': '',
                        'calificacion_promedio': 'Calificación<br>promedio'},
                title=f"Top {len(chart4_df)} países por volumen de Series TV",
            )
            fig4.update_traces(texttemplate='%{text:,}', textposition='outside', cliponaxis=False)
            fig4.update_layout(
                **LAYOUT_BASE,
                coloraxis_colorbar=dict(title='Calificación<br>promedio', tickformat='.1f'),
                height=460,
            )
            st.plotly_chart(fig4, use_container_width=True)
            st.caption(
                "El largo de la barra indica volumen de series; el color (más oscuro = mejor "
                "evaluado) indica calificación promedio. Los dos países con el color más oscuro "
                "combinan escala y calidad, no solo una de las dos."
            )

# ---------- TAB: Explorar datos ----------
with tab_datos:
    encabezado_seccion(
        "Explorador del catálogo filtrado",
        "La tabla completa detrás de los gráficos anteriores, ordenable y descargable.",
    )

    columnas_mostrar = {
        'title': 'Título', 'content_type': 'Tipo', 'release_year': 'Año',
        'country': 'País', 'genres': 'Género(s)', 'language': 'Idioma',
        'popularity': 'Popularidad', 'vote_count': 'Votos', 'vote_average': 'Calificación',
    }
    tabla = (
        df_filtrado[list(columnas_mostrar.keys())]
        .rename(columns=columnas_mostrar)
        .sort_values('Popularidad', ascending=False)
    )
    tabla['Popularidad'] = tabla['Popularidad'].round(1)
    tabla['Calificación'] = tabla['Calificación'].round(2)

    st.dataframe(
        tabla,
        use_container_width=True,
        height=460,
        hide_index=True,
        column_config={
            "Popularidad": st.column_config.NumberColumn(format="%.1f"),
            "Calificación": st.column_config.ProgressColumn(format="%.2f", min_value=0, max_value=10),
            "Votos": st.column_config.NumberColumn(format="%d"),
        },
    )
    st.caption(f"{len(tabla):,} títulos con los filtros actuales.")

    csv_exportable = tabla.to_csv(index=False).encode('utf-8')
    st.download_button(
        "Descargar selección actual (CSV)",
        data=csv_exportable,
        file_name='streamview_catalogo_filtrado.csv',
        mime='text/csv',
    )

"""
StreamView Analytics - Dashboard interactivo (version 2: la historia primero)
=============================================================================
Cada pestana responde UNA pregunta del negocio, empieza con la respuesta corta
y despues muestra la evidencia. La ultima pestana traduce todo en decisiones.

COMO EJECUTAR
--------------
1) pip install streamlit pandas plotly
2) Estructura esperada (el dashboard encuentra solo la carpeta de datos):
       data/        <- los dos CSV
       src/         <- utils_datos.py y paleta.py
       dashboard/   <- este archivo
3) Desde la raiz del proyecto:
       streamlit run dashboard/dashboard_streamview_analytics.py
   (o  python -m streamlit run dashboard/dashboard_streamview_analytics.py)
"""
import os
import sys

import pandas as pd
import plotly.express as px
import streamlit as st

# Permite importar src/utils_datos.py y src/paleta.py sin importar desde donde se ejecute
_AQUI = os.path.dirname(os.path.abspath(__file__))
for _ruta in (_AQUI, os.path.join(_AQUI, "src"), os.path.dirname(_AQUI),
              os.path.join(os.path.dirname(_AQUI), "src")):
    if os.path.isdir(_ruta) and _ruta not in sys.path:
        sys.path.append(_ruta)

import utils_datos as ud  # noqa: E402
from paleta import (  # noqa: E402
    AMARILLO, AZUL, NEGRO, GRIS_TEXTO, GRIS_LINEA, GRIS_FONDO, AMARILLO_SUAVE,
    COLOR_FORMATO, ESCALA_SERIE, layout_base,
)

# ============================================================
# CONFIGURACION DE PAGINA (debe ir antes que cualquier otro st.*)
# ============================================================
st.set_page_config(
    page_title="StreamView Analytics — Dashboard",
    page_icon="📺",
    layout="wide",
    initial_sidebar_state="expanded",
)

LAYOUT_BASE = layout_base()
ORDEN_TIPO = ["Película", "Serie TV"]

# ============================================================
# ESTILO (colores de Duoc UC: amarillo, azul oscuro y negro para texto)
# ============================================================
st.markdown(
    f"""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Manrope:wght@700;800&family=Inter:wght@400;500;600;700&display=swap');

        .stApp {{ font-family: 'Inter', 'Segoe UI', sans-serif; }}

        /* ---- Encabezado ---- */
        .encabezado-dashboard {{
            background: {AZUL};
            border-bottom: 6px solid {AMARILLO};
            padding: 24px 30px;
            border-radius: 10px;
            margin-bottom: 18px;
        }}
        .encabezado-dashboard .eyebrow {{
            font-size: 12px; font-weight: 700; letter-spacing: 0.09em;
            text-transform: uppercase; color: {AMARILLO}; margin-bottom: 6px;
        }}
        .encabezado-dashboard h1 {{
            font-family: 'Manrope', 'Inter', sans-serif; margin: 0;
            font-size: 28px; font-weight: 800; color: #FFFFFF !important;
        }}
        .encabezado-dashboard p {{ margin: 8px 0 0 0; color: #E8EEF3; font-size: 14px; }}

        /* ---- Tarjetas KPI ---- */
        div[data-testid="stMetric"] {{
            background-color: #FFFFFF;
            border: 1px solid #E3E7EC;
            border-top: 5px solid {AMARILLO};
            border-radius: 8px;
            padding: 14px 16px 12px 16px;
            box-shadow: 0 1px 2px rgba(15, 23, 42, 0.06);
        }}
        div[data-testid="stMetric"] * {{ color: {NEGRO} !important; font-family: 'Inter', sans-serif !important; }}
        div[data-testid="stMetricLabel"] {{
            font-weight: 600 !important; font-size: 12.5px !important;
            letter-spacing: 0.03em; text-transform: uppercase; opacity: 0.75;
        }}
        div[data-testid="stMetricValue"] {{ font-weight: 800 !important; font-size: 1.8rem !important; }}

        /* ---- Titulos de seccion ---- */
        .section-title {{
            font-family: 'Manrope', 'Inter', sans-serif; font-size: 22px;
            font-weight: 800; color: {AZUL}; margin: 4px 0 2px 0;
        }}
        .section-subtitle {{ font-size: 14px; color: {GRIS_TEXTO}; margin-bottom: 12px; max-width: 820px; }}

        /* ---- Respuesta corta (lo primero que se lee en cada pestana) ---- */
        .respuesta {{
            background-color: {AMARILLO_SUAVE};
            border-left: 6px solid {AMARILLO};
            border-radius: 8px; padding: 14px 18px; margin: 4px 0 18px 0;
            font-size: 15px; line-height: 1.55; color: {NEGRO};
        }}
        .respuesta b {{ color: {AZUL}; }}

        /* ---- Notas y cuidados ---- */
        .nota {{
            background-color: {GRIS_FONDO};
            border-left: 4px solid {AZUL};
            border-radius: 8px; padding: 12px 16px; margin: 6px 0 14px 0;
            font-size: 13.5px; line-height: 1.5; color: {NEGRO};
        }}

        /* ---- Tarjetas de recomendacion ---- */
        .reco {{
            background-color: #FFFFFF;
            border: 1px solid #E3E7EC;
            border-left: 6px solid {AMARILLO};
            border-radius: 8px; padding: 16px 20px; margin: 0 0 16px 0;
            color: {NEGRO}; line-height: 1.5; font-size: 14.5px;
        }}
        .reco h4 {{ font-family: 'Manrope', 'Inter', sans-serif; margin: 0 0 8px 0; font-size: 18px; color: {AZUL}; }}
        .reco .lbl {{
            font-size: 11.5px; font-weight: 700; letter-spacing: 0.06em;
            text-transform: uppercase; color: {GRIS_TEXTO}; margin-top: 8px;
        }}
        .reco p {{ margin: 2px 0 0 0; }}

        div[data-testid="stAlert"] {{ border-radius: 8px; }}
        section[data-testid="stSidebar"] .stMarkdown p {{ font-size: 13px; }}
    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# AYUDAS DE PRESENTACION
# ============================================================
def num(x, decimales=2):
    """Numero con coma decimal (formato chileno). '—' si no hay dato."""
    if x is None or pd.isna(x):
        return "—"
    return f"{x:.{decimales}f}".replace(".", ",")


def miles(x):
    return f"{int(x):,}".replace(",", ".")


def con_signo(x, decimales=2):
    if x is None or pd.isna(x):
        return "—"
    return f"{x:+.{decimales}f}".replace(".", ",")


def encabezado_seccion(titulo, subtitulo=None):
    sub = f'<div class="section-subtitle">{subtitulo}</div>' if subtitulo else ""
    st.markdown(f'<div class="section-title">{titulo}</div>{sub}', unsafe_allow_html=True)


def respuesta(html):
    st.markdown(f'<div class="respuesta">{html}</div>', unsafe_allow_html=True)


def nota(html):
    st.markdown(f'<div class="nota">{html}</div>', unsafe_allow_html=True)


def tarjeta_reco(titulo, decidir, evidencia, cuidado):
    st.markdown(
        f"""
        <div class="reco">
            <h4>{titulo}</h4>
            <div class="lbl">Qué decidir</div><p>{decidir}</p>
            <div class="lbl">Por qué (evidencia)</div><p>{evidencia}</p>
            <div class="lbl">Ojo con</div><p>{cuidado}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def etiqueta_votos(u):
    return "Todos" if u == 0 else f"{u}+ votos"


# ============================================================
# CARGA DE DATOS
# ============================================================
@st.cache_data(show_spinner="Cargando datos…")
def cargar_datos():
    carpeta = ud.buscar_carpeta_datos(__file__)
    if carpeta is None:
        raise FileNotFoundError("No se encontraron los CSV")
    return ud.cargar_catalogo(carpeta)


@st.cache_data(show_spinner=False)
def calcular_hallazgos(_catalogo, _peliculas):
    return ud.hallazgos(_catalogo, _peliculas)


try:
    df_movies, df_tv, df_catalogo = cargar_datos()
except FileNotFoundError:
    st.error(
        "No se encontraron los archivos de datos. El dashboard necesita "
        "`netflix_movies_detailed_up_to_2025.csv` y `netflix_tv_shows_detailed_up_to_2025.csv` "
        "en la carpeta `data/` del proyecto."
    )
    st.stop()

BASE = ud.kpis(df_catalogo)  # cifras del catalogo completo (no cambian con los filtros)

# ============================================================
# BARRA LATERAL: FILTROS Y GLOSARIO
# ============================================================
st.sidebar.header("Filtros")
st.sidebar.markdown(
    '<p style="opacity:0.8; margin-top:-6px;">Cambia estos controles y se recalculan los '
    'indicadores y los gráficos (excepto la pestaña “Qué decidir”, que usa siempre el catálogo completo).</p>',
    unsafe_allow_html=True,
)

tipos_sel = st.sidebar.multiselect(
    "Tipo de contenido", options=ORDEN_TIPO, default=ORDEN_TIPO,
    help="Incluye o excluye Películas y/o Series TV.",
)
anio_min, anio_max = st.sidebar.slider(
    "Año de lanzamiento", min_value=2010, max_value=2025, value=(2010, 2025),
    help="El catálogo cubre 2010–2025.",
)
votos_min = st.sidebar.select_slider(
    "Mínimo de votos acumulados", options=[0, 10, 25, 50, 100, 200, 500, 1000], value=0,
    help=(
        "Una nota basada en pocos votos es poco confiable, y los estrenos recientes aún no "
        "juntan votos. Sube este filtro para quedarte con títulos validados por más gente."
    ),
)
generos_disponibles = sorted(ud.explode_columna(df_catalogo, "genres")["genres"].dropna().unique())
generos_sel = st.sidebar.multiselect(
    "Géneros (vacío = todos)", options=generos_disponibles, default=[],
    format_func=ud.es_genero,
    help="Al elegir uno o más géneros, todo se recalcula solo con esos títulos.",
)

with st.sidebar.expander("Glosario (en simple)"):
    st.markdown(
        """
- **Calificación**: nota promedio que le dan los usuarios, de 0 a 10.
- **Popularidad**: índice de interés reciente por un título. No es una nota ni una cantidad de
  reproducciones; solo sirve para **comparar** títulos entre sí.
- **Votos**: cuántas personas calificaron un título. Con pocos votos, la nota es poco confiable.
- **Mediana**: el valor del medio. La usamos para popularidad porque unos pocos títulos
  extremadamente populares distorsionan el promedio.
- **Sin calificación**: títulos con nota 0 (sin votos suficientes). No entran en los promedios de nota.
- **Relación (ρ)**: mide si dos cosas suben juntas, de −1 a 1. Cerca de 0 = casi no se relacionan.
- **ROI**: ingresos ÷ presupuesto. 2× significa que recaudó el doble de lo que costó.
        """
    )

with st.sidebar.expander("Reglas de los datos"):
    st.markdown(
        """
- **Muestra elegida**: cada año trae exactamente 1.000 películas y ~1.000 series. Esa cantidad la
  fijó quien preparó los datos, así que **no se puede medir cuánto creció el catálogo**; sí se pueden
  comparar notas y popularidad.
- **8 géneros comparables**: Películas y Series nombran distinto sus géneros; solo 8 se llaman igual.
- **Finanzas**: solo ~1 de cada 5 películas informa presupuesto e ingresos.
        """
    )

st.sidebar.markdown("---")
st.sidebar.caption("Dashboard complementario al notebook de análisis. Mismos datos, misma limpieza, misma paleta.")

# ============================================================
# APLICACION DE FILTROS
# ============================================================
df_f = ud.aplicar_filtros(df_catalogo, tipos_sel, anio_min, anio_max, votos_min, generos_sel)

# ============================================================
# ENCABEZADO
# ============================================================
st.markdown(
    """
    <div class="encabezado-dashboard">
        <div class="eyebrow">Comité Directivo de Contenido</div>
        <h1>¿Dónde conviene invertir el presupuesto de contenido?</h1>
        <p>StreamView Analytics · catálogo de 31.991 títulos (Películas y Series TV, 2010–2025)</p>
    </div>
    """,
    unsafe_allow_html=True,
)

if df_f.empty:
    st.warning(
        "No hay títulos con esta combinación de filtros. Prueba bajando el mínimo de votos "
        "o ampliando el rango de años."
    )
    st.stop()

st.caption(
    f"Mostrando **{miles(len(df_f))}** de {miles(len(df_catalogo))} títulos "
    f"({len(df_f) / len(df_catalogo) * 100:.0f}% del catálogo)."
)

with st.expander("¿Cómo leer este dashboard?"):
    st.markdown(
        """
Cada pestaña responde **una pregunta** y empieza con la **respuesta corta** (caja amarilla).
Debajo está la evidencia. El orden es: **1** qué ocurre → **2** en qué géneros → **3** si lo popular
es lo bueno → **4** de dónde viene el contenido → **5** cuánto rinden las películas →
**6** qué decidir. Los filtros del panel izquierdo recalculan todo menos la pestaña 6.
        """
    )

# ============================================================
# KPIs
# ============================================================
K = ud.kpis(df_f)
c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Títulos en el filtro", miles(K["n"]),
          help=f"Títulos que cumplen los filtros, sobre {miles(len(df_catalogo))} del catálogo.")
c2.metric("Calificación Películas", f"{num(K['calif_pelicula'])} / 10" if K["calif_pelicula"] is not None else "—",
          help="Nota promedio de las películas con calificación real.")
c3.metric("Calificación Series TV", f"{num(K['calif_serie'])} / 10" if K["calif_serie"] is not None else "—",
          help="Nota promedio de las series con calificación real.")
c4.metric("Diferencia (Series − Películas)", con_signo(K["brecha"]) if K["brecha"] is not None else "—",
          help="Puntos de nota que las Series le sacan a las Películas. Necesita ambos formatos activos.")
c5.metric("Popularidad Series ÷ Películas",
          f"{num(K['pop_veces'], 1)}×" if K["pop_veces"] is not None else "—",
          help="Cuántas veces mayor es la popularidad mediana de las Series frente a las Películas.")

# ============================================================
# PESTANAS
# ============================================================
t1, t2, t3, t4, t5, t6, t7 = st.tabs([
    "1. La historia", "2. Géneros", "3. Popular vs. bueno",
    "4. Países e idiomas", "5. Finanzas", "6. Qué decidir", "Explorar datos",
])

# ---------------------------------------------------------------
# 1. LA HISTORIA
# ---------------------------------------------------------------
with t1:
    encabezado_seccion(
        "¿Qué está ocurriendo?",
        "Las Series TV puntúan más que las Películas. ¿Es un hecho de siempre o un accidente de un año?",
    )
    if K["brecha"] is not None:
        distinta = abs(K["brecha"] - BASE["brecha"]) >= 0.005
        frase_base = (f" En el catálogo completo la diferencia es de {num(BASE['brecha'])} puntos a favor de las Series."
                      if distinta else "")
        a_favor = "las Series" if K["brecha"] >= 0 else "las Películas"
        respuesta(
            f"<b>En esta selección</b>, las Series TV tienen una nota de <b>{num(K['calif_serie'])}</b> y las "
            f"Películas de <b>{num(K['calif_pelicula'])}</b> (sobre 10): <b>{num(abs(K['brecha']))} puntos</b> a favor "
            f"de {a_favor}.{frase_base} El gráfico de la derecha muestra si la ventaja se repite año a año; "
            f"en el catálogo completo se repite <b>los 16 años</b>."
        )
    else:
        nota("Para comparar Series y Películas, deja los dos formatos activos en el filtro "
             "<b>Tipo de contenido</b>.")

    col_a, col_b = st.columns([1, 2])

    with col_a:
        resumen = ud.resumen_formatos(df_f).dropna(subset=["calif_prom"]).rename_axis("content_type").reset_index()
        if not resumen.empty:
            fig_res = px.bar(
                resumen, x="content_type", y="calif_prom", color="content_type",
                color_discrete_map=COLOR_FORMATO, text="calif_prom",
                labels={"content_type": "", "calif_prom": "Calificación promedio (0–10)"},
                title="Nota promedio por formato",
            )
            fig_res.update_traces(texttemplate="%{text:.2f}", textposition="outside")
            fig_res.update_layout(**LAYOUT_BASE, showlegend=False, yaxis=dict(range=[0, 10]), height=400)
            st.plotly_chart(fig_res, use_container_width=True)
        else:
            st.info("No hay títulos calificados con estos filtros.")

    with col_b:
        por_anio = ud.calif_por_anio(df_f)
        if not por_anio.empty:
            fig_anio = px.line(
                por_anio, x="release_year", y="calif_prom", color="content_type",
                color_discrete_map=COLOR_FORMATO, markers=True,
                category_orders={"content_type": ORDEN_TIPO},
                labels={"release_year": "Año de lanzamiento", "calif_prom": "Calificación promedio (0–10)",
                        "content_type": ""},
                title="Las Series puntúan más, año tras año",
            )
            fig_anio.update_traces(line=dict(width=4), marker=dict(size=8, line=dict(width=1, color=NEGRO)))
            fig_anio.update_layout(
                **LAYOUT_BASE,
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                xaxis=dict(dtick=1), height=400,
            )
            st.plotly_chart(fig_anio, use_container_width=True)
        else:
            st.info("No hay títulos calificados en este rango de años.")
    st.caption(
        "Cómo leerlo: si las dos líneas se cruzaran, la ventaja sería un accidente. No se cruzan en ninguno "
        "de los 16 años. El eje vertical no parte de 0 porque aquí importa la distancia entre las líneas."
    )

    with st.expander("¿Y si las series puntúan alto solo porque tienen pocos votos?"):
        bv = ud.brecha_por_votos(df_catalogo)
        if not bv.empty:
            bv = bv.assign(exigencia=bv["votos_min"].map(etiqueta_votos))
            fig_bv = px.bar(
                bv, x="exigencia", y="brecha", text="brecha",
                labels={"exigencia": "Votos mínimos exigidos a cada título",
                        "brecha": "Diferencia de nota (Series − Películas)"},
                title="La ventaja de las Series se mantiene (y crece) al exigir más votos",
                color_discrete_sequence=[AZUL],
            )
            fig_bv.update_traces(texttemplate="%{text:.2f}", textposition="outside")
            fig_bv.update_layout(**LAYOUT_BASE, showlegend=False, height=360)
            st.plotly_chart(fig_bv, use_container_width=True)
            f50 = ud.fila(bv, "votos_min", 50)
            if f50 is not None:
                st.caption(
                    f"Es una duda razonable: la mitad de las series calificadas tiene menos de 10 votos. "
                    f"Por eso se probó exigiendo más votos: con 50+ votos quedan {miles(f50['n_serie'])} series y "
                    f"{miles(f50['n_pelicula'])} películas, y la diferencia sube a {num(f50['brecha'])} puntos. "
                    f"(Esta comprobación usa siempre el catálogo completo.)"
                )

    with st.expander("¿Por qué no se muestra cuántos títulos hay por año?"):
        st.markdown(
            "Imagina que quieres saber cómo evalúan el casino los alumnos de un colegio y alguien elige "
            "exactamente 1.000 alumnos de cada curso. Si cuentas alumnos por curso, te sale 1.000 en todos, "
            "pero eso no es cuántos alumnos hay: es cuántos eligieron. Aquí pasa lo mismo: cada año tiene "
            "1.000 películas y ~1.000 series porque la muestra se armó así. Por eso **no podemos decir que el "
            "catálogo creció**, pero sí comparar notas y popularidad entre años."
        )

# ---------------------------------------------------------------
# 2. GENEROS
# ---------------------------------------------------------------
with t2:
    encabezado_seccion(
        "¿En qué géneros ocurre?",
        "Solo los 8 géneros que se llaman igual en Películas y Series, para que la comparación sea justa.",
    )
    tg = ud.tabla_generos(df_f, solo_comparables=True)
    tg = tg.assign(genero=tg["genres"].map(ud.es_genero))

    if not tg.empty:
        pv_cal = tg.pivot(index="genres", columns="content_type", values="calif_prom")
        pv_n = tg.pivot(index="genres", columns="content_type", values="titulos")
        if {"Película", "Serie TV"} <= set(pv_cal.columns):
            ambos = pv_cal.dropna(subset=["Película", "Serie TV"])
            gana_nota = int((ambos["Serie TV"] > ambos["Película"]).sum())
            ambos_n = pv_n.reindex(ambos.index)
            gana_vol = int((ambos_n["Serie TV"] >= ambos_n["Película"]).sum())
            respuesta(
                f"En <b>{gana_nota} de {len(ambos)}</b> géneros comparables las Series tienen mejor nota que las "
                f"Películas, y en <b>{gana_vol} de {len(ambos)}</b> tienen igual o más títulos. "
                f"La ventaja de las Series <b>no depende de un género en particular</b>."
            )
        else:
            nota("Para comparar formatos, deja Películas y Series activas en el filtro de tipo de contenido.")

        # Grafico A: nota por genero
        orden_g = (tg.groupby("genero")["calif_prom"].mean().sort_values(ascending=True).index.tolist())
        figa = px.bar(
            tg, x="calif_prom", y="genero", color="content_type", orientation="h", barmode="group",
            color_discrete_map=COLOR_FORMATO, text="calif_prom",
            category_orders={"genero": orden_g, "content_type": ORDEN_TIPO},
            labels={"calif_prom": "Calificación promedio (0–10)", "genero": "", "content_type": ""},
            title="Nota promedio por género: las Series puntúan más en todos",
        )
        figa.update_traces(texttemplate="%{text:.2f}", textposition="outside", cliponaxis=False)
        figa.update_layout(
            **LAYOUT_BASE,
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            xaxis=dict(range=[0, 9]), height=480,
        )
        st.plotly_chart(figa, use_container_width=True)
        st.caption("Cómo leerlo: barras más largas = mejor nota. Cada género tiene un par de barras para comparar.")

        # Grafico B: volumen por genero
        orden_v = (tg.groupby("genero")["titulos"].sum().sort_values(ascending=True).index.tolist())
        figb = px.bar(
            tg, x="titulos", y="genero", color="content_type", orientation="h", barmode="group",
            color_discrete_map=COLOR_FORMATO, text="titulos",
            category_orders={"genero": orden_v, "content_type": ORDEN_TIPO},
            labels={"titulos": "Número de títulos", "genero": "", "content_type": ""},
            title="Cantidad de títulos por género",
        )
        figb.update_traces(texttemplate="%{text:,}", textposition="outside", cliponaxis=False)
        figb.update_layout(
            **LAYOUT_BASE,
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            height=480,
        )
        st.plotly_chart(figb, use_container_width=True)
        st.caption("Cómo leerlo: barras más largas = más títulos. La cantidad por año la fijó la muestra "
                   "(ver pestaña 1), pero la mezcla entre géneros sí es comparable.")
    else:
        st.info("No hay datos de los 8 géneros comparables con estos filtros.")

    st.markdown("---")
    encabezado_seccion(
        "Portafolio: ¿qué géneros combinan buena nota y buena popularidad?",
        "Cada burbuja es un género en un formato; su tamaño indica cuántos títulos hay detrás. "
        "Incluye todos los géneros con al menos 30 títulos.",
    )
    tp = ud.tabla_generos(df_f, solo_comparables=False)
    tp = tp[tp["titulos"] >= 30].dropna(subset=["calif_prom"])
    tp = tp.assign(genero=tp["genres"].map(ud.es_genero))
    if not tp.empty:
        figp = px.scatter(
            tp, x="pop_mediana", y="calif_prom", size="titulos", color="content_type",
            color_discrete_map=COLOR_FORMATO, hover_name="genero", size_max=40,
            category_orders={"content_type": ORDEN_TIPO},
            labels={"pop_mediana": "Popularidad mediana", "calif_prom": "Calificación promedio (0–10)",
                    "content_type": "", "titulos": "N.º de títulos"},
            title="Arriba = mejor nota · A la derecha = más popular",
        )
        figp.update_traces(marker=dict(line=dict(width=1, color=NEGRO)))
        calif_df = ud.calificados(df_f)
        if len(calif_df):
            figp.add_hline(
                y=float(calif_df["vote_average"].mean()), line_dash="dot", line_color=GRIS_TEXTO,
                annotation_text="Promedio de la selección", annotation_position="bottom right",
                annotation_font_size=10,
            )
        figp.update_layout(
            **LAYOUT_BASE,
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            height=500,
        )
        st.plotly_chart(figp, use_container_width=True)
        st.caption("Cómo leerlo: los géneros arriba a la derecha son los mejores en nota y popularidad. "
                   "Pasa el cursor sobre una burbuja para ver el género.")
    else:
        st.info("No hay suficientes títulos por género con estos filtros (se necesitan al menos 30).")

# ---------------------------------------------------------------
# 3. POPULAR VS. BUENO
# ---------------------------------------------------------------
with t3:
    encabezado_seccion(
        "¿Lo más popular es también lo mejor evaluado?",
        "Si fuera así, bastaría con mirar una sola métrica para decidir.",
    )
    rho, n_rho = ud.correlacion_pop_calif(df_f)
    fuerza = ud.fuerza_correlacion(rho)
    if rho is not None:
        explicacion = {
            "muy débil": "casi no se relacionan: que un título sea popular no dice nada sobre su nota.",
            "débil": "se relacionan poco: un título popular tiende a tener algo mejor nota, pero hay muchas excepciones.",
            "moderada": "se relacionan en parte: los populares suelen tener mejor nota, pero hay muchísimas excepciones "
                        "(populares con nota baja y títulos excelentes poco populares).",
            "fuerte": "van muy de la mano: los más populares casi siempre son los mejor evaluados.",
        }[fuerza]
        cierre = ("Por eso <b>no conviene decidir con una sola métrica</b>." if fuerza != "fuerte"
                  else "En esta selección, una sola métrica daría casi la misma respuesta que la otra.")
        respuesta(
            f"En esta selección, popularidad y nota <b>{explicacion}</b> "
            f"(relación ρ = <b>{num(rho)}</b>, “{fuerza}”). {cierre}"
        )
        st.metric("Relación popularidad ↔ nota (ρ)", num(rho),
                  help="Va de −1 a 1. Cerca de 0 = casi no se relacionan. Se calcula por posiciones "
                       "(ranking), así que los títulos extremadamente populares no la distorsionan.")
    else:
        nota("No hay suficientes títulos calificados para medir la relación con estos filtros.")

    dispersion = ud.calificados(df_f)
    if len(dispersion) > 0:
        fig_d = px.scatter(
            dispersion, x="popularity", y="vote_average", color="content_type",
            color_discrete_map=COLOR_FORMATO, log_x=True, opacity=0.5, render_mode="webgl",
            hover_name="title",
            hover_data={"content_type": True, "vote_count": ":,", "popularity": ":.1f", "vote_average": ":.2f"},
            category_orders={"content_type": ORDEN_TIPO},
            labels={"popularity": "Popularidad (escala logarítmica)",
                    "vote_average": "Calificación de audiencia (0–10)", "content_type": ""},
            title="Cada punto es un título",
        )
        fig_d.update_traces(marker=dict(size=6))
        fig_d.update_layout(
            **LAYOUT_BASE,
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            yaxis=dict(range=[0, 10.3]), height=500,
        )
        st.plotly_chart(fig_d, use_container_width=True)
        st.caption(
            "Cómo leerlo: si lo popular fuera lo mejor, los puntos formarían una línea que sube de izquierda a "
            "derecha. Aquí forman una nube ancha. La escala logarítmica (cada marca multiplica por 10) evita que "
            "unos pocos títulos extremadamente populares aplasten al resto."
        )

    with st.expander("¿Por qué la cifra cambia según los votos mínimos?"):
        cv = ud.correlacion_por_votos(df_catalogo)
        if not cv.empty:
            tabla_cv = cv.assign(
                **{"Votos mínimos": cv["votos_min"].map(etiqueta_votos),
                   "Títulos": cv["titulos"].map(miles),
                   "Relación (ρ)": cv["rho"].map(num),
                   "Fuerza": cv["rho"].map(ud.fuerza_correlacion)}
            )[["Votos mínimos", "Títulos", "Relación (ρ)", "Fuerza"]]
            st.dataframe(tabla_cv, hide_index=True, use_container_width=True)
        st.markdown(
            "Una nota que viene de 3 votos es puro ruido, y ese ruido tapa cualquier relación. Cuando se "
            "exige más votos, la relación aparece con más claridad. Por eso hay que decir siempre **con qué "
            "mínimo de votos** se calculó. (Tabla calculada sobre el catálogo completo.)"
        )

# ---------------------------------------------------------------
# 4. PAISES E IDIOMAS
# ---------------------------------------------------------------
with t4:
    encabezado_seccion(
        "¿De dónde viene el contenido y qué países destacan?",
        "Series TV: los 10 países con más títulos, con su nota promedio. Más abajo, los idiomas.",
    )
    tpa = ud.tabla_paises_series(df_f, 10)
    if tpa.empty:
        st.info("Este gráfico analiza Series TV. Activa “Serie TV” en el filtro de tipo de contenido.")
    else:
        mejor = tpa.dropna(subset=["calif_prom"]).sort_values("calif_prom", ascending=False).head(2)
        if len(mejor) == 2:
            a, b = mejor.iloc[0], mejor.iloc[1]
            respuesta(
                f"Entre los 10 países con más series, <b>{ud.es_pais(a['country'])}</b> ({num(a['calif_prom'])}) y "
                f"<b>{ud.es_pais(b['country'])}</b> ({num(b['calif_prom'])}) tienen la <b>mejor nota</b>. "
                f"Ojo: la nota de un país solo es sólida si tiene muchos títulos con votos (ver el detalle al pasar el cursor)."
            )
        tpa = tpa.sort_values("titulos", ascending=True).assign(pais=lambda d: d["country"].map(ud.es_pais))
        fig_p = px.bar(
            tpa, x="titulos", y="pais", color="calif_prom", color_continuous_scale=ESCALA_SERIE,
            orientation="h", text="titulos",
            category_orders={"pais": tpa["pais"].tolist()},
            hover_data={"titulos_50_votos": True, "calif_prom": ":.2f", "pais": False},
            labels={"titulos": "Número de series", "pais": "", "calif_prom": "Nota<br>promedio",
                    "titulos_50_votos": "Títulos con 50+ votos"},
            title=f"Top {len(tpa)} países por cantidad de Series TV",
        )
        fig_p.update_traces(texttemplate="%{text:,}", textposition="outside", cliponaxis=False)
        fig_p.update_layout(**LAYOUT_BASE, coloraxis_colorbar=dict(title="Nota<br>promedio", tickformat=".1f"),
                            height=470)
        st.plotly_chart(fig_p, use_container_width=True)
        st.caption("Cómo leerlo: el largo de la barra es la cantidad de series; el color, la nota (más oscuro = "
                   "mejor). Al pasar el cursor verás cuántas de esas series tienen 50 votos o más.")

    st.markdown("---")
    encabezado_seccion("¿Qué idiomas tienen más presencia?", "Porcentaje de títulos por idioma original, en la selección actual.")
    ti = ud.tabla_idiomas(df_f, 8)
    if not ti.empty:
        ti = ti.sort_values("porcentaje", ascending=True)
        fig_i = px.bar(
            ti, x="porcentaje", y="idioma", orientation="h", text="porcentaje",
            category_orders={"idioma": ti["idioma"].tolist()},
            labels={"porcentaje": "% de los títulos", "idioma": ""},
            title="El inglés domina, pero chino, japonés y coreano pesan mucho",
            color_discrete_sequence=[AZUL],
        )
        fig_i.update_traces(texttemplate="%{text:.1f}%", textposition="outside", cliponaxis=False)
        fig_i.update_layout(**LAYOUT_BASE, showlegend=False, height=400)
        st.plotly_chart(fig_i, use_container_width=True)
        top3 = ti[ti["language"].isin(["zh", "ja", "ko"])]["porcentaje"].sum()
        st.caption(f"Chino, japonés y coreano suman {num(top3, 1)}% de los títulos de la selección.")

# ---------------------------------------------------------------
# 5. FINANZAS
# ---------------------------------------------------------------
with t5:
    encabezado_seccion(
        "¿Cuánto rinden las películas?",
        "Solo películas que informan presupuesto e ingresos (alrededor de 1 de cada 5). Las series no tienen estos datos.",
    )
    ids_pel = df_f.loc[df_f["content_type"] == "Película", "id_unico"]
    if len(ids_pel) == 0:
        st.info("Esta pestaña analiza Películas. Activa “Película” en el filtro de tipo de contenido.")
    else:
        fin = ud.datos_financieros(df_movies, ids=ids_pel)
        if fin.empty:
            st.info("Ninguna película de esta selección informa presupuesto e ingresos.")
        else:
            roi_med = float(fin["roi"].median())
            pct_recupera = float((fin["roi"] > 1).mean() * 100)
            rg = ud.roi_por_genero(fin, 60)

            if not rg.empty:
                top = rg.iloc[0]
                respuesta(
                    f"La película mediana recauda <b>{num(roi_med, 1)} veces</b> lo que costó, y "
                    f"<b>{pct_recupera:.0f}%</b> recupera su presupuesto. El género con mayor retorno mediano es "
                    f"<b>{ud.es_genero(top['genres'])}</b> ({num(top['roi_mediano'], 1)}×), con un presupuesto "
                    f"mediano de US$ {num(top['presupuesto_mediano'] / 1e6, 1)} millones."
                )
            f1, f2, f3 = st.columns(3)
            f1.metric("Películas con datos financieros", miles(len(fin)),
                      help=f"{len(fin) / len(ids_pel) * 100:.0f}% de las películas de la selección.")
            f2.metric("Retorno mediano (ROI)", f"{num(roi_med, 1)}×",
                      help="Ingresos ÷ presupuesto. 2× = recaudó el doble de lo que costó.")
            f3.metric("Recuperan su presupuesto", f"{pct_recupera:.0f}%",
                      help="Porcentaje de películas con ROI mayor a 1.")

            if not rg.empty:
                rg = rg.sort_values("roi_mediano", ascending=True).assign(
                    genero=lambda d: d["genres"].map(ud.es_genero))
                fig_r = px.bar(
                    rg, x="roi_mediano", y="genero", orientation="h", text="roi_mediano",
                    category_orders={"genero": rg["genero"].tolist()},
                    hover_data={"titulos": True, "presupuesto_mediano": ":,.0f", "genero": False},
                    labels={"roi_mediano": "Retorno mediano (veces el presupuesto)", "genero": "",
                            "titulos": "Películas con datos", "presupuesto_mediano": "Presupuesto mediano (US$)"},
                    title="Retorno mediano por género (películas)",
                    color_discrete_sequence=[AMARILLO],
                )
                fig_r.update_traces(texttemplate="%{text:.1f}×", textposition="outside", cliponaxis=False,
                                    marker_line_color=NEGRO, marker_line_width=1)
                fig_r.update_layout(**LAYOUT_BASE, showlegend=False, height=480)
                st.plotly_chart(fig_r, use_container_width=True)
                st.caption("Cómo leerlo: barras más largas = más dinero recaudado por cada dólar invertido. "
                           "Solo géneros con al menos 60 películas con datos.")

            fig_s = px.scatter(
                fin, x="budget", y="revenue", log_x=True, log_y=True, opacity=0.55,
                hover_name="title",
                hover_data={"release_year": True, "budget": ":,.0f", "revenue": ":,.0f", "roi": ":.1f"},
                labels={"budget": "Presupuesto (US$, escala logarítmica)",
                        "revenue": "Ingresos (US$, escala logarítmica)", "release_year": "Año", "roi": "ROI"},
                title="Más presupuesto suele traer más ingresos, pero con mucha dispersión",
                color_discrete_sequence=[AMARILLO],
            )
            fig_s.update_traces(marker=dict(size=7, line=dict(width=0.5, color=NEGRO)))
            lo = float(min(fin["budget"].min(), fin["revenue"].min()))
            hi = float(max(fin["budget"].max(), fin["revenue"].max()))
            fig_s.add_scatter(x=[lo, hi], y=[lo, hi], mode="lines", name="Ingresos = presupuesto",
                              line=dict(color=AZUL, dash="dot", width=2), hoverinfo="skip")
            fig_s.update_layout(**LAYOUT_BASE, showlegend=True,
                                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                                height=500)
            st.plotly_chart(fig_s, use_container_width=True)
            st.caption("Cómo leerlo: los puntos sobre la línea punteada recaudaron más de lo que costaron; los "
                       "que están debajo, perdieron dinero (en bruto).")

            with st.expander("¿Cómo se calcula y qué limitaciones tiene?"):
                st.markdown(
                    f"- **ROI** = ingresos ÷ presupuesto. Es un retorno **bruto**: no descuenta marketing ni el "
                    f"reparto con las salas.\n"
                    f"- Solo se usan películas con presupuesto **e** ingresos de al menos US$ {miles(ud.UMBRAL_FINANCIERO)}; "
                    f"valores menores son simbólicos y dan retornos absurdos.\n"
                    f"- Solo ~1 de cada 5 películas informa estos datos, así que el resultado describe a las películas "
                    f"que sí los informan, no a todo el catálogo.\n"
                    f"- Se usa la **mediana**: unas pocas películas con retornos gigantes distorsionarían el promedio."
                )

# ---------------------------------------------------------------
# 6. QUE DECIDIR
# ---------------------------------------------------------------
with t6:
    encabezado_seccion(
        "¿Qué decisiones se desprenden de los datos?",
        "Cuatro decisiones para el Comité. Todas las cifras de esta pestaña usan el catálogo completo (sin filtros).",
    )
    H = calcular_hallazgos(df_catalogo, df_movies)
    KB = H["kpis"]

    sg, pg, paises = H["series_generos"], H["pel_generos"], H["paises"]
    ref = lambda g: ud.fila(sg, "genres", g)  # noqa: E731
    aa, sf, an = ref("Action & Adventure"), ref("Sci-Fi & Fantasy"), ref("Animation")
    japon, china, corea = (ud.fila(paises, "country", c) for c in ("Japan", "China", "South Korea"))

    # --- 1. Series
    partes = []
    for etq, f in (("Acción y Aventura", aa), ("Sci-Fi y Fantasía", sf), ("Animación", an)):
        if f is not None:
            partes.append(f"{etq}: nota {num(f['calif_prom'])} con {miles(f['titulos'])} series")
    mercados = []
    if japon is not None:
        mercados.append(f"Japón (nota {num(japon['calif_prom'])}, {miles(japon['titulos_50_votos'])} series con 50+ votos)")
    if china is not None:
        mercados.append(f"China (nota {num(china['calif_prom'])}, pero solo {miles(china['titulos_50_votos'])} series con 50+ votos)")
    ojo_corea = ""
    if corea is not None:
        ojo_corea = (f" Corea del Sur tiene mucho volumen ({miles(corea['titulos'])} series) pero su nota "
                     f"({num(corea['calif_prom'])}) queda bajo el promedio de las series ({num(KB['calif_serie'])}): "
                     f"conviene mirarla con más votos antes de apostar.")
    tarjeta_reco(
        "1 · Apostar por las Series",
        "Reorientar el mix hacia Series, priorizando Acción y Aventura, Sci-Fi y Fantasía y Animación, "
        "y mirando primero Japón y China como mercados.",
        f"Las Series puntúan {num(KB['calif_serie'])} vs. {num(KB['calif_pelicula'])} de las Películas "
        f"(+{num(KB['brecha'])}), todos los años y en los 8 géneros comparables. Los tres géneros: "
        f"{'; '.join(partes)}. Mercados: {' y '.join(mercados)}.",
        "Los datos no distinguen series originales de licenciadas: hablamos del formato Serie, no de producción "
        f"propia. La nota alta de China descansa en pocos títulos con votos.{ojo_corea}",
    )

    # --- 2. Documental
    doc_p = ud.fila(pg, "genres", "Documentary")
    doc_s = ud.fila(sg, "genres", "Documentary")
    mejor_pel = pg.iloc[0] if len(pg) else None
    es_mejor = mejor_pel is not None and mejor_pel["genres"] == "Documentary"
    if doc_p is not None:
        menos_pop = (1 - doc_p["pop_mediana"] / H["pop_mediana_peliculas"]) * 100
        extra_s = f" En formato serie, el documental puntúa {num(doc_s['calif_prom'])}." if doc_s is not None else ""
        tarjeta_reco(
            "2 · Proteger el Documental como nicho de calidad",
            "Mantener la inversión en documentales y evaluarla con métricas de calidad, no de alcance masivo.",
            f"Documental es {'el género de película mejor evaluado' if es_mejor else 'uno de los géneros de película mejor evaluados'} "
            f"(nota {num(doc_p['calif_prom'])}) pero su popularidad mediana ({num(doc_p['pop_mediana'], 1)}) es "
            f"{menos_pop:.0f}% menor que la de la película típica ({num(H['pop_mediana_peliculas'], 1)}).{extra_s}",
            "Es un nicho: no esperar audiencias masivas. Si se mide solo por popularidad, parecerá un mal negocio.",
        )

    # --- 3. Horror
    hor = ud.fila(pg, "genres", "Horror")
    rg_h = H["roi_generos"]
    roi_h = ud.fila(rg_h, "genres", "Horror")
    if hor is not None:
        peor_pel = pg.sort_values("calif_prom").iloc[0]
        es_peor = peor_pel["genres"] == "Horror"
        if roi_h is not None and H["roi_global"]:
            posicion = int(list(rg_h["genres"]).index("Horror")) + 1
            fin_txt = (f"En retorno financiero, en cambio, Horror es el puesto {posicion} de {len(rg_h)} géneros: "
                       f"{num(roi_h['roi_mediano'], 1)}× de retorno mediano vs. {num(H['roi_global'], 1)}× de la película "
                       f"típica, con un presupuesto mediano de US$ {num(roi_h['presupuesto_mediano'] / 1e6, 1)} millones.")
        else:
            fin_txt = "No hay suficientes datos financieros para evaluar su retorno."
        tarjeta_reco(
            "3 · No juzgar al Horror por su nota",
            "Evaluar el Horror por retorno y costo, no por calificación: mantenerlo como producción de bajo costo, "
            "sin esperar prestigio.",
            f"Horror tiene {miles(hor['titulos'])} películas y {'la nota más baja' if es_peor else 'una de las notas más bajas'} "
            f"({num(hor['calif_prom'])}). {fin_txt}",
            f"Solo {H['fin_cobertura'] * 100:.0f}% de las películas informa presupuesto e ingresos, y el retorno es "
            f"bruto (sin marketing). Es una señal fuerte, pero no una garantía.",
        )

    # --- 4. KPI compuesto
    rho_t, rho_50 = H["rho_todos"], H["rho_50"]
    if rho_t is not None and rho_50 is not None:
        tarjeta_reco(
            "4 · Decidir con dos métricas, no con una",
            "Usar un indicador compuesto (posición en popularidad + posición en nota) para las decisiones de luz verde.",
            f"Popularidad y nota se relacionan solo en parte: ρ = {num(rho_t)} con todos los títulos y "
            f"{num(rho_50)} exigiendo 50+ votos. Hay muchos títulos populares con nota baja y muchos muy bien "
            f"evaluados poco populares; mirar una sola métrica deja fuera a unos u otros.",
            "El índice de abajo es un ejemplo de cálculo, no una fórmula oficial: el peso de cada métrica "
            "(hoy 50/50) es una decisión del negocio.",
        )

    st.markdown("**Ejemplo del indicador compuesto: los 10 títulos con mejor combinación** (mínimo 50 votos)")
    top_idx = ud.indice_compuesto(df_catalogo, votos_min=50, n=10)
    if not top_idx.empty:
        vista = top_idx.rename(columns={
            "title": "Título", "content_type": "Tipo", "release_year": "Año",
            "popularity": "Popularidad", "vote_average": "Nota", "vote_count": "Votos", "indice": "Índice (0–100)",
        })
        vista["Popularidad"] = vista["Popularidad"].round(1)
        vista["Nota"] = vista["Nota"].round(2)
        vista["Índice (0–100)"] = vista["Índice (0–100)"].round(1)
        st.dataframe(vista, hide_index=True, use_container_width=True)
        st.caption("Índice = promedio de la posición (percentil) del título en popularidad y en nota, "
                   "entre los títulos con 50+ votos.")

# ---------------------------------------------------------------
# EXPLORAR DATOS
# ---------------------------------------------------------------
with t7:
    encabezado_seccion(
        "Explorador del catálogo filtrado",
        "La tabla detrás de los gráficos: ordenable y descargable. Respeta los filtros del panel lateral.",
    )
    columnas_mostrar = {
        "title": "Título", "content_type": "Tipo", "release_year": "Año",
        "country": "País", "genres": "Género(s)", "language": "Idioma",
        "popularity": "Popularidad", "vote_count": "Votos", "vote_average": "Calificación",
    }
    tabla = (
        df_f[list(columnas_mostrar.keys())]
        .rename(columns=columnas_mostrar)
        .sort_values("Popularidad", ascending=False)
    )
    tabla["Popularidad"] = tabla["Popularidad"].round(1)
    tabla["Calificación"] = tabla["Calificación"].round(2)

    st.dataframe(
        tabla, use_container_width=True, height=460, hide_index=True,
        column_config={
            "Popularidad": st.column_config.NumberColumn(format="%.1f"),
            "Calificación": st.column_config.ProgressColumn(format="%.2f", min_value=0, max_value=10),
            "Votos": st.column_config.NumberColumn(format="%d"),
        },
    )
    st.caption(f"{miles(len(tabla))} títulos con los filtros actuales. Calificación 0 = sin calificación.")

    st.download_button(
        "Descargar selección actual (CSV)",
        data=tabla.to_csv(index=False).encode("utf-8"),
        file_name="streamview_catalogo_filtrado.csv",
        mime="text/csv",
    )

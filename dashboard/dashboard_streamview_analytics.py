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
try:
    import infografia as ig  # noqa: E402
except ImportError:  # falta matplotlib u otro modulo
    ig = None
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

        /* ---- Pregunta que responde cada grafico ---- */
        .pregunta {{
            font-size: 12.5px; font-weight: 700; letter-spacing: 0.04em; text-transform: uppercase;
            color: {AZUL}; margin: 10px 0 2px 0;
        }}
        .pregunta span {{ color: {GRIS_TEXTO}; font-weight: 600; text-transform: none; letter-spacing: 0; }}

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


def pregunta(texto):
    """Etiqueta con la pregunta que responde el grafico de abajo (la misma del notebook)."""
    st.markdown(f'<div class="pregunta">Pregunta del gráfico · <span>{texto}</span></div>', unsafe_allow_html=True)


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
# Mismo catalogo con el umbral de confiabilidad (50+ votos), el que usan las recomendaciones y los paises
BASE50 = ud.kpis(df_catalogo[df_catalogo["vote_count"] >= ud.VOTOS_CONFIABLE])

# ============================================================
# BARRA LATERAL: FILTROS Y GLOSARIO
# ============================================================
st.sidebar.header("Filtros")
st.sidebar.markdown(
    '<p style="opacity:0.8; margin-top:-6px;">Cambia estos controles y se recalculan los '
    'indicadores y los gráficos (excepto la pestaña “Qué decidir”, que usa siempre el catálogo completo).</p>',
    unsafe_allow_html=True,
)

anio_min, anio_max = st.sidebar.slider(
    "Año de lanzamiento", min_value=2010, max_value=2025, value=(2010, 2025),
    help="El catálogo cubre 2010–2025.",
)
votos_min = st.sidebar.select_slider(
    "Mínimo de votos acumulados", options=[0, 10, 25, 50, 100, 200, 500, 1000], value=0,
    help=(
        "Una nota basada en pocos votos es poco confiable, y los estrenos recientes aún no "
        "juntan votos. Sube este filtro para quedarte con títulos validados por más gente. "
        f"{ud.VOTOS_CONFIABLE} votos es el umbral que usan las recomendaciones y la comparación de países."
    ),
)
generos_disponibles = sorted(ud.explode_columna(df_catalogo, "genres")["genres"].dropna().unique())
generos_sel = st.sidebar.multiselect(
    "Géneros (vacío = todos)", options=generos_disponibles, default=[],
    format_func=ud.etiqueta_genero, placeholder="Ej.: Animación, Drama",
    help=("Al elegir uno o más géneros, todo se recalcula solo con esos títulos. "
          "★ = género que existe en Películas y en Series (los 8 que se pueden comparar entre formatos). "
          "Los demás son de un solo formato, por ejemplo «Acción y Aventura» (Series) o «Acción» (Películas)."),
)
VOL_PAISES = ud.paises_por_volumen(df_catalogo)
paises_sel = st.sidebar.multiselect(
    "Países de producción (vacío = todos)", options=VOL_PAISES.index.tolist(), default=[],
    format_func=ud.es_pais,
    placeholder="Ej.: Corea del Sur, Japón",
    help=("Ordenados de mayor a menor cantidad de títulos. Al elegir uno o más países, "
          "todo se recalcula solo con sus títulos. Una coproducción entra si alguno de sus países está elegido. "
          "Sirve para revisar los mercados de la recomendación 2 (pestaña 6)."),
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

# ============================================================
# FILTRO PRINCIPAL: PELICULAS / SERIES (visible arriba, no escondido en el panel)
# ============================================================
st.markdown("##### ¿Qué quieres ver?")
vista = st.radio(
    "Formato", ["Todo el catálogo", "Solo Películas", "Solo Series TV"], horizontal=True,
    key="vista_tipo", label_visibility="collapsed",
    help="Filtra todo el dashboard (excepto la pestaña 6) por formato. Los demás filtros están en el panel izquierdo.",
)
tipos_sel = {"Todo el catálogo": ORDEN_TIPO, "Solo Películas": ["Película"], "Solo Series TV": ["Serie TV"]}[vista]
un_formato = len(tipos_sel) == 1

df_f = ud.aplicar_filtros(df_catalogo, tipos_sel, anio_min, anio_max, votos_min, generos_sel, paises_sel)

if df_f.empty:
    st.warning(
        "No hay títulos con esta combinación de filtros. Prueba bajando el mínimo de votos, "
        "ampliando el rango de años o quitando algún país o género."
    )
    st.stop()

_activos = []
if generos_sel:
    _activos.append("géneros: " + ", ".join(ud.es_genero(g) for g in generos_sel))
if paises_sel:
    _activos.append("países: " + ", ".join(ud.es_pais(p) for p in paises_sel))
if votos_min > 0:
    _activos.append(f"{votos_min}+ votos")
st.caption(
    f"Mostrando **{miles(len(df_f))}** de {miles(len(df_catalogo))} títulos "
    f"({len(df_f) / len(df_catalogo) * 100:.0f}% del catálogo)"
    + (f" · Filtros activos: {' · '.join(_activos)}." if _activos else ".")
)

with st.expander("¿Cómo leer este dashboard?"):
    st.markdown(
        """
Cada pestaña responde **una pregunta** y empieza con la **respuesta corta** (caja amarilla).
Debajo está la evidencia. El orden es: **1** qué ocurre → **2** en qué géneros → **3** si lo popular
es lo bueno → **4** de dónde viene el contenido → **5** cuánto rinden las películas →
**6** qué decidir. El selector «¿Qué quieres ver?» y los filtros del panel izquierdo recalculan todo menos la pestaña 6.
        """
    )

# ============================================================
# KPIs
# ============================================================
K = ud.kpis(df_f)
if un_formato:
    cal = ud.calificados(df_f)
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Títulos en el filtro", miles(K["n"]),
              help=f"Títulos que cumplen los filtros, sobre {miles(len(df_catalogo))} del catálogo.")
    c2.metric("Calificación promedio", f"{num(cal['vote_average'].mean())} / 10" if len(cal) else "—",
              help="Nota promedio de los títulos con calificación real.")
    c3.metric("Popularidad mediana", num(df_f["popularity"].median(), 1),
              help="Índice relativo de interés; sirve para comparar, no es cantidad de reproducciones.")
    c4.metric("Votos por título (mediana)", miles(df_f["vote_count"].median()),
              help="Cuánta gente calificó un título típico: más votos = nota más confiable.")
    st.caption("Estás viendo un solo formato, por eso se ocultan las comparaciones Series vs. Películas. "
               "Para compararlos, vuelve a «Todo el catálogo».")
else:
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Títulos en el filtro", miles(K["n"]),
              help=f"Títulos que cumplen los filtros, sobre {miles(len(df_catalogo))} del catálogo.")
    c2.metric("Calificación Películas", f"{num(K['calif_pelicula'])} / 10" if K["calif_pelicula"] is not None else "—",
              help="Nota promedio de las películas con calificación real.")
    c3.metric("Calificación Series TV", f"{num(K['calif_serie'])} / 10" if K["calif_serie"] is not None else "—",
              help="Nota promedio de las series con calificación real.")
    _b50 = ud.brecha_por_votos(df_f, umbrales=(ud.VOTOS_CONFIABLE,))
    c4.metric("Diferencia (Series − Películas)", con_signo(K["brecha"]) if K["brecha"] is not None else "—",
              delta=(f"{con_signo(_b50.iloc[0]['brecha'])} con {ud.VOTOS_CONFIABLE}+ votos" if len(_b50) else None),
              delta_color="off",
              help=("Puntos de nota que las Series le sacan a las Películas con los filtros actuales. Debajo, la misma "
                    f"diferencia contando solo títulos con {ud.VOTOS_CONFIABLE}+ votos: es la cifra que usa la recomendación "
                    "y el mismo umbral que se exige para comparar países."))
    c5.metric("Popularidad Series ÷ Películas",
              f"{num(K['pop_veces'], 1)}×" if K["pop_veces"] is not None else "—",
              help="Cuántas veces mayor es la popularidad mediana de las Series frente a las Películas.")

# ============================================================
# PESTANAS
# ============================================================
t1, t2, t3, t4, t5, t6, t8, t7 = st.tabs([
    "1. La historia", "2. Géneros", "3. Popular vs. bueno",
    "4. Países e idiomas", "5. Finanzas", "6. Qué decidir", "7. Infografía", "Explorar datos",
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
        a_favor = "las Series" if K["brecha"] >= 0 else "las Películas"
        aviso_votos = ""
        if votos_min < ud.VOTOS_CONFIABLE:
            aviso_votos = (f" Ojo: esta cifra incluye títulos con menos de {ud.VOTOS_CONFIABLE} votos, cuya nota es poco "
                           f"confiable. Sube el «Mínimo de votos» a {ud.VOTOS_CONFIABLE} para ver la cifra que usa la recomendación.")
        respuesta(
            f"Con el umbral de confiabilidad que usamos también para comparar países (<b>{ud.VOTOS_CONFIABLE}+ votos</b> "
            f"por título), las Series TV tienen una nota de <b>{num(BASE50['calif_serie'])}</b> y las Películas de "
            f"<b>{num(BASE50['calif_pelicula'])}</b> en el catálogo completo: <b>{num(BASE50['brecha'])} puntos</b> a favor "
            f"de las Series, y la ventaja se repite <b>los 16 años</b>.<br>"
            f"<b>En esta selección</b> ({'sin mínimo de votos' if votos_min == 0 else f'{votos_min}+ votos'}): Series <b>{num(K['calif_serie'])}</b>, "
            f"Películas <b>{num(K['calif_pelicula'])}</b>, <b>{num(abs(K['brecha']))} puntos</b> a favor de {a_favor}."
            f"{aviso_votos}"
        )
    else:
        nota("Para comparar Series y Películas, elige «Todo el catálogo» en «¿Qué quieres ver?»"
             ".")

    col_a, col_b = st.columns([1, 2])

    with col_a:
        pregunta("¿Qué formato se califica mejor?")
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
            st.plotly_chart(fig_res, width="stretch")
        else:
            st.info("No hay títulos calificados con estos filtros.")

    with col_b:
        pregunta("¿Ocurre todos los años?")
        por_anio = ud.calif_por_anio(df_f, ud.MIN_TITULOS_ANIO, ud.VOTOS_ANIO)
        _pv = por_anio.pivot(index="release_year", columns="content_type", values="calif_prom")
        if {"Película", "Serie TV"} <= set(_pv.columns):
            _pv = _pv.dropna(subset=["Película", "Serie TV"])
            anios_comp = len(_pv)
            anios_serie = int((_pv["Serie TV"] > _pv["Película"]).sum())
        else:
            anios_comp = anios_serie = 0
        if anios_comp <= 1:
            titulo_anio = "Nota promedio por año"
        elif anios_serie == anios_comp:
            titulo_anio = f"Las Series puntúan más en los {anios_comp} años comparables"
        elif anios_serie == 0:
            titulo_anio = f"Las Películas puntúan más en los {anios_comp} años comparables"
        else:
            titulo_anio = f"Las Series puntúan más en {anios_serie} de {anios_comp} años"
        if not por_anio.empty:
            fig_anio = px.line(
                por_anio, x="release_year", y="calif_prom", color="content_type",
                color_discrete_map=COLOR_FORMATO, markers=True,
                category_orders={"content_type": ORDEN_TIPO},
                labels={"release_year": "Año de lanzamiento", "calif_prom": "Calificación promedio (0–10)",
                        "content_type": ""},
                title=titulo_anio,
            )
            fig_anio.update_traces(line=dict(width=4), marker=dict(size=8, line=dict(width=1, color=NEGRO)))
            fig_anio.update_layout(
                **LAYOUT_BASE,
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                xaxis=dict(dtick=1), height=400,
            )
            st.plotly_chart(fig_anio, width="stretch")
        else:
            st.info(f"Con estos filtros ningún año tiene al menos {ud.MIN_TITULOS_ANIO} títulos con {ud.VOTOS_ANIO}+ votos por formato, "
                    "así que no se dibuja la evolución (el promedio de pocos títulos es ruido).")
    if anios_comp == 1:
        st.caption("Con estos filtros solo hay un año comparable: no se puede hablar de una tendencia. "
                   f"Solo cuentan títulos con {ud.VOTOS_ANIO}+ votos y años con {ud.MIN_TITULOS_ANIO}+ títulos así por formato.")
    elif anios_comp:
        if anios_serie == anios_comp:
            lectura_anio = (f"En esta selección las líneas no se cruzan en ninguno de los {anios_comp} años comparables: "
                            "la ventaja de las Series no es un accidente de un año.")
        elif anios_serie == 0:
            lectura_anio = (f"En esta selección las Películas puntúan más en los {anios_comp} años comparables.")
        else:
            lectura_anio = (f"En esta selección las líneas se cruzan: las Series puntúan más en {anios_serie} de "
                            f"{anios_comp} años, así que aquí la ventaja no es estable.")
        st.caption(
            "Cómo leerlo: si las dos líneas se cruzaran, la ventaja sería un accidente. "
            f"{lectura_anio} Solo cuentan títulos con {ud.VOTOS_ANIO}+ votos (los estrenos recientes aún tienen muy "
            f"pocos y bajarían el último año sin ser una tendencia) y se omiten los años con menos de "
            f"{ud.MIN_TITULOS_ANIO} títulos así por formato. El eje vertical no parte de 0 porque aquí importa la distancia entre las líneas."
        )
    else:
        st.caption(f"Solo cuentan títulos con {ud.VOTOS_ANIO}+ votos y se omiten los años con menos de "
                   f"{ud.MIN_TITULOS_ANIO} títulos así por formato, porque su promedio es ruido.")

    pregunta("¿La ventaja depende de las series con pocos votos?")
    bv = ud.brecha_por_votos(df_catalogo)
    if not bv.empty:
        bv = bv.assign(exigencia=bv["votos_min"].map(etiqueta_votos))
        bv["umbral"] = bv["votos_min"].eq(ud.VOTOS_CONFIABLE).map(
            {True: f"Umbral de la recomendación ({ud.VOTOS_CONFIABLE}+ votos)", False: "Otros mínimos"})
        fig_bv = px.bar(
            bv, x="exigencia", y="brecha", text="brecha", color="umbral",
            color_discrete_map={f"Umbral de la recomendación ({ud.VOTOS_CONFIABLE}+ votos)": AZUL,
                                "Otros mínimos": GRIS_LINEA},
            category_orders={"exigencia": bv["exigencia"].tolist()},
            labels={"exigencia": "Votos mínimos exigidos a cada título",
                    "brecha": "Diferencia de nota (Series − Películas)", "umbral": ""},
            title="La ventaja de las Series se mantiene y crece al exigir más votos",
        )
        fig_bv.update_traces(texttemplate="%{text:.2f}", textposition="outside", cliponaxis=False)
        fig_bv.update_layout(**LAYOUT_BASE, height=360,
                             legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
        st.plotly_chart(fig_bv, width="stretch")
        f0, f50 = ud.fila(bv, "votos_min", 0), ud.fila(bv, "votos_min", ud.VOTOS_CONFIABLE)
        if f0 is not None and f50 is not None:
            st.caption(
                f"Cómo leerlo: la mitad de las series calificadas tiene menos de 10 votos, y su nota es ruido. "
                f"Por eso la recomendación usa {ud.VOTOS_CONFIABLE}+ votos, el mismo umbral que la comparación de países: "
                f"quedan {miles(f50['n_serie'])} series y {miles(f50['n_pelicula'])} películas, y la diferencia es de "
                f"{num(f50['brecha'])} puntos (sin mínimo era {num(f0['brecha'])}). Exigir votos no crea la ventaja: la aumenta. "
                f"(Este gráfico usa siempre el catálogo completo.)"
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

    titulo_generos = "Nota promedio por género comparable"
    if not tg.empty:
        pv_cal = tg.pivot(index="genres", columns="content_type", values="calif_prom")
        pv_n = tg.pivot(index="genres", columns="content_type", values="titulos")
        if {"Película", "Serie TV"} <= set(pv_cal.columns):
            ambos = pv_cal.dropna(subset=["Película", "Serie TV"])
            gana_nota = int((ambos["Serie TV"] > ambos["Película"]).sum())
            ambos_n = pv_n.reindex(ambos.index)
            gana_vol = int((ambos_n["Serie TV"] >= ambos_n["Película"]).sum())
            if len(ambos) and gana_nota == len(ambos):
                titulo_generos = f"Nota promedio por género: las Series puntúan más en los {len(ambos)}"
                cierre_g = "La ventaja de las Series <b>no depende de un género en particular</b>."
            elif len(ambos) and gana_nota == 0:
                titulo_generos = f"Nota promedio por género: las Películas puntúan más en los {len(ambos)}"
                cierre_g = "En esta selección la ventaja es de las <b>Películas</b>."
            else:
                titulo_generos = f"Nota promedio por género: las Series puntúan más en {gana_nota} de {len(ambos)}"
                cierre_g = ("En esta selección la ventaja de las Series <b>depende del género</b>: "
                            "revisa el gráfico antes de generalizar.")
            respuesta(
                f"En <b>{gana_nota} de {len(ambos)}</b> géneros comparables las Series tienen mejor nota que las "
                f"Películas, y en <b>{gana_vol} de {len(ambos)}</b> tienen igual o más títulos. {cierre_g}"
            )
        else:
            nota("Para comparar formatos, deja Películas y Series activas en el filtro de tipo de contenido.")

        # Grafico A: nota por genero
        pregunta("¿Ocurre en todos los géneros? (nota)")
        orden_g = (tg.groupby("genero")["calif_prom"].mean().sort_values(ascending=True).index.tolist())
        figa = px.bar(
            tg, x="calif_prom", y="genero", color="content_type", orientation="h", barmode="group",
            color_discrete_map=COLOR_FORMATO, text="calif_prom",
            category_orders={"genero": orden_g, "content_type": ORDEN_TIPO},
            labels={"calif_prom": "Calificación promedio (0–10)", "genero": "", "content_type": ""},
            title=titulo_generos,
        )
        figa.update_traces(texttemplate="%{text:.2f}", textposition="outside", cliponaxis=False)
        figa.update_layout(
            **LAYOUT_BASE,
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            xaxis=dict(range=[0, 9]), height=480,
        )
        st.plotly_chart(figa, width="stretch")
        st.caption("Cómo leerlo: barras más largas = mejor nota. Cada género tiene un par de barras para comparar.")

        # Grafico B: volumen por genero
        pregunta("¿Qué géneros tienen más títulos en cada formato?")
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
        st.plotly_chart(figb, width="stretch")
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
    pregunta("¿Qué géneros combinan buena nota y buena popularidad?")
    tp = ud.tabla_generos(df_f, solo_comparables=False)
    tp = tp[(tp["titulos"] >= 30) & (tp["genres"] != "Unknown")].dropna(subset=["calif_prom"])   # «Sin género» son datos faltantes, no un género
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
        st.plotly_chart(figp, width="stretch")
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
        if not un_formato:
            cf = ud.correlacion_por_formato(df_f, 50)
            if all(v[0] is not None for v in cf.values()):
                nota(
                    "<b>Ojo al mezclar formatos:</b> las Series tienen más popularidad y mejor nota que las "
                    "Películas, y eso hace parecer que ambas métricas se relacionan más de lo que es cierto. "
                    f"Dentro de cada formato (con 50+ votos) la relación es de <b>{num(cf['Película'][0])}</b> en "
                    f"Películas y de <b>{num(cf['Serie TV'][0])}</b> en Series: "
                    f"{ud.fuerza_correlacion(max(abs(cf['Película'][0]), abs(cf['Serie TV'][0])))}."
                )
    else:
        nota("No hay suficientes títulos calificados para medir la relación con estos filtros.")

    pregunta("¿Lo popular es también lo mejor evaluado?")
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
        st.plotly_chart(fig_d, width="stretch")
        st.caption(
            "Cómo leerlo: si lo popular fuera lo mejor, los puntos formarían una línea que sube de izquierda a "
            "derecha. Aquí forman una nube ancha. La escala logarítmica (cada marca multiplica por 10) evita que "
            "unos pocos títulos extremadamente populares aplasten al resto."
        )

    with st.expander("¿Por qué la cifra cambia según los votos mínimos y según el formato?"):
        filas = []
        for u in (0, 50, 100, 200):
            r_todos, _ = ud.correlacion_pop_calif(df_catalogo[df_catalogo["vote_count"] >= u])
            r_fmt = ud.correlacion_por_formato(df_catalogo, u)
            filas.append({
                "Votos mínimos": etiqueta_votos(u),
                "Todos juntos (ρ)": num(r_todos),
                "Solo Películas (ρ)": num(r_fmt["Película"][0]),
                "Solo Series (ρ)": num(r_fmt["Serie TV"][0]),
            })
        st.dataframe(pd.DataFrame(filas), hide_index=True, width="stretch")
        st.markdown(
            "**Dos efectos.** (1) Una nota que viene de 3 votos es puro ruido y tapa la relación: al exigir más "
            "votos, la relación aparece con más claridad. (2) Si se mezclan Películas y Series, la relación se ve "
            "más fuerte de lo que es, porque las Series tienen **más popularidad y mejor nota**: parte de la "
            "relación es solo la diferencia entre formatos. Dentro de cada formato es **débil**. Por eso hay que "
            "decir siempre **con qué mínimo de votos y con qué formatos** se calculó. (Tabla sobre el catálogo completo.)"
        )

# ---------------------------------------------------------------
# 4. PAISES E IDIOMAS
# ---------------------------------------------------------------
with t4:
    encabezado_seccion(
        "¿De dónde vienen las Series mejor evaluadas?",
        "Nota promedio de las series por país, comparada con un mínimo de votos para que sea confiable. Más abajo, los idiomas del catálogo.",
    )
    # Con paises elegidos en el filtro: se comparan SOLO esos paises, y se marca cuales tienen base suficiente
    if paises_sel:
        pregunta("¿Cómo se comparan los países elegidos?")
        pe = ud.paises_nota_50(df_f, 0)
        pe = pe[pe["country"].isin(paises_sel)].copy()
        sin_datos = [ud.es_pais(p) for p in paises_sel if p not in set(pe["country"])]
        if pe.empty:
            st.info(f"Ninguno de los países elegidos tiene series con {ud.VOTOS_CONFIABLE}+ votos en esta selección. "
                    "Activa «Serie TV» en «¿Qué quieres ver?» o amplía los años.")
        else:
            pe["base"] = pe["titulos"].ge(ud.MIN_TITULOS_GRUPO).map(
                {True: f"Base suficiente ({ud.MIN_TITULOS_GRUPO}+ series)", False: "Pocas series: referencial"})
            pe = pe.sort_values("nota", ascending=False).assign(
                pais=lambda d: d["country"].map(ud.es_pais),
                etiqueta=lambda d: d.apply(lambda r: f"{num(r['nota'])} ± {num(r['error'])}  ({miles(r['titulos'])} series)"
                                           if pd.notna(r["error"]) else f"{num(r['nota'])}  ({miles(r['titulos'])} serie)",
                                           axis=1),
            )
            ok = pe[pe["titulos"] >= ud.MIN_TITULOS_GRUPO].sort_values("nota", ascending=False)
            txt_ok = (", ".join(f"<b>{r['pais']}</b> {num(r['nota'])}" for _, r in ok.iterrows())
                      if not ok.empty else "ninguno")
            debiles = pe[pe["titulos"] < ud.MIN_TITULOS_GRUPO]["pais"].tolist()
            respuesta(
                f"Países elegidos con base suficiente ({ud.MIN_TITULOS_GRUPO}+ series con {ud.VOTOS_CONFIABLE}+ votos): {txt_ok}. "
                + (f"Con pocas series, solo como referencia: {', '.join(debiles)}. " if debiles else "")
                + (f"Sin series con {ud.VOTOS_CONFIABLE}+ votos: {', '.join(sin_datos)}." if sin_datos else "")
            )
            fig_pe = px.bar(
                pe, x="nota", y="pais", orientation="h", text="etiqueta", color="base",
                color_discrete_map={f"Base suficiente ({ud.MIN_TITULOS_GRUPO}+ series)": AZUL,
                                    "Pocas series: referencial": GRIS_LINEA},
                category_orders={"pais": pe["pais"].tolist()},
                labels={"nota": f"Nota promedio de las series con {ud.VOTOS_CONFIABLE}+ votos (0–10)", "pais": "", "base": ""},
                title="Series de los países elegidos: nota promedio (± margen de error)",
            )
            fig_pe.update_traces(textposition="outside", cliponaxis=False)
            fig_pe.update_layout(**LAYOUT_BASE, xaxis=dict(range=[0, 11]), height=max(260, 70 * len(pe) + 120),
                                 legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
            st.plotly_chart(fig_pe, width="stretch")
            st.caption("Cómo leerlo: barra azul = país con suficientes series para comparar; gris = pocas series, la nota "
                       "puede moverse mucho por azar (mira el ± margen de error). Quita el filtro de países para ver el "
                       "ranking general.")

    # Nota por pais usando solo series con 50+ votos; el minimo de series por pais baja si el filtro deja pocas
    min_t, pn = 100, pd.DataFrame()
    for min_t in (100, 50, 25):
        pn = ud.paises_nota_50(df_f, min_t)
        if len(pn) >= 3:
            break
    if paises_sel:
        pass  # con filtro de paises ya se mostro la comparacion de los paises elegidos
    elif pn.empty:
        st.info("Este gráfico analiza Series TV con 50+ votos. Activa “Serie TV” en «¿Qué quieres ver?» "
                "y revisa que el mínimo de votos no deje muy pocos títulos.")
    else:
        pregunta("¿De dónde vienen las Series mejor evaluadas?")
        vol = ud.tabla_paises_series(df_f, 10)
        a, b = pn.iloc[0], (pn.iloc[1] if len(pn) > 1 else None)
        mejores = (f"<b>{ud.es_pais(a['country'])}</b> ({num(a['nota'])})" +
                   (f" y <b>{ud.es_pais(b['country'])}</b> ({num(b['nota'])})" if b is not None else ""))
        china = ud.fila(vol, "country", "China")
        aviso_china = ""
        if china is not None and int(china["titulos_50_votos"]) < min_t:
            aviso_china = (f" <b>Cuidado con China</b>: tiene {miles(china['titulos'])} series, pero solo "
                           f"{miles(china['titulos_50_votos'])} con 50+ votos; su promedio no se puede comparar con confianza.")
        respuesta(
            f"Entre los países con al menos {min_t} series con 50+ votos, {mejores} tienen la <b>mejor nota</b>."
            f"{aviso_china}"
        )
        pn_plot = pn.sort_values("nota", ascending=True).assign(
            pais=lambda d: d["country"].map(ud.es_pais),
            etiqueta=lambda d: d.apply(lambda r: f"{num(r['nota'])}  ({miles(r['titulos'])} series)", axis=1),
        )
        fig_p = px.bar(
            pn_plot, x="nota", y="pais", orientation="h", text="etiqueta",
            category_orders={"pais": pn_plot["pais"].tolist()},
            labels={"nota": "Nota promedio de las series con 50+ votos (0–10)", "pais": ""},
            title="Series: nota promedio por país (solo con 50+ votos)",
            color_discrete_sequence=[AZUL],
        )
        fig_p.update_traces(textposition="outside", cliponaxis=False)
        fig_p.update_layout(**LAYOUT_BASE, showlegend=False, xaxis=dict(range=[0, 10.5]), height=420)
        st.plotly_chart(fig_p, width="stretch")
        st.caption(f"Cómo leerlo: cada barra es la nota promedio de las series del país que tienen 50 votos o más; "
                   f"entre paréntesis, cuántas series cumplen eso. Solo aparecen países con {min_t}+ series así.")

        with st.expander("¿Por qué se exige un mínimo de votos? ¿Y por qué un país con menos series puede tener mejor nota?"):
            # Siempre sobre el catalogo completo: asi "sin minimo" y "50+ votos" se pueden comparar de verdad
            vol_cat = ud.tabla_paises_series(df_catalogo, 10)
            nota50 = ud.paises_nota_50(df_catalogo, 0)[["country", "nota", "error"]]
            tv = vol_cat.merge(nota50, on="country", how="left")
            tv = tv.assign(**{
                "País": tv["country"].map(ud.es_pais),
                "Series (total)": tv["titulos"].map(miles),
                "Series con 50+ votos": tv["titulos_50_votos"].map(miles),
                "Nota prom. (sin mínimo)": tv["calif_prom"].map(num),
                "Nota prom. (50+ votos)": tv["nota"].map(num),
                "Margen de error (±)": tv["error"].map(num),
            })[["País", "Series (total)", "Series con 50+ votos", "Nota prom. (sin mínimo)",
                "Nota prom. (50+ votos)", "Margen de error (±)"]]
            st.dataframe(tv, hide_index=True, width="stretch")
            st.markdown(
                "**1. Por qué el mínimo de votos.** Muchas series de un país tienen muy pocos votos, y esas notas son "
                "ruido: bajan o suben el promedio sin que signifique nada. Al exigir 50+ votos cambia el orden de los "
                "países, así que **la comparación entre países se hace siempre con ese mínimo**.\n\n"
                "**2. Por qué un país con menos series puede tener mejor nota.** La cantidad de títulos y su nota "
                "miden cosas distintas: un país puede tener muchas series y una nota media, o pocas y una nota alta. "
                "Lo que sí importa es que haya **suficientes series con votos** para que el promedio sea confiable. "
                "El **margen de error** de la última columna lo muestra: es cuánto puede moverse el promedio por azar. "
                "Con cientos de series es pequeño (unas pocas centésimas) y con pocas series (como China) es grande. "
                "Por eso se comparan solo países con 100+ series con 50+ votos.\n\n"
                "*Tabla calculada sobre el catálogo completo, sin filtros.*"
            )

    st.markdown("---")
    encabezado_seccion("¿Qué idiomas tienen más presencia?", "Porcentaje de títulos por idioma original, en la selección actual.")
    pregunta("¿En qué idiomas está el catálogo?")
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
        st.plotly_chart(fig_i, width="stretch")
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
        st.info("Esta pestaña analiza Películas. Elige «Todo el catálogo» o «Solo Películas» en «¿Qué quieres ver?».")
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
                pregunta("¿Qué géneros de películas devuelven más dinero?")
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
                st.plotly_chart(fig_r, width="stretch")
                st.caption("Cómo leerlo: barras más largas = más dinero recaudado por cada dólar invertido. "
                           "Solo géneros con al menos 60 películas con datos.")

            pregunta("¿Más presupuesto trae más ingresos?")
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
            st.plotly_chart(fig_s, width="stretch")
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
        "Seis decisiones para el Comité, las mismas y en el mismo orden que el informe ejecutivo. "
        "Todas las cifras de esta pestaña usan el catálogo completo (sin filtros).",
    )
    H = calcular_hallazgos(df_catalogo, df_movies)
    KB, K50 = H["kpis"], H["kpis50"]
    V = ud.VOTOS_CONFIABLE
    G = ud.MIN_TITULOS_GRUPO
    PN0 = ud.paises_nota_50(df_catalogo, 0)  # nota y margen de error de cada pais (series con 50+ votos)

    # --- 1. Series (mismo umbral que los paises: 50+ votos) y, dentro de ellas, los generos mejor evaluados
    tg2 = H["series_top_generos"]
    n_g = H["series_top_generos_n"]
    txt_g = " y ".join(f"<b>{ud.es_genero(g)}</b> ({num(v)}; {miles(n_g[g])} series)" for g, v in tg2.items())
    txt_g_corto = " y ".join(ud.es_genero(g) for g in tg2.index)
    tarjeta_reco(
        "1 · Priorizar Series de calidad",
        f"Orientar la próxima inversión de contenido hacia Series, empezando por {txt_g_corto}.",
        f"Con {V}+ votos por título (el mismo umbral que exigimos para comparar países), las Series puntúan "
        f"{num(K50['calif_serie'])} vs. {num(K50['calif_pelicula'])} de las Películas (+{num(K50['brecha'])}), "
        f"sobre {miles(H['n_series50'])} series y {miles(H['n_peliculas50'])} películas. Ganan en "
        f"{H['anios_series']} de {H['anios_total']} años (la menor diferencia anual es de {num(H['brecha_min_anio'])} puntos) "
        f"y en {H['generos_series']} de {H['generos_total']} géneros comparables. Sin exigir votos la diferencia es "
        f"menor (+{num(KB['brecha'])}): el umbral no crea la ventaja, la confirma. Dentro de las Series lideran {txt_g}, "
        f"contando solo géneros con {G}+ series con {V}+ votos.",
        f"Solo una de cada cuatro series calificadas alcanza {V} votos: la conclusión vale para series con audiencia "
        "suficiente para evaluarlas. Los datos no distinguen series originales de licenciadas. Documental y Western "
        f"tienen notas altas, pero menos de {G} series con {V}+ votos: no se recomiendan con confianza.",
    )

    # --- 2. Paises con base suficiente
    pa = H["paises"]
    if len(pa) >= 2:
        top2 = pa.head(2)
        nombres = " y ".join(ud.es_pais(c) for c in top2["country"])
        top_p = " y ".join(f"<b>{ud.es_pais(r['country'])}</b> ({num(r['nota'])} ± {num(r['error'])}; "
                           f"{miles(r['titulos'])} series)" for _, r in top2.iterrows())
        eeuu = ud.fila(PN0, "country", "United States of America")
        if eeuu is None:
            eeuu = ud.fila(PN0, "country", "United States")
        txt_eeuu = (f" Como referencia, Estados Unidos tiene {num(eeuu['nota'])} ± {num(eeuu['error'])} con "
                    f"{miles(eeuu['titulos'])} series." if eeuu is not None else "")
        tarjeta_reco(
            f"2 · Mirar primero {nombres}",
            f"Explorar adquisición y coproducción en esos mercados; revisar cada uno con el filtro por país. "
            f"Estados Unidos conserva la mayor escala.",
            f"Nota promedio de las series con {V}+ votos, solo en países con {G} o más series así (pestaña 4): "
            f"{top_p}.{txt_eeuu}",
            "Sin exigir un mínimo de votos el orden de los países cambia: la comparación solo es confiable con ese mínimo.",
        )

    # --- 3. Dos metricas
    tarjeta_reco(
        "3 · No decidir por popularidad sola",
        "Usar el índice combinado (posición en popularidad y en nota) para las decisiones de luz verde.",
        f"Dentro de cada formato ({V}+ votos), popularidad y nota se relacionan de forma débil: "
        f"ρ = {num(H['rho_pel50'])} en Películas y {num(H['rho_ser50'])} en Series. Mirar una sola métrica "
        f"deja fuera a muchos títulos buenos o populares.",
        "El índice de abajo es un ejemplo (50% popularidad, 50% nota), no una fórmula oficial: el peso es una "
        "decisión del negocio. En una lista mezclada dominan las Series, por eso la tabla muestra 5 de cada formato.",
    )

    # --- 4. Finanzas
    rg5 = H["roi_generos"]
    if not rg5.empty and H["roi_global"]:
        top5 = rg5.iloc[0]
        g5 = ud.es_genero(top5["genres"])
        tarjeta_reco(
            f"4 · Evaluar {g5} por retorno",
            f"Revisar {g5} con costos reales antes de comprometer presupuesto: evaluarlo por costo y retorno, "
            f"no por calificación.",
            f"{g5} tiene el mayor retorno mediano: {num(top5['roi_mediano'], 1)}× frente a "
            f"{num(H['roi_global'], 1)}× de la película típica ({miles(top5['titulos'])} películas con datos de dinero), "
            f"con un presupuesto mediano de US$ {num(top5['presupuesto_mediano'] / 1e6, 1)} millones.",
            f"Solo {H['fin_cobertura'] * 100:.0f}% de las películas informa presupuesto e ingresos, y el retorno es "
            f"bruto (sin marketing). Es una señal, no una garantía.",
        )

    # --- 5. Paises con pocos datos
    china = ud.fila(H["paises_vol"], "country", "China")
    china50 = ud.fila(PN0, "country", "China")
    if china is not None and china50 is not None and int(china["titulos_50_votos"]) < G:
        txt_5 = (f"China tiene la nota más alta ({num(china50['nota'])}), pero solo {miles(china['titulos_50_votos'])} "
                 f"de sus {miles(china['titulos'])} series tienen {V}+ votos, con un margen de error de "
                 f"± {num(china50['error'])}"
                 + (" (" + " y ".join(f"{ud.es_pais(r['country'])}: ± {num(r['error'])}" for _, r in pa.head(2).iterrows())
                    + ")." if len(pa) >= 2 else "."))
    else:
        txt_5 = (f"Un país con pocas series votadas puede quedar arriba o abajo por azar: su margen de error es grande.")
    tarjeta_reco(
        "5 · No recomendar países con pocos datos",
        f"Exigir un mínimo de votos ({V}+) y de series ({G}+) antes de comparar países.",
        txt_5,
        "El filtro por país muestra en gris los países con pocas series: su nota es solo referencial.",
    )

    # --- 6. Datos de comportamiento
    tarjeta_reco(
        "6 · Cruzar con datos de comportamiento real",
        "Integrar retención y tiempo de visualización antes de comprometer presupuesto de producción a gran escala.",
        "El engagement se midió con aproximaciones (popularidad, votos y nota); las fuentes disponibles no tienen "
        "datos de reproducción, retención ni abandono.",
        "Hasta tener esos datos, estas recomendaciones indican dónde mirar primero, no dónde invertir únicamente.",
    )

    pregunta("¿Cómo elegir títulos mirando popularidad y nota a la vez? (recomendación 3)")
    st.markdown("**Ejemplo del indicador compuesto: los 5 mejores de cada formato** "
                f"(mínimo {H['indice_votos']} votos)")
    top_idx = H["indice"]
    if not top_idx.empty:
        tabla_idx = top_idx[["title", "content_type", "release_year", "popularity", "vote_average",
                             "vote_count", "indice"]].rename(columns={
            "title": "Título", "content_type": "Tipo", "release_year": "Año",
            "popularity": "Popularidad", "vote_average": "Nota", "vote_count": "Votos", "indice": "Índice (0–100)",
        })
        tabla_idx["Popularidad"] = tabla_idx["Popularidad"].round(1)
        tabla_idx["Nota"] = tabla_idx["Nota"].round(2)
        tabla_idx["Índice (0–100)"] = tabla_idx["Índice (0–100)"].round(1)
        st.dataframe(tabla_idx, hide_index=True, width="stretch")
        st.caption("Índice = promedio de la posición (percentil) del título en popularidad y en nota, calculada "
                   "entre todos los títulos con 50+ votos. Se muestran los 5 mejores de cada formato para poder compararlos.")

# ---------------------------------------------------------------
# EXPLORAR DATOS
# ---------------------------------------------------------------
# ---------------------------------------------------------------
# 7. INFOGRAFIA DEL SEGMENTO (se genera con los filtros activos)
# ---------------------------------------------------------------
with t8:
    encabezado_seccion(
        "Infografía del segmento filtrado",
        "Aplica filtros en el panel lateral y genera un informe breve y un volante A4 con cifras, ranking de mayor a menor y recomendación.",
    )
    if ig is None:
        st.error("Falta la librería matplotlib. Agrégala a requirements.txt (matplotlib) e instálala.")
    else:
        c1, c2 = st.columns(2)
        criterio_lbl = c1.selectbox("Ordenar el ranking por", list(ud.CRITERIOS_RANKING.keys()), key="ig_criterio")
        titulo_ig = c2.text_input("Título personalizado (opcional)", key="ig_titulo",
                                  placeholder="Ej.: Series de Animación 2015–2025")
        criterio_ig = ud.CRITERIOS_RANKING[criterio_lbl]
        _plural_c = ("películas" if list(tipos_sel) == ["Película"] else
                     "series" if list(tipos_sel) == ["Serie TV"] else "series y películas")
        paises_ig = st.multiselect(
            "Países a comparar en la infografía (máximo 6)",
            options=VOL_PAISES.index.tolist(), default=paises_sel[:6], max_selections=6,
            format_func=ud.es_pais, placeholder="Ej.: Corea del Sur, Japón, Estados Unidos",
            help=(f"Agrega a la infografía un gráfico con la nota de las {_plural_c} de cada país elegido, un formato por barra "
                  f"(solo títulos con {ud.VOTOS_CONFIABLE}+ votos). Se precargan los países del "
                  "panel lateral. Usa los mismos filtros de formato, años, votos y género, pero no el filtro de país, "
                  "para que cada país cuente todos sus títulos."),
        )
        st.caption(
            f"¿Por qué {ud.VOTOS_CONFIABLE}+ votos? El filtro de país no usa umbral: entran todos los títulos del país. "
            f"El umbral se usa solo para **comparar notas entre países**: la nota de un título con pocos votos es "
            f"poco confiable, y el promedio de un país con pocos títulos se mueve mucho por azar. Por eso un país con "
            f"menos de {ud.MIN_TITULOS_GRUPO} títulos con {ud.VOTOS_CONFIABLE}+ votos en un formato aparece en color claro "
            "(referencial), en vez de desaparecer."
        )
        df_comp_ig = ud.aplicar_filtros(df_catalogo, tipos_sel, anio_min, anio_max, votos_min, generos_sel, None)
        firma = (tuple(tipos_sel), anio_min, anio_max, votos_min, tuple(generos_sel), tuple(paises_sel),
                 criterio_ig, titulo_ig, tuple(paises_ig))

        if st.button("Generar infografía con los filtros actuales", type="primary", key="ig_boton"):
            try:
                fig_ig = ig.construir_infografia(df_f, df_catalogo, tipos_sel, anio_min, anio_max, votos_min,
                                                 generos_sel, criterio=criterio_ig, titulo=titulo_ig,
                                                 peliculas=df_movies, paises=paises_sel,
                                                 paises_comp=paises_ig, df_comp=df_comp_ig)
                informe_md = ig.construir_informe(df_f, df_catalogo, tipos_sel, anio_min, anio_max, votos_min,
                                                  generos_sel, criterio=criterio_ig, titulo=titulo_ig,
                                                  paises=paises_sel, paises_comp=paises_ig, df_comp=df_comp_ig)
                png_b, pdf_b = ig.exportar(fig_ig)
                st.session_state["ig_resultado"] = {"firma": firma, "png": png_b, "pdf": pdf_b,
                                                    "informe": informe_md}
            except ValueError as e:
                st.session_state.pop("ig_resultado", None)
                st.warning(str(e))

        res = st.session_state.get("ig_resultado")
        if res:
            if res["firma"] != firma:
                st.info("Cambiaste los filtros después de generar esta infografía. "
                        "Presiona el botón para actualizarla.")
            d1, d2, d3 = st.columns(3)
            nombre = "infografia_streamview"
            d1.download_button("Descargar PNG", res["png"], file_name=nombre + ".png", mime="image/png")
            d2.download_button("Descargar PDF", res["pdf"], file_name=nombre + ".pdf", mime="application/pdf")
            d3.download_button("Descargar informe (.md)", res["informe"].encode("utf-8"),
                               file_name=nombre + "_informe.md", mime="text/markdown")
            with st.expander("Ver informe del segmento"):
                st.markdown(res["informe"])
            st.image(res["png"])
        else:
            st.caption("Aún no se ha generado ninguna infografía.")

with t7:
    encabezado_seccion(
        "Explorador del catálogo filtrado",
        "Pregunta que responde: ¿qué títulos hay detrás de cada cifra? Es la tabla de los gráficos: sirve para comprobar un dato, ordenar por cualquier columna (clic en el encabezado), buscar un título (ícono de lupa) y descargar la selección en CSV. Respeta los filtros del panel lateral.",
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
        tabla, width="stretch", height=460, hide_index=True,
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

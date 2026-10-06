"""
utils_datos.py - Logica de datos de StreamView Analytics (un solo lugar)

El notebook y el dashboard importan este modulo, asi las cifras de ambos
nunca se contradicen. Solo usa pandas y numpy: no depende de Streamlit ni de Plotly.

Reglas que aplica (las mismas en todo el proyecto):
  - Un titulo = un registro. Se crea 'id_unico' porque 'show_id' se repite entre catalogos.
  - vote_average = 0 significa "sin calificacion", no una nota de 0: se excluye de los promedios.
  - La popularidad se compara con la MEDIANA (unos pocos titulos extremos distorsionan el promedio).
  - La relacion popularidad-calificacion se mide con Spearman (por rangos), no con Pearson.
"""
import os
import re

import numpy as np
import pandas as pd

CSV_PELICULAS = "netflix_movies_detailed_up_to_2025.csv"
CSV_SERIES = "netflix_tv_shows_detailed_up_to_2025.csv"

# Unicos 8 generos que se llaman igual en Peliculas y en Series
GENEROS_COMPARABLES = ["Drama", "Comedy", "Animation", "Crime", "Family", "Mystery", "Documentary", "Western"]

# Presupuesto e ingresos menores a este monto se descartan (valores simbolicos que dan ROI absurdos)
UMBRAL_FINANCIERO = 100_000

COLUMNAS_COMUNES = [
    "id_unico", "show_id", "content_type", "title", "director", "cast", "country",
    "release_year", "genres", "language", "description",
    "popularity", "vote_count", "vote_average", "sin_calificacion",
]

# ------------------------------------------------------------------
# Nombres en espanol (si no esta en el diccionario, se deja el original)
# ------------------------------------------------------------------
GENEROS_ES = {
    "Drama": "Drama", "Comedy": "Comedia", "Animation": "Animación", "Crime": "Crimen",
    "Family": "Familia", "Mystery": "Misterio", "Documentary": "Documental", "Western": "Western",
    "Action": "Acción", "Adventure": "Aventura", "Fantasy": "Fantasía",
    "Science Fiction": "Ciencia ficción", "Action & Adventure": "Acción y Aventura",
    "Sci-Fi & Fantasy": "Sci-Fi y Fantasía", "Kids": "Infantil", "History": "Historia",
    "Talk": "Talk show", "Soap": "Telenovela", "TV Movie": "Película para TV",
    "Music": "Música", "War": "Bélica", "War & Politics": "Guerra y Política",
    "News": "Noticias", "Unknown": "Sin género",
}
PAISES_ES = {
    "United States of America": "Estados Unidos", "Japan": "Japón", "United Kingdom": "Reino Unido",
    "South Korea": "Corea del Sur", "France": "Francia", "Canada": "Canadá", "Germany": "Alemania",
    "Spain": "España", "Belgium": "Bélgica", "Italy": "Italia", "Mexico": "México",
    "Philippines": "Filipinas", "Brazil": "Brasil", "Russia": "Rusia", "Turkey": "Turquía",
    "Sweden": "Suecia", "Thailand": "Tailandia", "Denmark": "Dinamarca",
    "Netherlands": "Países Bajos", "Poland": "Polonia", "Ireland": "Irlanda",
}
IDIOMAS_ES = {
    "en": "Inglés", "zh": "Chino", "ja": "Japonés", "ko": "Coreano", "es": "Español",
    "fr": "Francés", "de": "Alemán", "hi": "Hindi", "tl": "Tagalo", "pt": "Portugués",
    "ru": "Ruso", "it": "Italiano", "tr": "Turco", "ar": "Árabe", "nl": "Neerlandés",
    "cn": "Cantonés", "th": "Tailandés", "pl": "Polaco", "sv": "Sueco", "da": "Danés",
}


def es_genero(g):
    return GENEROS_ES.get(g, g)


def es_pais(p):
    return PAISES_ES.get(p, p)


def es_idioma(i):
    return IDIOMAS_ES.get(i, i)


# ------------------------------------------------------------------
# Carga y limpieza
# ------------------------------------------------------------------
def buscar_carpeta_datos(archivo_base=None):
    """Busca la carpeta con los dos CSV, sin importar desde donde se ejecute el dashboard."""
    aqui = os.path.dirname(os.path.abspath(archivo_base)) if archivo_base else os.getcwd()
    cwd = os.getcwd()
    candidatos = [
        aqui, os.path.join(aqui, "data"),
        os.path.dirname(aqui), os.path.join(os.path.dirname(aqui), "data"),
        cwd, os.path.join(cwd, "data"), os.path.join(os.path.dirname(cwd), "data"),
    ]
    for carpeta in candidatos:
        if (os.path.exists(os.path.join(carpeta, CSV_PELICULAS))
                and os.path.exists(os.path.join(carpeta, CSV_SERIES))):
            return carpeta
    return None


def limpiar_dataset(df, tipo_contenido):
    """Limpia y estandariza un dataset (Peliculas o Series)."""
    d = df.copy()
    d = d.drop_duplicates()
    d = d.drop_duplicates(subset=["show_id"], keep="first")

    d = d.drop(columns=[c for c in ["duration", "rating"] if c in d.columns])

    for col in ["title", "director", "cast", "country", "genres", "language", "description"]:
        if col in d.columns:
            d[col] = d[col].astype("string").str.strip()

    d["release_year"] = d["release_year"].astype(int)
    d["content_type"] = tipo_contenido
    d["sin_calificacion"] = d["vote_average"] == 0
    d["id_unico"] = tipo_contenido[:3].upper() + "_" + d["show_id"].astype(str)
    return d


def cargar_catalogo(carpeta):
    """Devuelve (peliculas, series, catalogo). 'peliculas' conserva budget y revenue."""
    peliculas = limpiar_dataset(pd.read_csv(os.path.join(carpeta, CSV_PELICULAS)), "Película")
    series = limpiar_dataset(pd.read_csv(os.path.join(carpeta, CSV_SERIES)), "Serie TV")
    catalogo = pd.concat([peliculas[COLUMNAS_COMUNES], series[COLUMNAS_COMUNES]], ignore_index=True)
    return peliculas, series, catalogo


def explode_columna(df, columna):
    """Una columna con varios valores separados por coma -> una fila por valor."""
    d = df.assign(**{columna: df[columna].fillna("").str.split(", ")}).explode(columna)
    d[columna] = d[columna].str.strip()
    return d[d[columna] != ""]


def aplicar_filtros(df, tipos, anio_min, anio_max, votos_min, generos=None):
    """Filtros del panel lateral. El genero se compara de forma exacta
    (asi 'Action' no arrastra a 'Action & Adventure')."""
    out = df[
        df["content_type"].isin(tipos)
        & df["release_year"].between(anio_min, anio_max)
        & (df["vote_count"] >= votos_min)
    ].copy()
    if generos:
        elegidos = set(generos)
        listas = out["genres"].fillna("").str.split(", ")
        out = out[listas.apply(lambda lst: not elegidos.isdisjoint(lst))]
    return out


def calificados(df):
    """Solo titulos con calificacion real (vote_average > 0)."""
    return df[~df["sin_calificacion"]]


# ------------------------------------------------------------------
# Indicadores
# ------------------------------------------------------------------
def resumen_formatos(df):
    c = calificados(df)
    r = pd.DataFrame({
        "titulos": df.groupby("content_type").size(),
        "calificados": c.groupby("content_type").size(),
        "calif_prom": c.groupby("content_type")["vote_average"].mean(),
        "pop_mediana": df.groupby("content_type")["popularity"].median(),
        "votos_mediana": c.groupby("content_type")["vote_count"].median(),
    })
    return r.reindex(["Película", "Serie TV"])


def _valor(r, columna, formato):
    try:
        x = r.loc[formato, columna]
    except KeyError:
        return None
    return None if pd.isna(x) else float(x)


def kpis(df):
    """Los 5 indicadores de arriba del dashboard."""
    r = resumen_formatos(df)
    cp = _valor(r, "calif_prom", "Película")
    cs = _valor(r, "calif_prom", "Serie TV")
    pp = _valor(r, "pop_mediana", "Película")
    ps = _valor(r, "pop_mediana", "Serie TV")
    return {
        "n": int(len(df)),
        "calif_pelicula": cp,
        "calif_serie": cs,
        "brecha": (cs - cp) if (cp is not None and cs is not None) else None,
        "pop_veces": (ps / pp) if (pp and ps) else None,
    }


def calif_por_anio(df):
    return (
        calificados(df).groupby(["release_year", "content_type"])["vote_average"]
        .mean().reset_index().rename(columns={"vote_average": "calif_prom"})
    )


def brecha_por_votos(df, umbrales=(0, 10, 50, 100, 250, 500)):
    """Prueba de robustez: la ventaja de las Series, exigiendo cada vez mas votos."""
    c = calificados(df)
    filas = []
    for u in umbrales:
        s = c[c["vote_count"] >= u]
        medias = s.groupby("content_type")["vote_average"].mean()
        n = s.groupby("content_type").size()
        if "Película" in medias.index and "Serie TV" in medias.index:
            filas.append({
                "votos_min": u,
                "n_pelicula": int(n["Película"]), "n_serie": int(n["Serie TV"]),
                "calif_pelicula": float(medias["Película"]), "calif_serie": float(medias["Serie TV"]),
                "brecha": float(medias["Serie TV"] - medias["Película"]),
            })
    return pd.DataFrame(filas)


def tabla_generos(df, solo_comparables=True):
    """Por genero y formato: titulos, calificacion promedio y popularidad mediana."""
    x = explode_columna(df, "genres")
    if solo_comparables:
        x = x[x["genres"].isin(GENEROS_COMPARABLES)]
    if x.empty:
        return pd.DataFrame(columns=["genres", "content_type", "titulos", "pop_mediana", "calif_prom"])
    base = (x.groupby(["genres", "content_type"])
            .agg(titulos=("id_unico", "nunique"), pop_mediana=("popularity", "median"))
            .reset_index())
    cal = (calificados(x).groupby(["genres", "content_type"])["vote_average"]
           .mean().reset_index(name="calif_prom"))
    return base.merge(cal, on=["genres", "content_type"], how="left")


def correlacion_pop_calif(df):
    """Spearman entre popularidad y calificacion. Devuelve (rho, n)."""
    c = calificados(df)
    if len(c) < 30:
        return None, len(c)
    # Spearman = correlacion de Pearson entre las POSICIONES (rangos) de ambas variables.
    # Se calcula asi para no depender de scipy (da el mismo resultado).
    rho = c["popularity"].rank().corr(c["vote_average"].rank())
    return (None if pd.isna(rho) else float(rho)), int(len(c))


def fuerza_correlacion(rho):
    if rho is None:
        return None
    a = abs(rho)
    if a < 0.2:
        return "muy débil"
    if a < 0.4:
        return "débil"
    if a < 0.6:
        return "moderada"
    return "fuerte"


def correlacion_por_votos(df, umbrales=(0, 50, 100, 200)):
    filas = []
    for u in umbrales:
        rho, n = correlacion_pop_calif(df[df["vote_count"] >= u])
        if rho is not None:
            filas.append({"votos_min": u, "titulos": n, "rho": rho})
    return pd.DataFrame(filas)


def tabla_paises_series(df, n=10):
    """Top paises por volumen de Series, con su calificacion y cuantos titulos tienen 50+ votos."""
    s = df[df["content_type"] == "Serie TV"]
    if s.empty:
        return pd.DataFrame(columns=["country", "titulos", "calif_prom", "titulos_50_votos"])
    x = explode_columna(s, "country")
    vol = x.groupby("country")["id_unico"].nunique().rename("titulos")
    c = calificados(x)
    cal = c.groupby("country")["vote_average"].mean().rename("calif_prom")
    sol = c[c["vote_count"] >= 50].groupby("country")["id_unico"].nunique().rename("titulos_50_votos")
    t = pd.concat([vol, cal, sol], axis=1).reset_index()
    t["titulos_50_votos"] = t["titulos_50_votos"].fillna(0).astype(int)
    return t.sort_values("titulos", ascending=False).head(n)


def tabla_idiomas(df, n=8):
    v = df["language"].value_counts(normalize=True).head(n) * 100
    t = pd.DataFrame({"language": v.index, "porcentaje": v.values})
    t["idioma"] = t["language"].map(es_idioma)
    return t


# ------------------------------------------------------------------
# Finanzas (solo peliculas con presupuesto e ingresos informados)
# ------------------------------------------------------------------
def datos_financieros(df_peliculas, ids=None, umbral=UMBRAL_FINANCIERO):
    d = df_peliculas
    if ids is not None:
        d = d[d["id_unico"].isin(set(ids))]
    f = d[(d["budget"] >= umbral) & (d["revenue"] >= umbral)].copy()
    f["roi"] = f["revenue"] / f["budget"]
    return f


def roi_por_genero(fin, min_n=60):
    if fin.empty:
        return pd.DataFrame(columns=["genres", "titulos", "roi_mediano", "presupuesto_mediano"])
    x = explode_columna(fin, "genres")
    t = (x.groupby("genres")
         .agg(titulos=("roi", "size"), roi_mediano=("roi", "median"),
              presupuesto_mediano=("budget", "median"))
         .reset_index())
    return t[t["titulos"] >= min_n].sort_values("roi_mediano", ascending=False)


# ------------------------------------------------------------------
# Indice compuesto (recomendacion 4)
# ------------------------------------------------------------------
def indice_compuesto(df, votos_min=50, n=10):
    """Promedio de dos posiciones (percentiles): popularidad y calificacion, de 0 a 100."""
    c = calificados(df)
    c = c[c["vote_count"] >= votos_min].copy()
    if c.empty:
        return c
    c["indice"] = 100 * (c["popularity"].rank(pct=True) + c["vote_average"].rank(pct=True)) / 2
    cols = ["title", "content_type", "release_year", "popularity", "vote_average", "vote_count", "indice"]
    return c.sort_values("indice", ascending=False).head(n)[cols]


# ------------------------------------------------------------------
# Ranking de titulos (para la infografia del segmento)
# ------------------------------------------------------------------
CRITERIOS_RANKING = {
    "Combinado (popularidad + nota)": "indice",
    "Calificación": "nota",
    "Popularidad": "popularidad",
}


def ranking_titulos(df, criterio="indice", n=10, votos_min=50):
    """Los n mejores titulos del segmento, ordenados de mayor a menor.

    Solo entran titulos con calificacion real y al menos 'votos_min' votos (una nota basada en
    3 votos no es confiable). Si con ese minimo no alcanzan n titulos, se baja el minimo
    (50 -> 10 -> el del filtro) y se informa cual se uso.
    Devuelve (tabla, votos_usados). 'valor' es la cifra por la que se ordeno.
    """
    base = calificados(df)
    umbrales = sorted({votos_min, min(votos_min, 10), 0}, reverse=True)
    elegibles, usado = base, 0
    for u in umbrales:
        elegibles = base[base["vote_count"] >= u]
        usado = u
        if len(elegibles) >= n:
            break
    if elegibles.empty:
        return elegibles.assign(valor=[], indice=[]), usado

    e = elegibles.copy()
    e["indice"] = 100 * (e["popularity"].rank(pct=True) + e["vote_average"].rank(pct=True)) / 2
    if criterio == "nota":
        e["valor"] = e["vote_average"]
        e = e.sort_values(["vote_average", "vote_count"], ascending=False)
    elif criterio == "popularidad":
        e["valor"] = e["popularity"]
        e = e.sort_values("popularity", ascending=False)
    else:
        e["valor"] = e["indice"]
        e = e.sort_values("indice", ascending=False)
    cols = ["title", "content_type", "release_year", "popularity", "vote_average",
            "vote_count", "indice", "valor"]
    return e.head(n)[cols].reset_index(drop=True), usado


# ------------------------------------------------------------------
# Hallazgos para la pestana "Que decidir" (siempre sobre el catalogo completo)
# ------------------------------------------------------------------
def fila(tabla, columna, valor):
    """Devuelve la fila de 'tabla' donde columna == valor, o None."""
    if tabla is None or tabla.empty:
        return None
    r = tabla[tabla[columna] == valor]
    return None if r.empty else r.iloc[0]


def hallazgos(df, df_peliculas):
    h = {"kpis": kpis(df), "brecha_votos": brecha_por_votos(df)}
    h["rho_todos"], _ = correlacion_pop_calif(df)
    h["rho_50"], _ = correlacion_pop_calif(df[df["vote_count"] >= 50])

    ts = tabla_generos(df[df["content_type"] == "Serie TV"], solo_comparables=False)
    h["series_generos"] = ts[ts["titulos"] >= 150].sort_values("calif_prom", ascending=False)

    tp = tabla_generos(df[df["content_type"] == "Película"], solo_comparables=False)
    h["pel_generos"] = tp[tp["titulos"] >= 100].sort_values("calif_prom", ascending=False)
    h["pop_mediana_peliculas"] = float(df.loc[df["content_type"] == "Película", "popularity"].median())

    h["paises"] = tabla_paises_series(df, 10)

    ids_pel = df.loc[df["content_type"] == "Película", "id_unico"]
    fin = datos_financieros(df_peliculas, ids=ids_pel)
    h["fin"] = fin
    h["fin_cobertura"] = float(len(fin) / max(len(ids_pel), 1))
    h["roi_global"] = float(fin["roi"].median()) if len(fin) else None
    h["roi_generos"] = roi_por_genero(fin, 80)
    return h


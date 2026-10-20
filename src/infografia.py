"""
infografia.py - Infografia-volante de un segmento del catalogo (StreamView Analytics)

Toma los filtros que el usuario aplico en el dashboard y arma UNA hoja A4 con:
  1. Titulo claro (describe el segmento)      4. Hallazgos destacados en texto breve
  2. Breve introduccion                        5. Conclusion o recomendacion final
  3. Visualizaciones: ranking top 10 + 2 graficos de apoyo + 4 indicadores

Es el equivalente a un "volante": el dashboard sirve para explorar, la infografia sirve para
comunicar un mensaje concreto y se descarga como PNG (para pantalla) o PDF (para imprimir).

Usa solo matplotlib (sin Kaleido ni Chrome), asi funciona igual en Codespaces y en Streamlit Cloud.
"""
import io
import textwrap

import matplotlib

matplotlib.use("Agg")  # sin ventana: solo genera imagenes
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.patches import Rectangle  # noqa: E402

import utils_datos as ud  # noqa: E402
from paleta import (  # noqa: E402
    AMARILLO, AZUL, NEGRO, BLANCO, GRIS_TEXTO, GRIS_LINEA, GRIS_FONDO,
    AMARILLO_SUAVE, COLOR_FORMATO,
)

plt.rcParams["pdf.fonttype"] = 42   # texto seleccionable y nitido en el PDF
plt.rcParams["font.family"] = "DejaVu Sans"

ANCHO_IN, ALTO_IN = 8.27, 11.69      # A4 vertical
TEXTO = "#1A1A1A"   # texto de apoyo: casi negro, para que se lea bien impreso
ETIQUETA_CRITERIO = {"indice": "índice combinado (0–100)", "nota": "calificación (0–10)",
                     "popularidad": "popularidad"}
ETIQUETA_EJE = {"indice": "Índice: posición entre todos los títulos del segmento (100 = el mejor)",
                "nota": "Nota del público (0–10)", "popularidad": "Popularidad (índice relativo de interés)"}


# ------------------------------------------------------------------
# Formato de numeros y textos (coma decimal, punto de miles)
# ------------------------------------------------------------------
def _num(x, d=2):
    return "—" if x is None else f"{x:.{d}f}".replace(".", ",")


def _pct_catalogo(n, n_cat):
    p = n / n_cat * 100
    return "menos de 0,1%" if p < 0.1 else f"{_num(p, 1)}%"


def _miles(x):
    return f"{int(round(x)):,}".replace(",", ".")


def _recorta(texto, n):
    texto = str(texto)
    return texto if len(texto) <= n else texto[: n - 1].rstrip() + "…"


def _parrafo(texto, ancho):
    return textwrap.fill(texto, width=ancho)


# ------------------------------------------------------------------
# Titulo y descripcion del segmento
# ------------------------------------------------------------------
def describir_filtros(tipos, anio_min, anio_max, votos_min, generos):
    partes = []
    if len(tipos) == 1:
        partes.append("Series TV" if tipos[0] == "Serie TV" else "Películas")
    if generos:
        nombres = [ud.es_genero(g) for g in generos]
        partes.append(", ".join(nombres[:3]) + (f" +{len(nombres) - 3}" if len(nombres) > 3 else ""))
    if (anio_min, anio_max) != (2010, 2025):
        partes.append(f"{anio_min}–{anio_max}" if anio_min != anio_max else str(anio_min))
    if votos_min > 0:
        partes.append(f"{votos_min}+ votos")
    return partes


# ------------------------------------------------------------------
# Textos automaticos: hallazgos y recomendacion
# ------------------------------------------------------------------
def _hallazgos(df, catalogo, ranking, criterio):
    c = ud.calificados(df)
    cc = ud.calificados(catalogo)
    out = []

    if len(c):
        nota, nota_cat = float(c["vote_average"].mean()), float(cc["vote_average"].mean())
        d = nota - nota_cat
        if abs(d) < 0.05:
            out.append(f"Nota promedio {_num(nota)}: igual que el catálogo completo ({_num(nota_cat)}).")
        else:
            out.append(f"Nota promedio {_num(nota)}: {_num(abs(d))} puntos "
                       f"{'sobre' if d > 0 else 'bajo'} el catálogo completo ({_num(nota_cat)}).")

    pop, pop_cat = float(df["popularity"].median()), float(catalogo["popularity"].median())
    out.append(f"Popularidad mediana {_num(pop, 1)}: {_num(pop / pop_cat, 1)} veces la del catálogo "
               f"completo ({_num(pop_cat, 1)}).")

    # Brecha entre formatos (solo si hay ambos y suficientes datos) o relacion popularidad-nota
    por_formato = c.groupby("content_type")["vote_average"].agg(["mean", "size"])
    if {"Película", "Serie TV"} <= set(por_formato.index) and (por_formato["size"] >= 30).all():
        ps, pp = por_formato.loc["Serie TV", "mean"], por_formato.loc["Película", "mean"]
        out.append(f"Series {_num(ps)} vs. Películas {_num(pp)} de nota: "
                   f"{_num(abs(ps - pp))} puntos a favor de {'las Series' if ps >= pp else 'las Películas'}.")
    else:
        rho, _ = ud.correlacion_pop_calif(df)
        if rho is not None:
            out.append(f"Popularidad y nota se relacionan de forma {ud.fuerza_correlacion(rho)} "
                       f"(ρ = {_num(rho)}).")

    if len(ranking):
        r = ranking.iloc[0]
        out.append(f"Mejor título: «{_recorta(r['title'], 30)}» ({r['content_type']}, {int(r['release_year'])}), "
                   f"nota {_num(r['vote_average'], 1)} y popularidad {_miles(r['popularity'])}.")
    return out


# Reglas con que se decide la recomendacion (estan a la vista para poder explicarlas y probarlas)
MIN_CALIFICADOS_REC = 30      # con menos titulos calificados la lectura es solo orientativa
UMBRAL_NOTA = 0.15            # puntos de nota sobre/bajo el catalogo para decir "alta" o "baja"
UMBRAL_POP_ALTA = 1.15        # popularidad mediana del segmento / la del catalogo
UMBRAL_POP_BAJA = 0.85
MIN_SERIES_PAIS = 50          # series con 50+ votos que debe tener un pais para entrar a la franja
MIN_PEL_FINANZAS = 30         # peliculas con presupuesto e ingresos para mostrar el retorno
MIN_PEL_GENERO = 60           # idem, por genero


# Version corta de cada recomendacion para la infografia: una palabra de accion y una frase
TEXTO_CORTO = {
    "calidad y alcance": ("PRIORIZAR", "Gusta mucho y llega a mucha gente."),
    "nicho de calidad": ("PROTEGER", "Muy bien evaluado, pero llega a pocos."),
    "alcance sin calidad": ("CUIDADO", "Llega a mucha gente, pero gusta menos."),
    "bajo en ambas": ("CAUTELA", "Gusta y llega menos que el promedio."),
    "buena nota, alcance normal": ("BUENA OPCIÓN", "Gusta más que el promedio del catálogo."),
    "nota baja, alcance normal": ("REVISAR", "Gusta menos que el promedio."),
    "alcance alto, nota normal": ("NEUTRO", "Llama la atención, pero sin destacar en nota."),
    "alcance bajo, nota normal": ("EVALUAR", "Interesa menos que el promedio; mira costo y retorno."),
    "cercano al promedio": ("NEUTRO", "Rinde igual que el promedio del catálogo."),
}


def diagnosticar(df, catalogo):
    """Compara el segmento con el catalogo y devuelve las cifras y la regla que dieron la recomendacion.

    Devuelve un dict: caso, texto, d_nota (puntos), razon_pop (veces), n_calificados.
    """
    c, cc = ud.calificados(df), ud.calificados(catalogo)
    if len(c) < MIN_CALIFICADOS_REC:
        return {"caso": "pocos datos", "d_nota": None, "razon_pop": None, "n_calificados": len(c),
                "etiqueta": "POCOS DATOS", "corto": "Amplía los filtros antes de decidir.",
                "texto": ("Pocos títulos con calificación: la lectura es orientativa. Amplía los filtros "
                          "(por ejemplo, el rango de años) antes de tomar una decisión de inversión.")}
    d_nota = float(c["vote_average"].mean() - cc["vote_average"].mean())
    razon_pop = float(df["popularity"].median() / catalogo["popularity"].median())
    nota_alta, nota_baja = d_nota >= UMBRAL_NOTA, d_nota <= -UMBRAL_NOTA
    pop_alta, pop_baja = razon_pop >= UMBRAL_POP_ALTA, razon_pop <= UMBRAL_POP_BAJA
    if nota_alta and pop_alta:
        caso, texto = ("calidad y alcance",
                       "Segmento fuerte en calidad y en alcance: es un buen candidato para priorizar en la próxima "
                       "inversión de contenido.")
    elif nota_alta and pop_baja:
        caso, texto = ("nicho de calidad",
                       "Nicho de calidad: está bien evaluado pero llega a menos gente. Conviene protegerlo y "
                       "medirlo por su nota, no por su alcance.")
    elif nota_baja and pop_alta:
        caso, texto = ("alcance sin calidad",
                       "Mucho alcance pero nota bajo el promedio: revisa la calidad antes de aumentar la inversión.")
    elif nota_baja and pop_baja:
        caso, texto = ("bajo en ambas",
                       "Bajo el promedio del catálogo en nota y en alcance: invertir con cautela y evaluarlo por "
                       "retorno y costo, no por prestigio.")
    elif nota_alta:
        caso, texto = ("buena nota, alcance normal",
                       "Buena nota con alcance similar al catálogo: es un segmento de calidad que aún puede crecer en alcance.")
    elif nota_baja:
        caso, texto = ("nota baja, alcance normal",
                       "Nota bajo el promedio con alcance similar al catálogo: revisa la calidad antes de invertir más.")
    elif pop_alta:
        caso, texto = ("alcance alto, nota normal",
                       "Más alcance que el catálogo pero con nota similar: llama la atención del público, aunque no destaca en calidad.")
    elif pop_baja:
        caso, texto = ("alcance bajo, nota normal",
                       "Menos alcance que el catálogo y nota similar: es un segmento de menor interés; evalúalo por costo y retorno.")
    else:
        caso, texto = ("cercano al promedio",
                       "Rendimiento cercano al promedio del catálogo: para decidir, usa popularidad y nota en "
                       "conjunto (se relacionan solo en parte).")
    etiqueta, corto = TEXTO_CORTO[caso]
    return {"caso": caso, "texto": texto, "etiqueta": etiqueta, "corto": corto, "d_nota": d_nota,
            "razon_pop": razon_pop, "n_calificados": len(c)}


def _recomendacion(df, catalogo):
    """Conclusion en lenguaje simple, segun como se compara el segmento con todo el catalogo."""
    return diagnosticar(df, catalogo)["texto"]


# ------------------------------------------------------------------
# Piezas graficas
# ------------------------------------------------------------------
def _estilo_ejes(ax):
    for lado in ("top", "right"):
        ax.spines[lado].set_visible(False)
    for lado in ("left", "bottom"):
        ax.spines[lado].set_color(GRIS_LINEA)
    ax.tick_params(colors=TEXTO, labelsize=9.5)
    ax.set_facecolor("none")


def _titulo_seccion(cv, x, y, texto):
    cv.text(x, y, texto, fontsize=12, fontweight="bold", color=AZUL, va="center", ha="left")
    cv.add_patch(Rectangle((x, y - 0.0135), 0.045, 0.0024, color=AMARILLO, lw=0))


def _tarjeta(cv, x, y, w, h, etiqueta, valor, detalle=None):
    cv.add_patch(Rectangle((x, y), w, h, facecolor=BLANCO, edgecolor=GRIS_LINEA, lw=0.8))
    cv.add_patch(Rectangle((x, y + h - 0.006), w, 0.006, color=AMARILLO, lw=0))
    cv.text(x + 0.016, y + h - 0.025, etiqueta, fontsize=8.5, fontweight="bold", color=GRIS_TEXTO, va="center")
    cv.text(x + 0.016, y + h * 0.43, valor, fontsize=21, fontweight="bold", color=NEGRO, va="center")
    if detalle:
        cv.text(x + 0.016, y + 0.016, detalle, fontsize=9.5, color=AZUL, va="center")


def _recomendacion_destacada(cv, diag, y, h):
    """Lo primero que se lee: una palabra de accion + una frase corta."""
    cv.add_patch(Rectangle((0.05, y), 0.90, h, facecolor=AMARILLO_SUAVE, lw=0))
    cv.add_patch(Rectangle((0.05, y), 0.010, h, color=AMARILLO, lw=0))
    cv.text(0.082, y + h - 0.022, "QUÉ HACER", fontsize=9, fontweight="bold", color=GRIS_TEXTO, va="center")
    cv.text(0.082, y + h * 0.40, diag["etiqueta"], fontsize=24, fontweight="bold", color=AZUL, va="center")
    cv.text(0.47, y + h * 0.40, _parrafo(diag["corto"], 36), fontsize=13, fontweight="bold", color=NEGRO,
            va="center", linespacing=1.25)


def _lista_ranking(cv, ranking, criterio, y_titulo):
    """Mejores titulos como lista limpia: sin ejes ni barras. 3 por formato (o 5 si hay un solo formato)."""
    formatos = list(dict.fromkeys(ranking["content_type"]))
    if not len(ranking):
        cv.text(0.5, y_titulo - 0.07, "No hay títulos con calificación suficiente para armar el ranking.",
                ha="center", fontsize=10, color=TEXTO)
        return y_titulo - 0.12
    dos = len(formatos) == 2
    cols = ([(0.05, 0.43), (0.52, 0.43)] if dos else [(0.05, 0.90)])
    paso = 0.040
    fin = y_titulo
    for (x, w), tipo in zip(cols, formatos):
        sub = ranking[ranking["content_type"] == tipo].head(3).reset_index(drop=True)
        color = COLOR_FORMATO[tipo]
        txt_col = BLANCO if tipo == "Serie TV" else NEGRO
        y_chip = y_titulo - 0.034
        cv.add_patch(Rectangle((x, y_chip - 0.011), w, 0.022, facecolor=color, edgecolor=NEGRO, lw=0.6))
        cv.text(x + 0.012, y_chip, "SERIES" if tipo == "Serie TV" else "PELÍCULAS", fontsize=9.5,
                fontweight="bold", color=txt_col, va="center")
        cv.text(x + w - 0.012, y_chip, "nota" if criterio != "popularidad" else "popularidad", fontsize=8.5,
                color=txt_col, va="center", ha="right")
        for i, r in sub.iterrows():
            yy = y_chip - 0.040 - i * paso
            cv.text(x + 0.004, yy, str(i + 1), fontsize=15, fontweight="bold", color=AZUL, va="center")
            cv.text(x + 0.034, yy + 0.006, _recorta(r["title"], 27 if dos else 60), fontsize=11.5,
                    fontweight="bold", color=NEGRO, va="center")
            extra = f" · nota {_num(r['vote_average'], 1)}" if criterio == "popularidad" else ""
            cv.text(x + 0.034, yy - 0.0085, f"{int(r['release_year'])}{extra}", fontsize=8.5, color=GRIS_TEXTO,
                    va="center")
            valor = _miles(r["popularity"]) if criterio == "popularidad" else _num(r["vote_average"], 1)
            cv.text(x + w - 0.012, yy, valor, fontsize=14, fontweight="bold", color=AZUL, va="center", ha="right")
            cv.add_patch(Rectangle((x, yy - 0.0215), w, 0.0008, color=GRIS_LINEA, lw=0))
            fin = min(fin, yy - 0.0215)
    return fin


def _evolucion(fig, df, rect):
    """Nota por año (si hay varios años) o por formato (si hay pocos)."""
    ax = fig.add_axes(rect)
    _estilo_ejes(ax)
    por_anio = ud.calif_por_anio(df)
    anios = sorted(por_anio["release_year"].unique())
    if len(anios) >= 3:
        for tipo in ("Película", "Serie TV"):
            s = por_anio[por_anio["content_type"] == tipo].sort_values("release_year")
            if len(s) < 2:
                continue
            ax.plot(s["release_year"], s["calif_prom"], color=COLOR_FORMATO[tipo], lw=3, marker="o", ms=4,
                    mec=NEGRO, mew=0.6)
            ax.text(s["release_year"].iloc[-1] + 0.3, s["calif_prom"].iloc[-1],
                    "Series" if tipo == "Serie TV" else "Películas", fontsize=10, fontweight="bold",
                    va="center", color=NEGRO)
        lo, hi = por_anio["calif_prom"].min(), por_anio["calif_prom"].max()
        ax.set_ylim(lo - 0.25, hi + 0.25)
        ax.set_xlim(anios[0] - 0.5, anios[-1] + 4.6)
        paso = max(1, (anios[-1] - anios[0]) // 4)
        ax.set_xticks(list(range(anios[0], anios[-1] + 1, paso)))
        ax.yaxis.grid(True, color="#E6E6E6", lw=0.6)
        ax.set_axisbelow(True)
        return "Nota por año"
    c = ud.calificados(df).groupby("content_type")["vote_average"].mean()
    tipos = [t for t in ("Película", "Serie TV") if t in c.index]
    ax.bar(range(len(tipos)), [c[t] for t in tipos], color=[COLOR_FORMATO[t] for t in tipos],
           edgecolor=NEGRO, linewidth=0.6, width=0.5)
    for i, t in enumerate(tipos):
        ax.text(i, c[t] + 0.12, _num(c[t]), ha="center", fontsize=11, fontweight="bold")
    ax.set_xticks(range(len(tipos)))
    ax.set_xticklabels(["Series" if t == "Serie TV" else "Películas" for t in tipos], fontsize=10)
    ax.set_ylim(0, 10)
    return "Nota por formato"


def _generos_top(fig, df, rect):
    """Panel derecho: 4 generos con mejor nota (solo los 8 comparables si el segmento tiene los dos formatos)."""
    ax = fig.add_axes(rect)
    _estilo_ejes(ax)
    ax.spines["left"].set_visible(False)
    x = ud.explode_columna(df, "genres")
    t = (ud.calificados(x).groupby("genres")
         .agg(titulos=("id_unico", "nunique"), nota=("vote_average", "mean")).reset_index())
    t = t[t["titulos"] >= 30]
    if df["content_type"].nunique() == 2:
        # con Series y Peliculas juntas solo se comparan los generos que existen en ambos formatos
        # (los mismos 8 de la pestana Generos); si no, los generos propios de las series inflarian la nota
        t = t[t["genres"].isin(ud.GENEROS_COMPARABLES)]
    t = t.sort_values("nota", ascending=False).head(4)
    if t.empty:
        ax.axis("off")
        ax.text(0.5, 0.5, "Sin datos suficientes", ha="center", va="center", fontsize=9,
                color=TEXTO, transform=ax.transAxes)
        return "Géneros mejor evaluados"
    n = len(t)
    valores = t["nota"].tolist()
    ax.barh(range(n), valores, color=AZUL, height=0.6)
    ax.set_ylim(n - 0.4, -0.6)
    ax.set_xlim(0, max(valores) * 1.28)
    ax.set_yticks(range(n))
    ax.set_yticklabels([_recorta(ud.es_genero(g), 22) for g in t["genres"]], fontsize=9.5, color=NEGRO)
    ax.set_xticks([])
    for i, v in enumerate(valores):
        ax.text(v + max(valores) * 0.02, i, _num(v), va="center", fontsize=10.5, fontweight="bold", color=NEGRO)
    return "Géneros mejor evaluados"


def _bloque_paises(cv, x, y, w, h, df):
    """Franja: 3 mejores paises para series (nota con 50+ votos). Se avisa si no hay series suficientes."""
    cv.add_patch(Rectangle((x, y), w, h, facecolor=BLANCO, edgecolor=GRIS_LINEA, lw=0.8))
    cv.add_patch(Rectangle((x, y + h - 0.005), w, 0.005, color=AMARILLO, lw=0))
    cv.text(x + 0.016, y + h - 0.019, "MEJORES PAÍSES · SERIES", fontsize=8.5, fontweight="bold",
            color=GRIS_TEXTO, va="center")
    t = ud.paises_nota_50(df, min_titulos=MIN_SERIES_PAIS).head(3)
    if t.empty:
        cv.text(x + 0.016, y + h * 0.40, "Este segmento no tiene series\nsuficientes para comparar países.",
                fontsize=9.5, color=TEXTO, va="center", linespacing=1.3)
        return
    for i, r in t.reset_index(drop=True).iterrows():
        yy = y + h - 0.043 - i * 0.0185
        cv.text(x + 0.016, yy, f"{i + 1}. {_recorta(ud.es_pais(r['country']), 20)}", fontsize=11,
                fontweight="bold", color=NEGRO, va="center")
        cv.text(x + w - 0.016, yy, _num(r["nota"]), fontsize=11.5, color=AZUL, va="center", ha="right",
                fontweight="bold")


def _bloque_dinero(cv, x, y, w, h, df, peliculas):
    """Franja: cuanto devuelve cada dolar invertido en las peliculas que informan presupuesto e ingresos."""
    cv.add_patch(Rectangle((x, y), w, h, facecolor=BLANCO, edgecolor=GRIS_LINEA, lw=0.8))
    cv.add_patch(Rectangle((x, y + h - 0.005), w, 0.005, color=AMARILLO, lw=0))
    cv.text(x + 0.016, y + h - 0.019, "DINERO · PELÍCULAS", fontsize=8.5, fontweight="bold",
            color=GRIS_TEXTO, va="center")
    ids = df.loc[df["content_type"] == "Película", "id_unico"]
    pel = peliculas[peliculas["id_unico"].isin(set(ids))] if peliculas is not None else peliculas
    fin = ud.datos_financieros(pel) if pel is not None else None
    if fin is None or len(fin) < MIN_PEL_FINANZAS:
        cv.text(x + 0.016, y + h * 0.40, "Pocas películas informan presupuesto\ne ingresos en este segmento.",
                fontsize=9.5, color=TEXTO, va="center", linespacing=1.3)
        return
    roi_med = float(fin["roi"].median())
    cv.text(x + 0.016, y + h - 0.043, "Por cada $1 invertido", fontsize=11, fontweight="bold", color=NEGRO, va="center")
    cv.text(x + w - 0.016, y + h - 0.043, f"vuelven ${_num(roi_med, 1)}", fontsize=11.5, color=AZUL, va="center",
            ha="right", fontweight="bold")
    g = ud.roi_por_genero(fin, min_n=MIN_PEL_GENERO)
    if len(g):
        r = g.iloc[0]
        cv.text(x + 0.016, y + h - 0.0615, f"Mejor género: {_recorta(ud.es_genero(r['genres']), 14)}",
                fontsize=11, fontweight="bold", color=NEGRO, va="center")
        cv.text(x + w - 0.016, y + h - 0.0615, f"vuelven ${_num(r['roi_mediano'], 1)}", fontsize=11.5, color=AZUL,
                va="center", ha="right", fontweight="bold")
    pct = len(fin) / max(len(pel), 1) * 100
    cv.text(x + 0.016, y + 0.010, f"Solo el {_num(pct, 0)}% de las películas informa su dinero.",
            fontsize=7.5, color=GRIS_TEXTO, va="center", style="italic")


def _hallazgos_cortos(df, catalogo, generos):
    """Dos frases cortas para la infografia, sin terminos tecnicos."""
    c = ud.calificados(df)
    out = []
    por_formato = c.groupby("content_type")["vote_average"].agg(["mean", "size"])
    if {"Película", "Serie TV"} <= set(por_formato.index) and (por_formato["size"] >= 30).all():
        ps, pp = por_formato.loc["Serie TV", "mean"], por_formato.loc["Película", "mean"]
        out.append(f"{'Las Series' if ps >= pp else 'Las Películas'} tienen {_num(abs(ps - pp))} puntos "
                   f"más de nota que {'las Películas' if ps >= pp else 'las Series'}.")
    else:
        por_anio = c.groupby("release_year")["vote_average"].agg(["mean", "size"])
        por_anio = por_anio[por_anio["size"] >= 10]
        if len(por_anio) >= 3:
            a = por_anio["mean"].idxmax()
            out.append(f"Mejor año: {int(a)}, con nota promedio de {_num(por_anio.loc[a, 'mean'])}.")
    for col, etiqueta, traducir in (("genres", "Género más frecuente", ud.es_genero),
                                    ("country", "País con más títulos", ud.es_pais)):
        if col == "genres" and len(generos) == 1:
            continue
        x = ud.explode_columna(df, col)
        if x.empty:
            continue
        conteo = x.groupby(col)["id_unico"].nunique().sort_values(ascending=False)
        out.append(f"{etiqueta}: {traducir(conteo.index[0])} ({_num(conteo.iloc[0] / len(df) * 100, 0)}% de los títulos).")
        break
    return out[:2]


# ------------------------------------------------------------------
# Funcion principal
# ------------------------------------------------------------------
def construir_infografia(df, catalogo, tipos, anio_min, anio_max, votos_min, generos,
                         criterio="indice", titulo=None, peliculas=None):
    """Arma la figura (A4). 'df' es el catalogo YA filtrado; 'catalogo' es el completo (para comparar).
    'peliculas' (opcional) es la tabla de peliculas con budget y revenue, para la franja de dinero.

    Orden de lectura: titulo -> que hacer -> 3 cifras -> mejores titulos -> grafico(s) -> 2 hallazgos ->
    paises y dinero. Casi no hay texto explicativo: el detalle y las definiciones estan en el dashboard."""
    if df.empty or len(ud.calificados(df)) < 5:
        raise ValueError("Hay muy pocos títulos calificados con estos filtros (mínimo 5). "
                         "Amplía el rango de años o quita algún filtro.")

    votos_base = 100 if criterio == "nota" else 50
    ranking, votos_usados = ud.ranking_titulos(df, criterio, n=10, votos_min=max(votos_min, votos_base), por_formato=True)

    fig = plt.figure(figsize=(ANCHO_IN, ALTO_IN), dpi=150, facecolor=BLANCO)
    cv = fig.add_axes([0, 0, 1, 1])
    cv.set_xlim(0, 1)
    cv.set_ylim(0, 1)
    cv.axis("off")

    # ---------- 1. Titulo + una linea de introduccion ----------
    partes = describir_filtros(tipos, anio_min, anio_max, votos_min, generos)
    titulo_auto = " · ".join(partes) if partes else "Todo el catálogo"
    titulo_final = (titulo or "").strip() or titulo_auto
    n, n_cat = len(df), len(catalogo)
    cv.add_patch(Rectangle((0, 0.905), 1, 0.095, color=AZUL, lw=0))
    cv.add_patch(Rectangle((0, 0.905), 1, 0.007, color=AMARILLO, lw=0))
    cv.text(0.05, 0.980, "STREAMVIEW ANALYTICS · FICHA DEL SEGMENTO", fontsize=9, fontweight="bold",
            color=AMARILLO, va="center")
    linea_titulo = textwrap.wrap(titulo_final, width=46)[:2]
    cv.text(0.05, 0.953 if len(linea_titulo) == 1 else 0.950, "\n".join(linea_titulo),
            fontsize=22 if len(linea_titulo) == 1 else 16, fontweight="bold", color=BLANCO, va="center",
            linespacing=1.15)
    cv.text(0.05, 0.926, f"{_miles(n)} títulos · {_pct_catalogo(n, n_cat)} del catálogo", fontsize=10,
            color=BLANCO, va="center")

    # ---------- 2. Que hacer (lo primero que se lee) ----------
    diag = diagnosticar(df, catalogo)
    _recomendacion_destacada(cv, diag, 0.785, 0.100)

    # ---------- 3. Tres cifras ----------
    c, cc = ud.calificados(df), ud.calificados(catalogo)
    nota = float(c["vote_average"].mean()) if len(c) else None
    nota_cat = float(cc["vote_average"].mean())
    pop, pop_cat = float(df["popularity"].median()), float(catalogo["popularity"].median())
    razon = pop / pop_cat
    d_nota = (nota - nota_cat) if nota is not None else None
    if d_nota is None:
        det_nota = None
    elif abs(d_nota) < 0.05:
        det_nota = f"Igual al catálogo ({_num(nota_cat)})"
    else:
        det_nota = f"{_num(abs(d_nota))} {'sobre' if d_nota > 0 else 'bajo'} el catálogo ({_num(nota_cat)})"
    det_pop = "Igual al catálogo" if 0.95 <= razon <= 1.05 else "veces la del catálogo"
    ancho, hueco, y0, alto = 0.29, 0.015, 0.665, 0.098
    tarjetas = [
        ("TÍTULOS", _miles(n), f"{_pct_catalogo(n, n_cat)} del catálogo"),
        ("NOTA PROMEDIO", f"{_num(nota)} / 10" if nota is not None else "—", det_nota),
        ("POPULARIDAD", f"{_num(razon, 1)}×", det_pop),
    ]
    for i, (et, val, det) in enumerate(tarjetas):
        _tarjeta(cv, 0.05 + i * (ancho + hueco), y0, ancho, alto, et, val, det)

    # ---------- 4. Los mejores titulos ----------
    dos_formatos = ranking["content_type"].nunique() == 2
    _titulo_seccion(cv, 0.05, 0.632, "Los títulos más destacados")
    orden = {"indice": "por popularidad y nota juntas", "nota": "por nota", "popularidad": "por popularidad"}[criterio]
    cv.text(0.95, 0.632, f"Ordenados {orden}", fontsize=9, color=GRIS_TEXTO, ha="right", va="center", style="italic")
    y_fin = _lista_ranking(cv, ranking, criterio, 0.632)

    # ---------- 5. Graficos ----------
    y_tit = y_fin - 0.026
    alto_g = 0.112
    y_ax = y_tit - 0.034 - alto_g
    con_generos = not generos
    rect_izq = [0.085, y_ax, 0.355 if con_generos else 0.80, alto_g]
    titulo_b = _evolucion(fig, df, rect_izq)
    _titulo_seccion(cv, 0.05, y_tit, titulo_b)
    if con_generos:
        titulo_c = _generos_top(fig, df, [0.715, y_ax, 0.235, alto_g])
        _titulo_seccion(cv, 0.575, y_tit, titulo_c)

    # ---------- 6. Dos hallazgos ----------
    y_h = y_ax - 0.040
    _titulo_seccion(cv, 0.05, y_h, "Lo más importante")
    y = y_h - 0.030
    for h in _hallazgos_cortos(df, catalogo, generos):
        cv.add_patch(Rectangle((0.05, y - 0.0035), 0.010, 0.0075, color=AMARILLO, ec=NEGRO, lw=0.5))
        cv.text(0.072, y, _recorta(h, 80), fontsize=11, color=NEGRO, va="center")
        y -= 0.026

    # ---------- 7. Paises y dinero ----------
    y_f = 0.062
    alto_f = 0.092
    _bloque_paises(cv, 0.05, y_f, 0.4425, alto_f, df)
    _bloque_dinero(cv, 0.5075, y_f, 0.4425, alto_f, df, peliculas)

    # ---------- Pie ----------
    cv.text(0.05, 0.033, f"Fuente: StreamView Analytics · catálogo de {_miles(n_cat)} títulos (2010–2025).",
            fontsize=8, color=GRIS_TEXTO, va="center")
    cv.add_patch(Rectangle((0, 0), 1, 0.006, color=AMARILLO, lw=0))
    return fig



def _perfil_segmento(df, generos=()):
    """Genero y pais mas frecuentes del segmento (por cantidad de titulos distintos)."""
    out = []
    for col, etiqueta, traducir in (("genres", "Género más frecuente", ud.es_genero),
                                    ("country", "País con más títulos", ud.es_pais)):
        if col == "genres" and len(generos) == 1:
            continue                      # con un solo género filtrado, "el más frecuente" es trivial
        x = ud.explode_columna(df, col)
        if x.empty:
            continue
        conteo = x.groupby(col)["id_unico"].nunique().sort_values(ascending=False)
        out.append(f"{etiqueta}: {traducir(conteo.index[0])} ({_miles(conteo.iloc[0])} títulos, "
                   f"{_num(conteo.iloc[0] / len(df) * 100, 0)}% del segmento).")
    return out


def construir_informe(df, catalogo, tipos, anio_min, anio_max, votos_min, generos, criterio="indice", titulo=None):
    """Informe breve (Markdown) del segmento filtrado: mismos datos que la infografia.

    Orden fijo: resumen -> 1 segmento analizado -> 2 cifras clave -> 3 hallazgos -> 4 ranking ->
    5 recomendacion (con la regla que la origino) -> 6 como leer el informe.
    """
    if df.empty or len(ud.calificados(df)) < 5:
        raise ValueError("Hay muy pocos títulos calificados con estos filtros (mínimo 5). "
                         "Amplía el rango de años o quita algún filtro.")
    partes = describir_filtros(tipos, anio_min, anio_max, votos_min, generos)
    nombre = (titulo or "").strip() or (" · ".join(partes) if partes else "Todo el catálogo")
    base = max(votos_min, 100 if criterio == "nota" else 50)
    ranking, usados = ud.ranking_titulos(df, criterio=criterio, n=10, votos_min=base, por_formato=True)
    c, cc = ud.calificados(df), ud.calificados(catalogo)
    n, n_cat = len(df), len(catalogo)
    nota, nota_cat = float(c["vote_average"].mean()), float(cc["vote_average"].mean())
    pop, pop_cat = float(df["popularity"].median()), float(catalogo["popularity"].median())
    pct_serie, pct_serie_cat = (float((d["content_type"] == "Serie TV").mean() * 100) for d in (df, catalogo))
    pct_cal, pct_cal_cat = len(c) / n * 100, len(cc) / n_cat * 100
    votos_med, votos_med_cat = float(df["vote_count"].median()), float(catalogo["vote_count"].median())
    diag = diagnosticar(df, catalogo)
    formato = ", ".join("Series TV" if t == "Serie TV" else "Películas" for t in tipos) if tipos else "todos"
    generos_txt = ", ".join(ud.es_genero(g) for g in generos) if generos else "todos"

    L = [f"# Informe del segmento: {nombre}", "",
         "*StreamView Analytics · generado desde el dashboard con los filtros activos*", "",
         f"> **Resumen.** {_miles(n)} títulos ({_num(n / n_cat * 100, 1)}% del catálogo), nota promedio "
         f"**{_num(nota)}** (catálogo {_num(nota_cat)}) y popularidad mediana **{_num(pop, 1)}** "
         f"({_num(pop / pop_cat, 1)}× el catálogo). **{diag['texto']}**", "",
         "## 1. Segmento analizado", "",
         "| Parámetro | Valor |", "|---|---|",
         f"| Formato | {formato} |",
         f"| Años de lanzamiento | {anio_min}–{anio_max} |",
         f"| Votos mínimos | {votos_min} |",
         f"| Géneros | {generos_txt} |",
         f"| Ranking ordenado por | {ETIQUETA_CRITERIO[criterio]} |", "",
         "## 2. Cifras clave", "",
         "| Indicador | Segmento | Catálogo completo | Diferencia |", "|---|---|---|---|",
         f"| Títulos | {_miles(n)} | {_miles(n_cat)} | {_num(n / n_cat * 100, 1)}% del catálogo |",
         f"| Con calificación | {_num(pct_cal, 1)}% | {_num(pct_cal_cat, 1)}% | "
         f"{_num(pct_cal - pct_cal_cat, 1)} pts |",
         f"| Nota promedio (0–10) | {_num(nota)} | {_num(nota_cat)} | {nota - nota_cat:+.2f} pts".replace(".", ",") + " |",
         f"| Popularidad mediana | {_num(pop, 1)} | {_num(pop_cat, 1)} | {_num(pop / pop_cat, 1)}× |",
         f"| Votos por título (mediana) | {_miles(votos_med)} | {_miles(votos_med_cat)} | "
         f"{_num(votos_med / votos_med_cat, 1) + '×' if votos_med_cat else '—'} |",
         f"| Series TV en el segmento | {_num(pct_serie, 0)}% | {_num(pct_serie_cat, 0)}% | — |", "",
         "## 3. Hallazgos", ""]
    hallazgos = _hallazgos(df, catalogo, ranking, criterio)[2:] + _perfil_segmento(df, generos)
    L += [f"{i}. {h}" for i, h in enumerate(hallazgos[:4], start=1)]
    titulo_rank = ("los 5 mejores de cada formato" if ranking["content_type"].nunique() == 2 else "los 10 mejores títulos")
    L += ["", f"## 4. Ranking: {titulo_rank} (solo con {usados}+ votos)", "",
          f"Ordenado de mayor a menor por {ETIQUETA_CRITERIO[criterio]}, dentro de cada formato. "
          f"Para ver solo Películas o solo Series, elige ese formato en el filtro.", "",
          "| N.º | Título | Formato | Año | Nota | Popularidad | Votos | Índice |",
          "|---|---|---|---|---|---|---|---|"]
    for i, r in ranking.iterrows():
        L.append(f"| {i + 1} | {r['title']} | {r['content_type']} | {int(r['release_year'])} | "
                 f"{_num(r['vote_average'], 1)} | {_miles(r['popularity'])} | {_miles(r['vote_count'])} | "
                 f"{_num(r['indice'], 0)} |")
    L += ["", "## 5. Recomendación", "", f"**{diag['texto']}**", ""]
    if diag["d_nota"] is not None:
        L += [f"*Por qué:* la nota del segmento está {_num(abs(diag['d_nota']))} puntos "
              f"{'sobre' if diag['d_nota'] >= 0 else 'bajo'} el catálogo y su popularidad mediana es "
              f"{_num(diag['razon_pop'], 1)}× la del catálogo. Se considera nota alta o baja a partir de "
              f"±{_num(UMBRAL_NOTA)} puntos y popularidad alta o baja a partir de ×{_num(UMBRAL_POP_ALTA)} / "
              f"×{_num(UMBRAL_POP_BAJA)}.", ""]
    L += ["## 6. Cómo leer este informe", "",
          "- La **popularidad** es un índice relativo de interés, no una cantidad de reproducciones.",
          "- Nota 0 = sin calificación: no entra en los promedios. Una nota con pocos votos es poco confiable, "
          "por eso el ranking exige un mínimo de votos.",
          "- El **índice combinado** (0–100) promedia la posición del título en popularidad y en nota.",
          "- La cantidad de títulos por año la fijó la muestra, así que no mide el crecimiento del catálogo."]
    return "\n".join(L)


def exportar(fig):
    """Devuelve (png_bytes, pdf_bytes) y libera la figura."""
    png, pdf = io.BytesIO(), io.BytesIO()
    fig.savefig(png, format="png", dpi=150, facecolor=BLANCO)
    fig.savefig(pdf, format="pdf", facecolor=BLANCO)
    plt.close(fig)
    return png.getvalue(), pdf.getvalue()

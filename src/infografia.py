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


def diagnosticar(df, catalogo):
    """Compara el segmento con el catalogo y devuelve las cifras y la regla que dieron la recomendacion.

    Devuelve un dict: caso, texto, d_nota (puntos), razon_pop (veces), n_calificados.
    """
    c, cc = ud.calificados(df), ud.calificados(catalogo)
    if len(c) < MIN_CALIFICADOS_REC:
        return {"caso": "pocos datos", "d_nota": None, "razon_pop": None, "n_calificados": len(c),
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
    return {"caso": caso, "texto": texto, "d_nota": d_nota, "razon_pop": razon_pop, "n_calificados": len(c)}


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
    ax.tick_params(colors=TEXTO, labelsize=9)
    ax.set_facecolor("none")


def _titulo_seccion(cv, x, y, texto):
    cv.text(x, y, texto, fontsize=10.5, fontweight="bold", color=AZUL, va="center", ha="left")
    cv.add_patch(Rectangle((x, y - 0.0125), 0.045, 0.0022, color=AMARILLO, lw=0))


def _tarjeta(cv, x, y, w, h, etiqueta, valor, detalle=None):
    cv.add_patch(Rectangle((x, y), w, h, facecolor=BLANCO, edgecolor=GRIS_LINEA, lw=0.8))
    cv.add_patch(Rectangle((x, y + h - 0.006), w, 0.006, color=AMARILLO, lw=0))
    cv.text(x + 0.014, y + h - 0.021, etiqueta, fontsize=8, fontweight="bold", color=TEXTO, va="center")
    cv.text(x + 0.014, y + h * 0.56, valor, fontsize=15.5, fontweight="bold", color=NEGRO, va="center")
    if detalle:
        cv.text(x + 0.014, y + 0.020, detalle, fontsize=8.5, color=AZUL, va="center", linespacing=1.25)


def _ranking(fig, ranking, criterio, votos_usados):
    ax = fig.add_axes([0.43, 0.488, 0.52, 0.262])
    _estilo_ejes(ax)
    n = len(ranking)
    if n == 0:
        ax.axis("off")
        ax.text(0.5, 0.5, "No hay títulos con calificación suficiente\npara armar el ranking con estos filtros.",
                ha="center", va="center", fontsize=9, color=TEXTO, transform=ax.transAxes)
        return
    agrupado = ranking["content_type"].nunique() == 2
    if agrupado:
        k = int((ranking["content_type"] == ranking["content_type"].iloc[0]).sum())   # filas del primer grupo
        ys = [i if i < k else i + 0.25 for i in range(n)]
        num_en_grupo = [i + 1 if i < k else i - k + 1 for i in range(n)]
    else:
        k = n
        ys = list(range(n))
        num_en_grupo = [i + 1 for i in range(n)]
    valores = ranking["valor"].tolist()
    colores = [COLOR_FORMATO[t] for t in ranking["content_type"]]
    ax.barh(ys, valores, height=0.74, color=colores, edgecolor=NEGRO, linewidth=0.6)
    ax.set_ylim(ys[-1] + 0.55, -0.6)           # el N.º 1 queda arriba
    ax.set_xlim(0, max(valores) * 1.20)
    ax.set_yticks([])
    ax.spines["left"].set_visible(False)
    ax.tick_params(axis="x", labelsize=8.5)
    ax.xaxis.grid(True, color="#E6E6E6", lw=0.6)
    ax.set_axisbelow(True)
    ax.set_xlabel(ETIQUETA_EJE[criterio], fontsize=8.5, color=TEXTO)

    izq = ax.get_yaxis_transform()       # x en fraccion del eje, y en datos
    for i, r in ranking.iterrows():
        y = ys[i]
        ax.text(-0.02, y, f"{num_en_grupo[i]}. {_recorta(r['title'], 30)}", transform=izq, ha="right",
                va="center", fontsize=10.5, fontweight="bold", color=NEGRO)
        ax.text(max(valores) * 0.012, y, f"{r['content_type']} · {int(r['release_year'])} · nota {_num(r['vote_average'], 1)}"
                f" · popularidad {_miles(r['popularity'])}", ha="left", va="center", fontsize=8.6,
                fontweight="bold", color=BLANCO if r["content_type"] == "Serie TV" else NEGRO)
        decimales = 0 if criterio == "indice" else (1 if criterio == "nota" else 0)
        ax.text(r["valor"] + max(valores) * 0.012, y, _num(r["valor"], decimales), va="center", ha="left",
                fontsize=9.5, fontweight="bold", color=NEGRO)
    if agrupado:
        for desde, hasta, tipo in ((0, k - 1, ranking["content_type"].iloc[0]), (k, n - 1, ranking["content_type"].iloc[-1])):
            y0, y1 = ys[desde] - 0.42, ys[hasta] + 0.42
            ax.add_patch(Rectangle((1.015, y0), 0.04, y1 - y0, transform=izq, clip_on=False,
                                   facecolor=COLOR_FORMATO[tipo], edgecolor=NEGRO, lw=0.6))
            ax.text(1.035, (y0 + y1) / 2, "SERIES" if tipo == "Serie TV" else "PELÍCULAS", transform=izq, rotation=90,
                    ha="center", va="center", fontsize=8.5, fontweight="bold",
                    color=BLANCO if tipo == "Serie TV" else NEGRO, clip_on=False)
        ax.axhline(k - 1 + 0.625, color=GRIS_LINEA, lw=0.8, ls="--")
    return ax


def _evolucion(fig, df):
    """Panel izquierdo: nota por año (si hay varios años) o por formato (si hay pocos)."""
    ax = fig.add_axes([0.085, 0.305, 0.355, 0.112])
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
                    "Series" if tipo == "Serie TV" else "Películas", fontsize=9, fontweight="bold",
                    va="center", color=NEGRO)
        lo, hi = por_anio["calif_prom"].min(), por_anio["calif_prom"].max()
        ax.set_ylim(lo - 0.25, hi + 0.25)
        ax.set_xlim(anios[0] - 0.5, anios[-1] + 4.2)
        paso = max(1, (anios[-1] - anios[0]) // 5)
        ax.set_xticks(list(range(anios[0], anios[-1] + 1, paso)))
        ax.yaxis.grid(True, color="#E6E6E6", lw=0.6)
        ax.set_axisbelow(True)
        ax.set_ylabel("Nota promedio (0–10)", fontsize=8.5, color=TEXTO)
        return "Nota promedio por año de lanzamiento"
    # Pocos años: barras por formato
    c = ud.calificados(df).groupby("content_type")["vote_average"].mean()
    tipos = [t for t in ("Película", "Serie TV") if t in c.index]
    ax.bar(range(len(tipos)), [c[t] for t in tipos], color=[COLOR_FORMATO[t] for t in tipos],
           edgecolor=NEGRO, linewidth=0.6, width=0.5)
    for i, t in enumerate(tipos):
        ax.text(i, c[t] + 0.12, _num(c[t]), ha="center", fontsize=10, fontweight="bold")
    ax.set_xticks(range(len(tipos)))
    ax.set_xticklabels(["Series" if t == "Serie TV" else "Películas" for t in tipos], fontsize=9.5)
    ax.set_ylim(0, 10)
    ax.set_ylabel("Nota promedio (0–10)", fontsize=8.5, color=TEXTO)
    return "Nota promedio por formato"


def _tercer_panel(fig, df, generos_filtrados):
    """Panel derecho: generos con mejor nota (si no se filtro genero) o paises con mas titulos."""
    ax = fig.add_axes([0.665, 0.305, 0.285, 0.112])
    _estilo_ejes(ax)
    ax.spines["left"].set_visible(False)
    if not generos_filtrados:
        x = ud.explode_columna(df, "genres")
        t = (ud.calificados(x).groupby("genres")
             .agg(titulos=("id_unico", "nunique"), nota=("vote_average", "mean")).reset_index())
        t = t[t["titulos"] >= 30].sort_values("nota", ascending=False).head(6)
        titulo, etiqueta = "Géneros con mejor nota", "nota"
        t["nombre"] = t["genres"].map(ud.es_genero)
        valores, fmt = t["nota"].tolist(), lambda v: _num(v)
        extra = [f"{_miles(n)} títulos" for n in t["titulos"]]
    else:
        x = ud.explode_columna(df, "country")
        t = (x.groupby("country").agg(titulos=("id_unico", "nunique")).reset_index()
             .sort_values("titulos", ascending=False).head(6))
        notas = ud.calificados(x).groupby("country")["vote_average"].mean()
        t["nota"] = t["country"].map(notas)
        titulo = "Países por cantidad de títulos"
        t["nombre"] = t["country"].map(ud.es_pais)
        valores, fmt = t["titulos"].tolist(), lambda v: _miles(v)
        extra = [f"nota {_num(n, 1)}" if n == n else "s/n" for n in t["nota"]]
    if t.empty:
        ax.axis("off")
        ax.text(0.5, 0.5, "Sin datos suficientes", ha="center", va="center", fontsize=8,
                color=TEXTO, transform=ax.transAxes)
        return titulo
    n = len(t)
    ax.barh(range(n), valores, color=AZUL, height=0.62)
    ax.set_ylim(n - 0.4, -0.6)
    ax.set_xlim(0, max(valores) * 2.0)
    ax.set_yticks(range(n))
    ax.set_yticklabels([_recorta(s, 17) for s in t["nombre"]], fontsize=8.8, color=NEGRO)
    ax.set_xticks([])
    for i, (v, e) in enumerate(zip(valores, extra)):
        ax.text(v + max(valores) * 0.02, i, f"{fmt(v)} · {e}", va="center", fontsize=8, color=NEGRO)
    return titulo


def _bloque_paises(cv, x, y, w, h, df):
    """Franja: 3 mejores paises para series (nota con 50+ votos). Se omite el dato si no hay series suficientes."""
    cv.add_patch(Rectangle((x, y), w, h, facecolor=BLANCO, edgecolor=GRIS_LINEA, lw=0.8))
    cv.add_patch(Rectangle((x, y + h - 0.005), w, 0.005, color=AMARILLO, lw=0))
    cv.text(x + 0.014, y + h - 0.017, "MEJORES PAÍSES · SERIES", fontsize=8, fontweight="bold", color=TEXTO, va="center")
    t = ud.paises_nota_50(df, min_titulos=MIN_SERIES_PAIS).head(3)
    if t.empty:
        cv.text(x + 0.014, y + h * 0.40, "Este segmento no tiene series\nsuficientes para comparar países.",
                fontsize=8.5, color=TEXTO, va="center", linespacing=1.3)
        return
    for i, r in t.reset_index(drop=True).iterrows():
        yy = y + h - 0.037 - i * 0.0135
        cv.text(x + 0.014, yy, f"{i + 1}. {_recorta(ud.es_pais(r['country']), 20)}", fontsize=9.5,
                fontweight="bold", color=NEGRO, va="center")
        cv.text(x + w - 0.014, yy, f"{_num(r['nota'], 1)}  ·  {_miles(r['titulos'])} series", fontsize=8.5,
                color=AZUL, va="center", ha="right", fontweight="bold")
    cv.text(x + 0.014, y + 0.008, f"Nota de series con 50+ votos; solo países con {MIN_SERIES_PAIS}+ series así.",
            fontsize=6.8, color=TEXTO, va="center", style="italic")


def _bloque_dinero(cv, x, y, w, h, df, peliculas):
    """Franja: retorno de la inversion (ingresos / presupuesto) de las peliculas que informan ambos datos."""
    cv.add_patch(Rectangle((x, y), w, h, facecolor=BLANCO, edgecolor=GRIS_LINEA, lw=0.8))
    cv.add_patch(Rectangle((x, y + h - 0.005), w, 0.005, color=AMARILLO, lw=0))
    cv.text(x + 0.014, y + h - 0.017, "DINERO · PELÍCULAS", fontsize=8, fontweight="bold", color=TEXTO, va="center")
    # 'df' no trae presupuesto ni ingresos: se toman de la tabla de peliculas, solo las del segmento
    ids = df.loc[df["content_type"] == "Película", "id_unico"]
    pel = peliculas[peliculas["id_unico"].isin(set(ids))] if peliculas is not None else peliculas
    fin = ud.datos_financieros(pel) if pel is not None else None
    if fin is None or len(fin) < MIN_PEL_FINANZAS:
        cv.text(x + 0.014, y + h * 0.40, "Pocas películas informan presupuesto\ne ingresos en este segmento.",
                fontsize=8.5, color=TEXTO, va="center", linespacing=1.3)
        return
    roi_med = float(fin["roi"].median())
    cv.text(x + 0.014, y + h - 0.037, "Retorno típico", fontsize=9.5, fontweight="bold", color=NEGRO, va="center")
    cv.text(x + w - 0.014, y + h - 0.037, f"{_num(roi_med, 1)}×", fontsize=11, color=AZUL, va="center",
            ha="right", fontweight="bold")
    g = ud.roi_por_genero(fin, min_n=MIN_PEL_GENERO)
    if len(g):
        r = g.iloc[0]
        cv.text(x + 0.014, y + h - 0.0545, f"Mejor género: {_recorta(ud.es_genero(r['genres']), 14)}",
                fontsize=9.5, fontweight="bold", color=NEGRO, va="center")
        cv.text(x + w - 0.014, y + h - 0.0545, f"{_num(r['roi_mediano'], 1)}×", fontsize=11, color=AZUL,
                va="center", ha="right", fontweight="bold")
    pct = len(fin) / max(len(pel), 1) * 100
    cv.text(x + 0.014, y + 0.008, f"Ingresos ÷ presupuesto (mediana). Solo el {_num(pct, 0)}% informa ambos datos.",
            fontsize=6.8, color=TEXTO, va="center", style="italic")


# ------------------------------------------------------------------
# Funcion principal
# ------------------------------------------------------------------
def construir_infografia(df, catalogo, tipos, anio_min, anio_max, votos_min, generos,
                         criterio="indice", titulo=None, peliculas=None):
    """Arma la figura (A4). 'df' es el catalogo YA filtrado; 'catalogo' es el completo (para comparar).
    'peliculas' (opcional) es la tabla de peliculas con budget y revenue, para la franja de dinero."""
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

    # ---------- 1. Titulo ----------
    partes = describir_filtros(tipos, anio_min, anio_max, votos_min, generos)
    titulo_auto = " · ".join(partes) if partes else "Todo el catálogo"
    titulo_final = (titulo or "").strip() or titulo_auto
    cv.add_patch(Rectangle((0, 0.915), 1, 0.085, color=AZUL, lw=0))
    cv.add_patch(Rectangle((0, 0.915), 1, 0.007, color=AMARILLO, lw=0))
    cv.text(0.05, 0.979, "STREAMVIEW ANALYTICS · FICHA DEL SEGMENTO", fontsize=9, fontweight="bold",
            color=AMARILLO, va="center")
    linea_titulo = textwrap.wrap(titulo_final, width=46)[:2]
    cv.text(0.05, 0.950 if len(linea_titulo) == 1 else 0.945, "\n".join(linea_titulo),
            fontsize=19 if len(linea_titulo) == 1 else 15.5, fontweight="bold", color=BLANCO, va="center",
            linespacing=1.15)

    # ---------- 2. Introduccion ----------
    n, n_cat = len(df), len(catalogo)
    intro = (f"Este segmento reúne {_miles(n)} títulos ({_num(n / n_cat * 100, 1)}% del catálogo de {_miles(n_cat)}). "
             f"Aquí están sus cifras clave, el ranking de sus mejores títulos y la decisión que sugieren los datos.")
    cv.text(0.05, 0.897, _parrafo(intro, 92), fontsize=9.5, color=TEXTO, va="center", linespacing=1.4)

    # ---------- Indicadores ----------
    c, cc = ud.calificados(df), ud.calificados(catalogo)
    nota = float(c["vote_average"].mean()) if len(c) else None
    nota_cat = float(cc["vote_average"].mean())
    pop, pop_cat = float(df["popularity"].median()), float(catalogo["popularity"].median())
    pct_series = float((df["content_type"] == "Serie TV").mean() * 100)
    ancho, hueco, y0, alto = 0.2075, 0.0125, 0.783, 0.092
    d_nota = (nota - nota_cat) if nota is not None else None
    if d_nota is None:
        det_nota = None
    elif abs(d_nota) < 0.05:
        det_nota = f"Igual que el catálogo\ncompleto ({_num(nota_cat)})"
    else:
        det_nota = (f"{_num(abs(d_nota))} puntos {'sobre' if d_nota > 0 else 'bajo'} el\n"
                    f"catálogo completo ({_num(nota_cat)})")
    tarjetas = [
        ("TÍTULOS", _miles(n), f"{_num(n / n_cat * 100, 1)}% del catálogo\ncompleto ({_miles(n_cat)})"),
        ("NOTA PROMEDIO", f"{_num(nota)} de 10" if nota is not None else "—", det_nota),
        ("POPULARIDAD MEDIANA", _num(pop, 1), f"{_num(pop / pop_cat, 1)} veces la del\ncatálogo completo ({_num(pop_cat, 1)})"),
        ("FORMATO", f"{pct_series:.0f}% Series", f"{pct_series:.0f}% son Series y\n{100 - pct_series:.0f}% son Películas"),
    ]
    for i, (et, val, det) in enumerate(tarjetas):
        _tarjeta(cv, 0.05 + i * (ancho + hueco), y0, ancho, alto, et, val, det)

    # ---------- 3. Visualizaciones ----------
    _titulo_seccion(cv, 0.05, 0.763, "Ranking: los 5 mejores de cada formato" if ranking["content_type"].nunique() == 2 else "Ranking: los 10 mejores títulos del segmento")
    cv.text(0.95, 0.763, f"Solo títulos con {votos_usados}+ votos", fontsize=9, color=TEXTO,
            ha="right", va="center", style="italic")
    _ranking(fig, ranking, criterio, votos_usados)
    # leyenda de colores
    x_leyenda = 0.05
    for tipo, col, et in (("Película", AMARILLO, "Película"), ("Serie TV", AZUL, "Serie TV")):
        if (df["content_type"] == tipo).any():
            cv.add_patch(Rectangle((x_leyenda, 0.466), 0.013, 0.0095, facecolor=col, edgecolor=NEGRO, lw=0.6))
            cv.text(x_leyenda + 0.019, 0.4710, et, fontsize=9, va="center")
            x_leyenda += 0.115

    titulo_b = _evolucion(fig, df)
    _titulo_seccion(cv, 0.05, 0.442, titulo_b)
    titulo_c = _tercer_panel(fig, df, bool(generos))
    _titulo_seccion(cv, 0.575, 0.442, titulo_c)

    # ---------- 4. Hallazgos (los 2 que no repiten las tarjetas) ----------
    _titulo_seccion(cv, 0.05, 0.268, "Hallazgos principales")
    y = 0.246
    for h in _hallazgos(df, catalogo, ranking, criterio)[2:4]:
        lineas = textwrap.wrap(h, width=90)
        cv.add_patch(Rectangle((0.05, y - 0.0035), 0.010, 0.0075, color=AMARILLO, ec=NEGRO, lw=0.5))
        cv.text(0.072, y - 0.0003, "\n".join(lineas), fontsize=9.8, color=NEGRO, va="center", linespacing=1.3)
        y -= 0.0160 * len(lineas) + 0.0080

    # ---------- Paises y dinero ----------
    _bloque_paises(cv, 0.05, 0.116, 0.4425, 0.084, df)
    _bloque_dinero(cv, 0.5075, 0.116, 0.4425, 0.084, df, peliculas)

    # ---------- 5. Conclusion ----------
    y_caja = 0.052
    cv.add_patch(Rectangle((0.05, y_caja), 0.90, 0.056, facecolor=AMARILLO_SUAVE, lw=0))
    cv.add_patch(Rectangle((0.05, y_caja), 0.008, 0.056, color=AMARILLO, lw=0))
    cv.text(0.072, y_caja + 0.044, "RECOMENDACIÓN", fontsize=9, fontweight="bold", color=AZUL, va="center")
    cv.text(0.072, y_caja + 0.019, _parrafo(_recomendacion(df, catalogo), 90), fontsize=9.5,
            fontweight="bold", color=NEGRO, va="center", linespacing=1.3)

    # ---------- Pie ----------
    nota_pie = ("Fuente: catálogo de StreamView Analytics (31.991 títulos, 2010–2025). La popularidad es un índice "
                "relativo de interés, no una cantidad de reproducciones. Nota 0 = sin calificación y no entra en los "
                "promedios. La cantidad de títulos por año la fijó la muestra, por lo que no mide el crecimiento "
                "del catálogo.")
    cv.text(0.05, 0.030, _parrafo(nota_pie, 112), fontsize=7.6, color=TEXTO, va="center", linespacing=1.35)
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

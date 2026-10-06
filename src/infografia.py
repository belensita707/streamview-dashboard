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
ETIQUETA_CRITERIO = {"indice": "índice combinado (0–100)", "nota": "calificación (0–10)",
                     "popularidad": "popularidad"}


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
            out.append(f"Nota promedio {_num(nota)}/10: en línea con el catálogo completo ({_num(nota_cat)}).")
        else:
            out.append(f"Nota promedio {_num(nota)}/10: {_num(abs(d))} puntos "
                       f"{'sobre' if d > 0 else 'bajo'} el promedio del catálogo ({_num(nota_cat)}).")

    pop, pop_cat = float(df["popularity"].median()), float(catalogo["popularity"].median())
    out.append(f"Popularidad mediana {_num(pop, 1)}: {_num(pop / pop_cat, 1)}× la del catálogo "
               f"completo ({_num(pop_cat, 1)}).")

    # Brecha entre formatos (solo si hay ambos y suficientes datos) o relacion popularidad-nota
    por_formato = c.groupby("content_type")["vote_average"].agg(["mean", "size"])
    if {"Película", "Serie TV"} <= set(por_formato.index) and (por_formato["size"] >= 30).all():
        ps, pp = por_formato.loc["Serie TV", "mean"], por_formato.loc["Película", "mean"]
        out.append(f"Las Series puntúan {_num(ps)} y las Películas {_num(pp)}: "
                   f"{_num(abs(ps - pp))} puntos a favor de {'las Series' if ps >= pp else 'las Películas'}.")
    else:
        rho, _ = ud.correlacion_pop_calif(df)
        if rho is not None:
            out.append(f"Popularidad y nota se relacionan de forma {ud.fuerza_correlacion(rho)} "
                       f"(ρ = {_num(rho)}): mirar una sola métrica deja títulos fuera.")

    if len(ranking):
        r = ranking.iloc[0]
        out.append(f"Mejor posicionado: «{_recorta(r['title'], 38)}» ({r['content_type']}, {int(r['release_year'])}), "
                   f"nota {_num(r['vote_average'], 1)} y popularidad {_num(r['popularity'], 0)}.")
    return out


def _recomendacion(df, catalogo):
    """Conclusion en lenguaje simple, segun como se compara el segmento con todo el catalogo."""
    c, cc = ud.calificados(df), ud.calificados(catalogo)
    if len(c) < 30:
        return ("Pocos títulos con calificación: la lectura es orientativa. Amplía los filtros "
                "(por ejemplo, el rango de años) antes de tomar una decisión de inversión.")
    d_nota = float(c["vote_average"].mean() - cc["vote_average"].mean())
    razon_pop = float(df["popularity"].median() / catalogo["popularity"].median())
    nota_alta, nota_baja = d_nota >= 0.15, d_nota <= -0.15
    pop_alta, pop_baja = razon_pop >= 1.15, razon_pop <= 0.85
    if nota_alta and pop_alta:
        return ("Segmento fuerte en calidad y en alcance: es un buen candidato para priorizar en la próxima "
                "inversión de contenido.")
    if nota_alta and pop_baja:
        return ("Nicho de calidad: está bien evaluado pero llega a menos gente. Conviene protegerlo y "
                "medirlo por su nota, no por su alcance.")
    if nota_baja and pop_alta:
        return ("Mucho alcance pero nota bajo el promedio: revisa la calidad antes de aumentar la inversión.")
    if nota_baja and pop_baja:
        return ("Bajo el promedio del catálogo en nota y en alcance: invertir con cautela y evaluarlo por "
                "retorno y costo, no por prestigio.")
    return ("Rendimiento cercano al promedio del catálogo: para decidir, usa popularidad y nota en conjunto "
            "(casi no se relacionan entre sí).")


# ------------------------------------------------------------------
# Piezas graficas
# ------------------------------------------------------------------
def _estilo_ejes(ax):
    for lado in ("top", "right"):
        ax.spines[lado].set_visible(False)
    for lado in ("left", "bottom"):
        ax.spines[lado].set_color(GRIS_LINEA)
    ax.tick_params(colors=GRIS_TEXTO, labelsize=7.5)
    ax.set_facecolor("none")


def _titulo_seccion(cv, x, y, texto):
    cv.text(x, y, texto, fontsize=10.5, fontweight="bold", color=AZUL, va="center", ha="left")
    cv.add_patch(Rectangle((x, y - 0.0125), 0.045, 0.0022, color=AMARILLO, lw=0))


def _tarjeta(cv, x, y, w, h, etiqueta, valor, detalle=None):
    cv.add_patch(Rectangle((x, y), w, h, facecolor=BLANCO, edgecolor=GRIS_LINEA, lw=0.8))
    cv.add_patch(Rectangle((x, y + h - 0.006), w, 0.006, color=AMARILLO, lw=0))
    cv.text(x + 0.014, y + h - 0.020, etiqueta, fontsize=7.5, color=GRIS_TEXTO, va="center")
    cv.text(x + 0.014, y + h * 0.42, valor, fontsize=19, fontweight="bold", color=NEGRO, va="center")
    if detalle:
        cv.text(x + 0.014, y + 0.012, detalle, fontsize=7, color=AZUL, va="center")


def _ranking(fig, ranking, criterio, votos_usados):
    ax = fig.add_axes([0.43, 0.470, 0.52, 0.272])
    _estilo_ejes(ax)
    n = len(ranking)
    if n == 0:
        ax.axis("off")
        ax.text(0.5, 0.5, "No hay títulos con calificación suficiente\npara armar el ranking con estos filtros.",
                ha="center", va="center", fontsize=9, color=GRIS_TEXTO, transform=ax.transAxes)
        return
    ys = list(range(n))
    valores = ranking["valor"].tolist()
    colores = [COLOR_FORMATO[t] for t in ranking["content_type"]]
    ax.barh(ys, valores, height=0.62, color=colores, edgecolor=NEGRO, linewidth=0.6)
    ax.set_ylim(n - 0.4, -0.7)           # el N.º 1 queda arriba
    ax.set_xlim(0, max(valores) * 1.20)
    ax.set_yticks([])
    ax.spines["left"].set_visible(False)
    ax.tick_params(axis="x", labelsize=7)
    ax.xaxis.grid(True, color="#E6E6E6", lw=0.6)
    ax.set_axisbelow(True)
    ax.set_xlabel(f"Ordenado de mayor a menor por {ETIQUETA_CRITERIO[criterio]}", fontsize=7.5, color=GRIS_TEXTO)

    izq = ax.get_yaxis_transform()       # x en fraccion del eje, y en datos
    for i, r in ranking.iterrows():
        ax.text(-0.02, i - 0.12, f"{i + 1}. {_recorta(r['title'], 36)}", transform=izq, ha="right",
                va="center", fontsize=8.3, fontweight="bold", color=NEGRO)
        ax.text(-0.02, i + 0.22, f"{r['content_type']} · {int(r['release_year'])} · nota {_num(r['vote_average'], 1)}"
                f" · pop. {_num(r['popularity'], 0)}", transform=izq, ha="right", va="center",
                fontsize=6.6, color=GRIS_TEXTO)
        decimales = 0 if criterio == "indice" else (1 if criterio == "nota" else 0)
        ax.text(r["valor"] + max(valores) * 0.012, i, _num(r["valor"], decimales), va="center", ha="left",
                fontsize=7.8, fontweight="bold", color=NEGRO)
    return ax


def _evolucion(fig, df):
    """Panel izquierdo: nota por año (si hay varios años) o por formato (si hay pocos)."""
    ax = fig.add_axes([0.085, 0.262, 0.355, 0.140])
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
                    "Series" if tipo == "Serie TV" else "Películas", fontsize=7.5, fontweight="bold",
                    va="center", color=NEGRO)
        lo, hi = por_anio["calif_prom"].min(), por_anio["calif_prom"].max()
        ax.set_ylim(lo - 0.25, hi + 0.25)
        ax.set_xlim(anios[0] - 0.5, anios[-1] + 2.6)
        paso = max(1, (anios[-1] - anios[0]) // 5)
        ax.set_xticks(list(range(anios[0], anios[-1] + 1, paso)))
        ax.yaxis.grid(True, color="#E6E6E6", lw=0.6)
        ax.set_axisbelow(True)
        ax.set_ylabel("Nota promedio (0–10)", fontsize=7, color=GRIS_TEXTO)
        return "Nota promedio por año de lanzamiento"
    # Pocos años: barras por formato
    c = ud.calificados(df).groupby("content_type")["vote_average"].mean()
    tipos = [t for t in ("Película", "Serie TV") if t in c.index]
    ax.bar(range(len(tipos)), [c[t] for t in tipos], color=[COLOR_FORMATO[t] for t in tipos],
           edgecolor=NEGRO, linewidth=0.6, width=0.5)
    for i, t in enumerate(tipos):
        ax.text(i, c[t] + 0.12, _num(c[t]), ha="center", fontsize=8.5, fontweight="bold")
    ax.set_xticks(range(len(tipos)))
    ax.set_xticklabels(["Series" if t == "Serie TV" else "Películas" for t in tipos], fontsize=8)
    ax.set_ylim(0, 10)
    ax.set_ylabel("Nota promedio (0–10)", fontsize=7, color=GRIS_TEXTO)
    return "Nota promedio por formato"


def _tercer_panel(fig, df, generos_filtrados):
    """Panel derecho: generos con mejor nota (si no se filtro genero) o paises con mas titulos."""
    ax = fig.add_axes([0.665, 0.262, 0.285, 0.140])
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
        extra = [f"{_miles(n)} tít." for n in t["titulos"]]
    else:
        x = ud.explode_columna(df, "country")
        t = (x.groupby("country").agg(titulos=("id_unico", "nunique")).reset_index()
             .sort_values("titulos", ascending=False).head(6))
        notas = ud.calificados(x).groupby("country")["vote_average"].mean()
        t["nota"] = t["country"].map(notas)
        titulo = "Países con más títulos"
        t["nombre"] = t["country"].map(ud.es_pais)
        valores, fmt = t["titulos"].tolist(), lambda v: _miles(v)
        extra = [f"nota {_num(n, 1)}" if n == n else "s/n" for n in t["nota"]]
    if t.empty:
        ax.axis("off")
        ax.text(0.5, 0.5, "Sin datos suficientes", ha="center", va="center", fontsize=8,
                color=GRIS_TEXTO, transform=ax.transAxes)
        return titulo
    n = len(t)
    ax.barh(range(n), valores, color=AZUL, height=0.62)
    ax.set_ylim(n - 0.4, -0.6)
    ax.set_xlim(0, max(valores) * 1.55)
    ax.set_yticks(range(n))
    ax.set_yticklabels([_recorta(s, 22) for s in t["nombre"]], fontsize=7.5, color=NEGRO)
    ax.set_xticks([])
    for i, (v, e) in enumerate(zip(valores, extra)):
        ax.text(v + max(valores) * 0.02, i, f"{fmt(v)}  ·  {e}", va="center", fontsize=6.8, color=NEGRO)
    return titulo


# ------------------------------------------------------------------
# Funcion principal
# ------------------------------------------------------------------
def construir_infografia(df, catalogo, tipos, anio_min, anio_max, votos_min, generos,
                         criterio="indice", titulo=None):
    """Arma la figura (A4). 'df' es el catalogo YA filtrado; 'catalogo' es el completo (para comparar)."""
    if df.empty or len(ud.calificados(df)) < 5:
        raise ValueError("Hay muy pocos títulos calificados con estos filtros (mínimo 5). "
                         "Amplía el rango de años o quita algún filtro.")

    votos_base = 100 if criterio == "nota" else 50
    ranking, votos_usados = ud.ranking_titulos(df, criterio, n=10, votos_min=max(votos_min, votos_base))

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
    cv.text(0.05, 0.979, "STREAMVIEW ANALYTICS · FICHA DEL SEGMENTO", fontsize=7.5, fontweight="bold",
            color=AMARILLO, va="center")
    linea_titulo = textwrap.wrap(titulo_final, width=46)[:2]
    cv.text(0.05, 0.950 if len(linea_titulo) == 1 else 0.945, "\n".join(linea_titulo),
            fontsize=19 if len(linea_titulo) == 1 else 15.5, fontweight="bold", color=BLANCO, va="center",
            linespacing=1.15)

    # ---------- 2. Introduccion ----------
    n, n_cat = len(df), len(catalogo)
    intro = (f"Este segmento reúne {_miles(n)} títulos ({_num(n / n_cat * 100, 1)}% del catálogo de {_miles(n_cat)}). "
             f"Aquí están sus cifras clave, el ranking de sus mejores títulos y la decisión que sugieren los datos.")
    cv.text(0.05, 0.893, _parrafo(intro, 100), fontsize=8.7, color=GRIS_TEXTO, va="center", linespacing=1.4)

    # ---------- Indicadores ----------
    c, cc = ud.calificados(df), ud.calificados(catalogo)
    nota = float(c["vote_average"].mean()) if len(c) else None
    nota_cat = float(cc["vote_average"].mean())
    pop, pop_cat = float(df["popularity"].median()), float(catalogo["popularity"].median())
    pct_series = float((df["content_type"] == "Serie TV").mean() * 100)
    ancho, hueco, y0, alto = 0.2075, 0.0125, 0.790, 0.078
    tarjetas = [
        ("TÍTULOS", _miles(n), f"{_num(n / n_cat * 100, 1)}% del catálogo"),
        ("NOTA PROMEDIO", f"{_num(nota)} / 10" if nota is not None else "—",
         (f"{nota - nota_cat:+.2f}".replace(".", ",") + f" vs. catálogo ({_num(nota_cat)})") if nota is not None else None),
        ("POPULARIDAD MEDIANA", _num(pop, 1), f"{_num(pop / pop_cat, 1)}× el catálogo ({_num(pop_cat, 1)})"),
        ("SERIES TV EN EL SEGMENTO", f"{pct_series:.0f}%", f"Películas: {100 - pct_series:.0f}%"),
    ]
    for i, (et, val, det) in enumerate(tarjetas):
        _tarjeta(cv, 0.05 + i * (ancho + hueco), y0, ancho, alto, et, val, det)

    # ---------- 3. Visualizaciones ----------
    _titulo_seccion(cv, 0.05, 0.768, "Ranking: los 10 mejores títulos del segmento")
    cv.text(0.95, 0.768, f"Solo títulos con {votos_usados}+ votos", fontsize=7, color=GRIS_TEXTO,
            ha="right", va="center", style="italic")
    _ranking(fig, ranking, criterio, votos_usados)
    # leyenda de colores
    x_leyenda = 0.05
    for tipo, col, et in (("Película", AMARILLO, "Película"), ("Serie TV", AZUL, "Serie TV")):
        if (df["content_type"] == tipo).any():
            cv.add_patch(Rectangle((x_leyenda, 0.448), 0.012, 0.0085, facecolor=col, edgecolor=NEGRO, lw=0.6))
            cv.text(x_leyenda + 0.017, 0.4525, et, fontsize=7.5, va="center")
            x_leyenda += 0.095

    titulo_b = _evolucion(fig, df)
    _titulo_seccion(cv, 0.05, 0.428, titulo_b)
    titulo_c = _tercer_panel(fig, df, bool(generos))
    _titulo_seccion(cv, 0.575, 0.428, titulo_c)

    # ---------- 4. Hallazgos ----------
    _titulo_seccion(cv, 0.05, 0.226, "Hallazgos principales")
    y = 0.203
    for h in _hallazgos(df, catalogo, ranking, criterio)[:4]:
        lineas = textwrap.wrap(h, width=108)
        cv.add_patch(Rectangle((0.05, y - 0.0035), 0.010, 0.0075, color=AMARILLO, ec=NEGRO, lw=0.5))
        cv.text(0.072, y - 0.0003, "\n".join(lineas), fontsize=8.4, color=NEGRO, va="center", linespacing=1.35)
        y -= 0.0140 * len(lineas) + 0.0065

    # ---------- 5. Conclusion ----------
    y_caja = 0.052
    cv.add_patch(Rectangle((0.05, y_caja), 0.90, 0.060, facecolor=AMARILLO_SUAVE, lw=0))
    cv.add_patch(Rectangle((0.05, y_caja), 0.008, 0.060, color=AMARILLO, lw=0))
    cv.text(0.072, y_caja + 0.046, "RECOMENDACIÓN", fontsize=7.5, fontweight="bold", color=AZUL, va="center")
    cv.text(0.072, y_caja + 0.022, _parrafo(_recomendacion(df, catalogo), 98), fontsize=8.8,
            fontweight="bold", color=NEGRO, va="center", linespacing=1.35)

    # ---------- Pie ----------
    nota_pie = ("Fuente: catálogo de StreamView Analytics (31.991 títulos, 2010–2025). La popularidad es un índice "
                "relativo de interés, no una cantidad de reproducciones. Nota 0 = sin calificación y no entra en los "
                "promedios. La cantidad de títulos por año la fijó la muestra, por lo que no mide el crecimiento "
                "del catálogo.")
    cv.text(0.05, 0.027, _parrafo(nota_pie, 135), fontsize=6.2, color=GRIS_TEXTO, va="center", linespacing=1.35)
    cv.add_patch(Rectangle((0, 0), 1, 0.006, color=AMARILLO, lw=0))
    return fig


def construir_informe(df, catalogo, tipos, anio_min, anio_max, votos_min, generos, criterio="indice", titulo=None):
    """Informe breve (Markdown) del segmento filtrado: mismos datos que la infografia."""
    if df.empty or len(ud.calificados(df)) < 5:
        raise ValueError("Hay muy pocos títulos calificados con estos filtros (mínimo 5). "
                         "Amplía el rango de años o quita algún filtro.")
    partes = describir_filtros(tipos, anio_min, anio_max, votos_min, generos)
    nombre = (titulo or "").strip() or (" · ".join(partes) if partes else "Todo el catálogo")
    base = max(votos_min, 100 if criterio == "nota" else 50)
    ranking, usados = ud.ranking_titulos(df, criterio=criterio, n=10, votos_min=base)
    c, cc = ud.calificados(df), ud.calificados(catalogo)
    n, n_cat = len(df), len(catalogo)
    L = [f"# Informe del segmento: {nombre}", "",
         "**StreamView Analytics** · generado desde el dashboard con los filtros activos", "",
         "## Filtros aplicados",
         f"- Formato: {', '.join(tipos) if tipos else 'todos'}",
         f"- Años: {anio_min}–{anio_max}",
         f"- Votos mínimos: {votos_min}",
         f"- Géneros: {', '.join(ud.es_genero(g) for g in generos) if generos else 'todos'}", "",
         "## Cifras clave",
         f"- Títulos: {_miles(n)} ({_num(n / n_cat * 100, 1)}% del catálogo de {_miles(n_cat)})",
         f"- Nota promedio: {_num(c['vote_average'].mean())} / 10 (catálogo: {_num(cc['vote_average'].mean())})",
         f"- Popularidad mediana: {_num(df['popularity'].median(), 1)} (catálogo: {_num(catalogo['popularity'].median(), 1)})",
         "", "## Hallazgos"]
    L += [f"- {h}" for h in _hallazgos(df, catalogo, ranking, criterio)[:4]]
    L += ["", f"## Ranking de los 10 mejores títulos (solo con {usados}+ votos)", "",
          "| N.º | Título | Formato | Año | Nota | Popularidad |", "|---|---|---|---|---|---|"]
    for i, r in ranking.iterrows():
        L.append(f"| {i + 1} | {r['title']} | {r['content_type']} | {int(r['release_year'])} | "
                 f"{_num(r['vote_average'], 1)} | {_num(r['popularity'], 0)} |")
    L += ["", "## Recomendación", _recomendacion(df, catalogo), "",
          "---", "*Nota: la popularidad es un índice relativo, no reproducciones. Nota 0 = sin calificación "
          "y no entra en los promedios. La cantidad de títulos por año la fijó la muestra.*"]
    return "\n".join(L)


def exportar(fig):
    """Devuelve (png_bytes, pdf_bytes) y libera la figura."""
    png, pdf = io.BytesIO(), io.BytesIO()
    fig.savefig(png, format="png", dpi=150, facecolor=BLANCO)
    fig.savefig(pdf, format="pdf", facecolor=BLANCO)
    plt.close(fig)
    return png.getvalue(), pdf.getvalue()

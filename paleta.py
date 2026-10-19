"""
paleta.py - Paleta de StreamView Analytics (colores de Duoc UC)

REGLA UNICA: el mismo color significa siempre lo mismo.
    Amarillo     = Peliculas
    Azul oscuro  = Series TV
    Negro        = solo texto
El gris se usa solo como apoyo (ejes, lineas guia, fondos).
"""

# --- Colores institucionales de Duoc UC ---
AMARILLO = "#FCB426"   # amarillo del logo (medido en el logo oficial; Pantone 1225 C / 116 U)
AZUL = "#00263E"       # azul oscuro (aprox. digital del Pantone 2965 C de los manuales 2021-2022)
NEGRO = "#000000"      # negro corporativo (manual 2024): se usa solo para texto
BLANCO = "#FFFFFF"

# --- Neutros de apoyo (nunca para representar datos principales) ---
GRIS_TEXTO = "#4D4D4D"
GRIS_LINEA = "#BFBFBF"
GRIS_FONDO = "#F5F5F5"
AMARILLO_SUAVE = "#FFF6E0"   # fondo de las cajas de "respuesta corta"

COLOR_FORMATO = {"Película": AMARILLO, "Serie TV": AZUL}

# Escala de un solo matiz (mas oscuro = valor mas alto), para Series TV
ESCALA_SERIE = ["#DCE6EE", "#6F93AD", AZUL]


def layout_base():
    """Estilo comun para los graficos Plotly (se usa con **LAYOUT_BASE)."""
    return dict(
        template="plotly_white",
        font=dict(family='Inter, "Segoe UI", sans-serif', size=13, color=NEGRO),
        title_font=dict(size=16, color=NEGRO),
        margin=dict(l=10, r=10, t=60, b=10),
    )

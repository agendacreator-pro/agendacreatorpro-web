"""
Template engine: predefined layouts with EXACT element positions.
AI only provides colors/fonts/decorations. Templates provide structure.
All coordinates in mm for A5 (148×210).
"""


def _apply_colors(elements, colors):
    color_map = {}
    for c in colors:
        role = c.get("role", "")
        hex_val = c.get("hex", "")
        if role and hex_val:
            color_map[role] = hex_val

    bg = color_map.get("background", "#FFFFFF")
    accent = color_map.get("accent", "#4A90D9")
    primary = color_map.get("primary", "#2D2D2D")
    text_color = color_map.get("text", "#555555")
    border = color_map.get("border", "#E0E0E0")
    highlight = color_map.get("highlight", "#F0F6FF")
    secondary = color_map.get("secondary", "#F5F5F5")

    result = []
    for el in elements:
        new_el = dict(el)
        c = new_el.get("color", "")
        bg_c = new_el.get("bg_color", "")
        bc = new_el.get("border_color", "")

        if c == "_accent_":
            new_el["color"] = accent
        elif c == "_primary_":
            new_el["color"] = primary
        elif c == "_text_":
            new_el["color"] = text_color
        elif c == "_white_":
            new_el["color"] = "#FFFFFF"
        elif c == "_border_":
            new_el["color"] = border

        if bg_c == "_accent_":
            new_el["bg_color"] = accent
        elif bg_c == "_highlight_":
            new_el["bg_color"] = highlight
        elif bg_c == "_secondary_":
            new_el["bg_color"] = secondary
        elif bg_c == "_white_":
            new_el["bg_color"] = "#FFFFFF"

        if bc == "_accent_":
            new_el["border_color"] = accent
        elif bc == "_border_":
            new_el["border_color"] = border

        result.append(new_el)
    return result


def template_1dpp(colors=None):
    """Daily page: header + priorities left + notes left + schedule right."""
    els = [
        # === HEADER BAR ===
        {"type": "rect", "x": 0, "y": 0, "w": 148, "h": 28, "bg_color": "_accent_", "border": False},
        {"type": "text", "x": 10, "y": 3, "w": 50, "h": 8, "text": "TERCA", "font_name": "Helvetica-Bold", "font_size": 10, "color": "_white_", "bold": True, "align": "left"},
        {"type": "text", "x": 10, "y": 11, "w": 25, "h": 14, "text": "15", "font_name": "Helvetica-Bold", "font_size": 28, "color": "_white_", "bold": True, "align": "left"},
        {"type": "text", "x": 38, "y": 14, "w": 50, "h": 7, "text": "julho 2026", "font_name": "Helvetica", "font_size": 9, "color": "_white_", "align": "left"},

        # === ACCENT LINE ===
        {"type": "line", "x": 0, "y": 28, "w": 148, "h": 0, "color": "_accent_", "border_width": 1.5},

        # === LEFT COLUMN: PRIORIDADES ===
        {"type": "text", "x": 8, "y": 31, "w": 35, "h": 6, "text": "PRIORIDADES", "font_name": "Helvetica-Bold", "font_size": 7, "color": "_accent_", "bold": True},

        # Priority box 1
        {"type": "rect", "x": 8, "y": 38, "w": 62, "h": 10, "bg_color": "_highlight_", "border": True, "border_color": "_accent_", "border_width": 0.3, "radius": 2},
        {"type": "circle", "x": 10, "y": 40.5, "w": 3.5, "h": 3.5, "color": "_accent_"},
        {"type": "text", "x": 15, "y": 40, "w": 52, "h": 5, "text": "Revisar material do curso", "font_name": "Helvetica", "font_size": 6, "color": "_text_"},

        # Priority box 2
        {"type": "rect", "x": 8, "y": 50, "w": 62, "h": 10, "bg_color": "_highlight_", "border": True, "border_color": "_accent_", "border_width": 0.3, "radius": 2},
        {"type": "circle", "x": 10, "y": 52.5, "w": 3.5, "h": 3.5, "color": "_accent_"},
        {"type": "text", "x": 15, "y": 52, "w": 52, "h": 5, "text": "Enviar trabalho final", "font_name": "Helvetica", "font_size": 6, "color": "_text_"},

        # Priority box 3
        {"type": "rect", "x": 8, "y": 62, "w": 62, "h": 10, "bg_color": "_highlight_", "border": True, "border_color": "_accent_", "border_width": 0.3, "radius": 2},
        {"type": "circle", "x": 10, "y": 64.5, "w": 3.5, "h": 3.5, "color": "_accent_"},
        {"type": "text", "x": 15, "y": 64, "w": 52, "h": 5, "text": "Preparar apresentacao", "font_name": "Helvetica", "font_size": 6, "color": "_text_"},

        # === DIVIDER ===
        {"type": "line", "x": 8, "y": 76, "w": 62, "h": 0, "color": "_border_", "border_width": 0.5},

        # === LEFT COLUMN: ANOTACOES ===
        {"type": "text", "x": 8, "y": 79, "w": 35, "h": 6, "text": "ANOTACOES", "font_name": "Helvetica-Bold", "font_size": 7, "color": "_accent_", "bold": True},

        # Notes background
        {"type": "rect", "x": 8, "y": 87, "w": 62, "h": 115, "bg_color": "_white_", "border": True, "border_color": "_border_", "border_width": 0.3},

        # Ruled lines (every ~8mm from y=95 to y=195)
        {"type": "line", "x": 10, "y": 95, "w": 58, "h": 0, "color": "_border_", "border_width": 0.2},
        {"type": "line", "x": 10, "y": 103, "w": 58, "h": 0, "color": "_border_", "border_width": 0.2},
        {"type": "line", "x": 10, "y": 111, "w": 58, "h": 0, "color": "_border_", "border_width": 0.2},
        {"type": "line", "x": 10, "y": 119, "w": 58, "h": 0, "color": "_border_", "border_width": 0.2},
        {"type": "line", "x": 10, "y": 127, "w": 58, "h": 0, "color": "_border_", "border_width": 0.2},
        {"type": "line", "x": 10, "y": 135, "w": 58, "h": 0, "color": "_border_", "border_width": 0.2},
        {"type": "line", "x": 10, "y": 143, "w": 58, "h": 0, "color": "_border_", "border_width": 0.2},
        {"type": "line", "x": 10, "y": 151, "w": 58, "h": 0, "color": "_border_", "border_width": 0.2},
        {"type": "line", "x": 10, "y": 159, "w": 58, "h": 0, "color": "_border_", "border_width": 0.2},
        {"type": "line", "x": 10, "y": 167, "w": 58, "h": 0, "color": "_border_", "border_width": 0.2},
        {"type": "line", "x": 10, "y": 175, "w": 58, "h": 0, "color": "_border_", "border_width": 0.2},
        {"type": "line", "x": 10, "y": 183, "w": 58, "h": 0, "color": "_border_", "border_width": 0.2},
        {"type": "line", "x": 10, "y": 191, "w": 58, "h": 0, "color": "_border_", "border_width": 0.2},

        # === VERTICAL DIVIDER ===
        {"type": "line", "x": 74, "y": 31, "w": 0, "h": 172, "color": "_border_", "border_width": 0.5},

        # === RIGHT COLUMN: AGENDAMENTOS ===
        {"type": "text", "x": 78, "y": 31, "w": 35, "h": 6, "text": "AGENDAMENTOS", "font_name": "Helvetica-Bold", "font_size": 7, "color": "_accent_", "bold": True},

        # Time slots 08:00 to 18:00
        {"type": "text", "x": 78, "y": 40, "w": 12, "h": 5, "text": "08:00", "font_name": "Helvetica", "font_size": 5, "color": "_text_"},
        {"type": "line", "x": 92, "y": 44, "w": 48, "h": 0, "color": "_border_", "border_width": 0.2},

        {"type": "text", "x": 78, "y": 48, "w": 12, "h": 5, "text": "09:00", "font_name": "Helvetica", "font_size": 5, "color": "_text_"},
        {"type": "line", "x": 92, "y": 52, "w": 48, "h": 0, "color": "_border_", "border_width": 0.2},

        {"type": "text", "x": 78, "y": 56, "w": 12, "h": 5, "text": "10:00", "font_name": "Helvetica", "font_size": 5, "color": "_text_"},
        {"type": "line", "x": 92, "y": 60, "w": 48, "h": 0, "color": "_border_", "border_width": 0.2},

        {"type": "text", "x": 78, "y": 64, "w": 12, "h": 5, "text": "11:00", "font_name": "Helvetica", "font_size": 5, "color": "_text_"},
        {"type": "line", "x": 92, "y": 68, "w": 48, "h": 0, "color": "_border_", "border_width": 0.2},

        {"type": "text", "x": 78, "y": 72, "w": 12, "h": 5, "text": "12:00", "font_name": "Helvetica", "font_size": 5, "color": "_text_"},
        {"type": "line", "x": 92, "y": 76, "w": 48, "h": 0, "color": "_border_", "border_width": 0.2},

        {"type": "text", "x": 78, "y": 80, "w": 12, "h": 5, "text": "13:00", "font_name": "Helvetica", "font_size": 5, "color": "_text_"},
        {"type": "line", "x": 92, "y": 84, "w": 48, "h": 0, "color": "_border_", "border_width": 0.2},

        {"type": "text", "x": 78, "y": 88, "w": 12, "h": 5, "text": "14:00", "font_name": "Helvetica", "font_size": 5, "color": "_text_"},
        {"type": "line", "x": 92, "y": 92, "w": 48, "h": 0, "color": "_border_", "border_width": 0.2},

        {"type": "text", "x": 78, "y": 96, "w": 12, "h": 5, "text": "15:00", "font_name": "Helvetica", "font_size": 5, "color": "_text_"},
        {"type": "line", "x": 92, "y": 100, "w": 48, "h": 0, "color": "_border_", "border_width": 0.2},

        {"type": "text", "x": 78, "y": 104, "w": 12, "h": 5, "text": "16:00", "font_name": "Helvetica", "font_size": 5, "color": "_text_"},
        {"type": "line", "x": 92, "y": 108, "w": 48, "h": 0, "color": "_border_", "border_width": 0.2},

        {"type": "text", "x": 78, "y": 112, "w": 12, "h": 5, "text": "17:00", "font_name": "Helvetica", "font_size": 5, "color": "_text_"},
        {"type": "line", "x": 92, "y": 116, "w": 48, "h": 0, "color": "_border_", "border_width": 0.2},

        {"type": "text", "x": 78, "y": 120, "w": 12, "h": 5, "text": "18:00", "font_name": "Helvetica", "font_size": 5, "color": "_text_"},
        {"type": "line", "x": 92, "y": 124, "w": 48, "h": 0, "color": "_border_", "border_width": 0.2},

        # === BOTTOM AREA (y>130) ===
        {"type": "line", "x": 78, "y": 130, "w": 60, "h": 0, "color": "_border_", "border_width": 0.5},

        # Bottom notes/space
        {"type": "rect", "x": 78, "y": 134, "w": 60, "h": 68, "bg_color": "_secondary_", "border": True, "border_color": "_border_", "border_width": 0.3},
        {"type": "line", "x": 80, "y": 142, "w": 56, "h": 0, "color": "_border_", "border_width": 0.2},
        {"type": "line", "x": 80, "y": 150, "w": 56, "h": 0, "color": "_border_", "border_width": 0.2},
        {"type": "line", "x": 80, "y": 158, "w": 56, "h": 0, "color": "_border_", "border_width": 0.2},
        {"type": "line", "x": 80, "y": 166, "w": 56, "h": 0, "color": "_border_", "border_width": 0.2},
        {"type": "line", "x": 80, "y": 174, "w": 56, "h": 0, "color": "_border_", "border_width": 0.2},
        {"type": "line", "x": 80, "y": 182, "w": 56, "h": 0, "color": "_border_", "border_width": 0.2},
        {"type": "line", "x": 80, "y": 190, "w": 56, "h": 0, "color": "_border_", "border_width": 0.2},

        # Footer
        {"type": "text", "x": 60, "y": 203, "w": 28, "h": 5, "text": "1 / 365", "font_name": "Helvetica", "font_size": 5, "color": "_text_", "align": "center"},
    ]

    if colors:
        els = _apply_colors(els, colors)
    return els


def template_dados_pessoais(colors=None):
    """Personal data page."""
    els = [
        {"type": "rect", "x": 0, "y": 0, "w": 148, "h": 28, "bg_color": "_accent_", "border": False},
        {"type": "text", "x": 10, "y": 8, "w": 128, "h": 12, "text": "DADOS PESSOAIS", "font_name": "Helvetica-Bold", "font_size": 16, "color": "_white_", "bold": True, "align": "center"},
        {"type": "line", "x": 0, "y": 28, "w": 148, "h": 0, "color": "_accent_", "border_width": 1.5},

        {"type": "text", "x": 15, "y": 40, "w": 35, "h": 6, "text": "Nome:", "font_name": "Helvetica-Bold", "font_size": 8, "color": "_primary_", "bold": True},
        {"type": "line", "x": 50, "y": 45, "w": 85, "h": 0, "color": "_border_", "border_width": 0.3},

        {"type": "text", "x": 15, "y": 55, "w": 35, "h": 6, "text": "E-mail:", "font_name": "Helvetica-Bold", "font_size": 8, "color": "_primary_", "bold": True},
        {"type": "line", "x": 50, "y": 60, "w": 85, "h": 0, "color": "_border_", "border_width": 0.3},

        {"type": "text", "x": 15, "y": 70, "w": 35, "h": 6, "text": "Telefone:", "font_name": "Helvetica-Bold", "font_size": 8, "color": "_primary_", "bold": True},
        {"type": "line", "x": 50, "y": 75, "w": 85, "h": 0, "color": "_border_", "border_width": 0.3},

        {"type": "text", "x": 15, "y": 85, "w": 35, "h": 6, "text": "Endereco:", "font_name": "Helvetica-Bold", "font_size": 8, "color": "_primary_", "bold": True},
        {"type": "line", "x": 50, "y": 90, "w": 85, "h": 0, "color": "_border_", "border_width": 0.3},

        {"type": "text", "x": 15, "y": 100, "w": 35, "h": 6, "text": "Nascimento:", "font_name": "Helvetica-Bold", "font_size": 8, "color": "_primary_", "bold": True},
        {"type": "line", "x": 50, "y": 105, "w": 85, "h": 0, "color": "_border_", "border_width": 0.3},

        {"type": "text", "x": 15, "y": 115, "w": 35, "h": 6, "text": "Profissao:", "font_name": "Helvetica-Bold", "font_size": 8, "color": "_primary_", "bold": True},
        {"type": "line", "x": 50, "y": 120, "w": 85, "h": 0, "color": "_border_", "border_width": 0.3},

        {"type": "text", "x": 15, "y": 135, "w": 35, "h": 6, "text": "Observacoes:", "font_name": "Helvetica-Bold", "font_size": 8, "color": "_primary_", "bold": True},
        {"type": "rect", "x": 15, "y": 143, "w": 118, "h": 50, "bg_color": "_secondary_", "border": True, "border_color": "_border_", "border_width": 0.3},
        {"type": "line", "x": 17, "y": 151, "w": 114, "h": 0, "color": "_border_", "border_width": 0.2},
        {"type": "line", "x": 17, "y": 159, "w": 114, "h": 0, "color": "_border_", "border_width": 0.2},
        {"type": "line", "x": 17, "y": 167, "w": 114, "h": 0, "color": "_border_", "border_width": 0.2},
        {"type": "line", "x": 17, "y": 175, "w": 114, "h": 0, "color": "_border_", "border_width": 0.2},
        {"type": "line", "x": 17, "y": 183, "w": 114, "h": 0, "color": "_border_", "border_width": 0.2},
    ]
    if colors:
        els = _apply_colors(els, colors)
    return els


def template_planejamento(colors=None):
    """Weekly planning page: 7 rows (Mon-Sun) with time blocks."""
    els = [
        {"type": "rect", "x": 0, "y": 0, "w": 148, "h": 28, "bg_color": "_accent_", "border": False},
        {"type": "text", "x": 10, "y": 8, "w": 128, "h": 12, "text": "PLANEJAMENTO SEMANAL", "font_name": "Helvetica-Bold", "font_size": 14, "color": "_white_", "bold": True, "align": "center"},
        {"type": "line", "x": 0, "y": 28, "w": 148, "h": 0, "color": "_accent_", "border_width": 1.5},

        # Column headers
        {"type": "text", "x": 8, "y": 32, "w": 18, "h": 5, "text": "Hora", "font_name": "Helvetica-Bold", "font_size": 6, "color": "_accent_", "bold": True, "align": "center"},
        {"type": "text", "x": 28, "y": 32, "w": 14, "h": 5, "text": "SEG", "font_name": "Helvetica-Bold", "font_size": 5, "color": "_accent_", "bold": True, "align": "center"},
        {"type": "text", "x": 44, "y": 32, "w": 14, "h": 5, "text": "TER", "font_name": "Helvetica-Bold", "font_size": 5, "color": "_accent_", "bold": True, "align": "center"},
        {"type": "text", "x": 60, "y": 32, "w": 14, "h": 5, "text": "QUA", "font_name": "Helvetica-Bold", "font_size": 5, "color": "_accent_", "bold": True, "align": "center"},
        {"type": "text", "x": 76, "y": 32, "w": 14, "h": 5, "text": "QUI", "font_name": "Helvetica-Bold", "font_size": 5, "color": "_accent_", "bold": True, "align": "center"},
        {"type": "text", "x": 92, "y": 32, "w": 14, "h": 5, "text": "SEX", "font_name": "Helvetica-Bold", "font_size": 5, "color": "_accent_", "bold": True, "align": "center"},
        {"type": "text", "x": 108, "y": 32, "w": 14, "h": 5, "text": "SAB", "font_name": "Helvetica-Bold", "font_size": 5, "color": "_accent_", "bold": True, "align": "center"},
        {"type": "text", "x": 124, "y": 32, "w": 14, "h": 5, "text": "DOM", "font_name": "Helvetica-Bold", "font_size": 5, "color": "_accent_", "bold": True, "align": "center"},

        # Time grid lines (08:00-18:00)
        {"type": "line", "x": 8, "y": 38, "w": 132, "h": 0, "color": "_border_", "border_width": 0.3},

        {"type": "text", "x": 8, "y": 40, "w": 18, "h": 5, "text": "08:00", "font_name": "Helvetica", "font_size": 5, "color": "_text_", "align": "center"},
        {"type": "line", "x": 8, "y": 50, "w": 132, "h": 0, "color": "_border_", "border_width": 0.2},
        {"type": "text", "x": 8, "y": 52, "w": 18, "h": 5, "text": "09:00", "font_name": "Helvetica", "font_size": 5, "color": "_text_", "align": "center"},
        {"type": "line", "x": 8, "y": 62, "w": 132, "h": 0, "color": "_border_", "border_width": 0.2},
        {"type": "text", "x": 8, "y": 64, "w": 18, "h": 5, "text": "10:00", "font_name": "Helvetica", "font_size": 5, "color": "_text_", "align": "center"},
        {"type": "line", "x": 8, "y": 74, "w": 132, "h": 0, "color": "_border_", "border_width": 0.2},
        {"type": "text", "x": 8, "y": 76, "w": 18, "h": 5, "text": "11:00", "font_name": "Helvetica", "font_size": 5, "color": "_text_", "align": "center"},
        {"type": "line", "x": 8, "y": 86, "w": 132, "h": 0, "color": "_border_", "border_width": 0.2},
        {"type": "text", "x": 8, "y": 88, "w": 18, "h": 5, "text": "12:00", "font_name": "Helvetica", "font_size": 5, "color": "_text_", "align": "center"},
        {"type": "line", "x": 8, "y": 98, "w": 132, "h": 0, "color": "_border_", "border_width": 0.2},
        {"type": "text", "x": 8, "y": 100, "w": 18, "h": 5, "text": "13:00", "font_name": "Helvetica", "font_size": 5, "color": "_text_", "align": "center"},
        {"type": "line", "x": 8, "y": 110, "w": 132, "h": 0, "color": "_border_", "border_width": 0.2},
        {"type": "text", "x": 8, "y": 112, "w": 18, "h": 5, "text": "14:00", "font_name": "Helvetica", "font_size": 5, "color": "_text_", "align": "center"},
        {"type": "line", "x": 8, "y": 122, "w": 132, "h": 0, "color": "_border_", "border_width": 0.2},
        {"type": "text", "x": 8, "y": 124, "w": 18, "h": 5, "text": "15:00", "font_name": "Helvetica", "font_size": 5, "color": "_text_", "align": "center"},
        {"type": "line", "x": 8, "y": 134, "w": 132, "h": 0, "color": "_border_", "border_width": 0.2},
        {"type": "text", "x": 8, "y": 136, "w": 18, "h": 5, "text": "16:00", "font_name": "Helvetica", "font_size": 5, "color": "_text_", "align": "center"},
        {"type": "line", "x": 8, "y": 146, "w": 132, "h": 0, "color": "_border_", "border_width": 0.2},
        {"type": "text", "x": 8, "y": 148, "w": 18, "h": 5, "text": "17:00", "font_name": "Helvetica", "font_size": 5, "color": "_text_", "align": "center"},
        {"type": "line", "x": 8, "y": 158, "w": 132, "h": 0, "color": "_border_", "border_width": 0.2},

        # Vertical column dividers
        {"type": "line", "x": 26, "y": 38, "w": 0, "h": 120, "color": "_border_", "border_width": 0.2},
        {"type": "line", "x": 42, "y": 38, "w": 0, "h": 120, "color": "_border_", "border_width": 0.2},
        {"type": "line", "x": 58, "y": 38, "w": 0, "h": 120, "color": "_border_", "border_width": 0.2},
        {"type": "line", "x": 74, "y": 38, "w": 0, "h": 120, "color": "_border_", "border_width": 0.2},
        {"type": "line", "x": 90, "y": 38, "w": 0, "h": 120, "color": "_border_", "border_width": 0.2},
        {"type": "line", "x": 106, "y": 38, "w": 0, "h": 120, "color": "_border_", "border_width": 0.2},
        {"type": "line", "x": 122, "y": 38, "w": 0, "h": 120, "color": "_border_", "border_width": 0.2},

        # Bottom notes
        {"type": "text", "x": 8, "y": 165, "w": 35, "h": 6, "text": "METAS DA SEMANA", "font_name": "Helvetica-Bold", "font_size": 7, "color": "_accent_", "bold": True},
        {"type": "rect", "x": 8, "y": 173, "w": 132, "h": 30, "bg_color": "_secondary_", "border": True, "border_color": "_border_", "border_width": 0.3},
        {"type": "line", "x": 10, "y": 181, "w": 128, "h": 0, "color": "_border_", "border_width": 0.2},
        {"type": "line", "x": 10, "y": 189, "w": 128, "h": 0, "color": "_border_", "border_width": 0.2},
        {"type": "line", "x": 10, "y": 197, "w": 128, "h": 0, "color": "_border_", "border_width": 0.2},
    ]
    if colors:
        els = _apply_colors(els, colors)
    return els


def template_semanal(colors=None):
    """Weekly view: 7 day columns."""
    els = [
        {"type": "rect", "x": 0, "y": 0, "w": 148, "h": 28, "bg_color": "_accent_", "border": False},
        {"type": "text", "x": 10, "y": 8, "w": 128, "h": 12, "text": "AGENDA SEMANAL", "font_name": "Helvetica-Bold", "font_size": 14, "color": "_white_", "bold": True, "align": "center"},
        {"type": "line", "x": 0, "y": 28, "w": 148, "h": 0, "color": "_accent_", "border_width": 1.5},

        # 7 columns with day names
        {"type": "text", "x": 4, "y": 31, "w": 18, "h": 5, "text": "SEG 14", "font_name": "Helvetica-Bold", "font_size": 5, "color": "_accent_", "bold": True, "align": "center"},
        {"type": "text", "x": 24, "y": 31, "w": 18, "h": 5, "text": "TER 15", "font_name": "Helvetica-Bold", "font_size": 5, "color": "_accent_", "bold": True, "align": "center"},
        {"type": "text", "x": 44, "y": 31, "w": 18, "h": 5, "text": "QUA 16", "font_name": "Helvetica-Bold", "font_size": 5, "color": "_accent_", "bold": True, "align": "center"},
        {"type": "text", "x": 64, "y": 31, "w": 18, "h": 5, "text": "QUI 17", "font_name": "Helvetica-Bold", "font_size": 5, "color": "_accent_", "bold": True, "align": "center"},
        {"type": "text", "x": 84, "y": 31, "w": 18, "h": 5, "text": "SEX 18", "font_name": "Helvetica-Bold", "font_size": 5, "color": "_accent_", "bold": True, "align": "center"},
        {"type": "text", "x": 104, "y": 31, "w": 18, "h": 5, "text": "SAB 19", "font_name": "Helvetica-Bold", "font_size": 5, "color": "_accent_", "bold": True, "align": "center"},
        {"type": "text", "x": 124, "y": 31, "w": 18, "h": 5, "text": "DOM 20", "font_name": "Helvetica-Bold", "font_size": 5, "color": "_accent_", "bold": True, "align": "center"},

        # Column lines
        {"type": "line", "x": 22, "y": 30, "w": 0, "h": 172, "color": "_border_", "border_width": 0.3},
        {"type": "line", "x": 42, "y": 30, "w": 0, "h": 172, "color": "_border_", "border_width": 0.3},
        {"type": "line", "x": 62, "y": 30, "w": 0, "h": 172, "color": "_border_", "border_width": 0.3},
        {"type": "line", "x": 82, "y": 30, "w": 0, "h": 172, "color": "_border_", "border_width": 0.3},
        {"type": "line", "x": 102, "y": 30, "w": 0, "h": 172, "color": "_border_", "border_width": 0.3},
        {"type": "line", "x": 122, "y": 30, "w": 0, "h": 172, "color": "_border_", "border_width": 0.3},

        # Horizontal time lines in each column
        {"type": "line", "x": 2, "y": 50, "w": 144, "h": 0, "color": "_border_", "border_width": 0.15},
        {"type": "line", "x": 2, "y": 70, "w": 144, "h": 0, "color": "_border_", "border_width": 0.15},
        {"type": "line", "x": 2, "y": 90, "w": 144, "h": 0, "color": "_border_", "border_width": 0.15},
        {"type": "line", "x": 2, "y": 110, "w": 144, "h": 0, "color": "_border_", "border_width": 0.15},
        {"type": "line", "x": 2, "y": 130, "w": 144, "h": 0, "color": "_border_", "border_width": 0.15},
        {"type": "line", "x": 2, "y": 150, "w": 144, "h": 0, "color": "_border_", "border_width": 0.15},
        {"type": "line", "x": 2, "y": 170, "w": 144, "h": 0, "color": "_border_", "border_width": 0.15},
        {"type": "line", "x": 2, "y": 190, "w": 144, "h": 0, "color": "_border_", "border_width": 0.15},

        # Time labels
        {"type": "text", "x": 2, "y": 41, "w": 10, "h": 4, "text": "08", "font_name": "Helvetica", "font_size": 4, "color": "_text_", "align": "center"},
        {"type": "text", "x": 2, "y": 61, "w": 10, "h": 4, "text": "10", "font_name": "Helvetica", "font_size": 4, "color": "_text_", "align": "center"},
        {"type": "text", "x": 2, "y": 81, "w": 10, "h": 4, "text": "12", "font_name": "Helvetica", "font_size": 4, "color": "_text_", "align": "center"},
        {"type": "text", "x": 2, "y": 101, "w": 10, "h": 4, "text": "14", "font_name": "Helvetica", "font_size": 4, "color": "_text_", "align": "center"},
        {"type": "text", "x": 2, "y": 121, "w": 10, "h": 4, "text": "16", "font_name": "Helvetica", "font_size": 4, "color": "_text_", "align": "center"},
        {"type": "text", "x": 2, "y": 141, "w": 10, "h": 4, "text": "18", "font_name": "Helvetica", "font_size": 4, "color": "_text_", "align": "center"},
        {"type": "text", "x": 2, "y": 161, "w": 10, "h": 4, "text": "20", "font_name": "Helvetica", "font_size": 4, "color": "_text_", "align": "center"},
    ]
    if colors:
        els = _apply_colors(els, colors)
    return els


def template_notas(colors=None):
    """Notes page: full lined area."""
    els = [
        {"type": "rect", "x": 0, "y": 0, "w": 148, "h": 28, "bg_color": "_accent_", "border": False},
        {"type": "text", "x": 10, "y": 8, "w": 128, "h": 12, "text": "ANOTACOES", "font_name": "Helvetica-Bold", "font_size": 14, "color": "_white_", "bold": True, "align": "center"},
        {"type": "line", "x": 0, "y": 28, "w": 148, "h": 0, "color": "_accent_", "border_width": 1.5},

        {"type": "rect", "x": 8, "y": 32, "w": 132, "h": 170, "bg_color": "_white_", "border": True, "border_color": "_border_", "border_width": 0.3},
    ]
    for i in range(21):
        y = 40 + i * 8
        els.append({"type": "line", "x": 10, "y": y, "w": 128, "h": 0, "color": "_border_", "border_width": 0.2})
    if colors:
        els = _apply_colors(els, colors)
    return els


def template_checklist(colors=None):
    """Checklist page with checkboxes."""
    els = [
        {"type": "rect", "x": 0, "y": 0, "w": 148, "h": 28, "bg_color": "_accent_", "border": False},
        {"type": "text", "x": 10, "y": 8, "w": 128, "h": 12, "text": "CHECKLIST", "font_name": "Helvetica-Bold", "font_size": 14, "color": "_white_", "bold": True, "align": "center"},
        {"type": "line", "x": 0, "y": 28, "w": 148, "h": 0, "color": "_accent_", "border_width": 1.5},
    ]
    for i in range(20):
        y = 36 + i * 8
        els.append({"type": "circle", "x": 12, "y": y, "w": 4, "h": 4, "color": "_accent_"})
        els.append({"type": "line", "x": 20, "y": y + 4, "w": 118, "h": 0, "color": "_border_", "border_width": 0.2})
    if colors:
        els = _apply_colors(els, colors)
    return els


TEMPLATES = {
    "1dpp": template_1dpp,
    "dados_pessoais": template_dados_pessoais,
    "planejamento": template_planejamento,
    "semanal": template_semanal,
    "notas": template_notas,
    "checklist": template_checklist,
    "mensal": template_semanal,
    "calendario": template_semanal,
    "metas": template_notas,
    "divisoria": template_notas,
}


def get_template(page_type, colors=None):
    fn = TEMPLATES.get(page_type, template_1dpp)
    return fn(colors)

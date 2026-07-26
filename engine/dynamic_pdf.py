from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
from reportlab.lib.colors import HexColor, white, black
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT


def _parse_color(hex_str, fallback="#000000"):
    if not hex_str:
        return HexColor(fallback)
    try:
        return HexColor(hex_str)
    except Exception:
        return HexColor(fallback)


def _align(align_str):
    m = {"center": TA_CENTER, "right": TA_RIGHT}
    return m.get(align_str, TA_LEFT)


def _font_name(name, bold=False, italic=False):
    safe = (name or "Helvetica").replace(" ", "-").replace("_", "-")
    fonts = {
        "Helvetica": True, "Helvetica-Bold": True, "Helvetica-Oblique": True,
        "Helvetica-BoldOblique": True, "Times-Roman": True, "Times-Bold": True,
        "Times-Italic": True, "Times-BoldItalic": True, "Courier": True,
        "Courier-Bold": True, "Courier-Oblique": True, "Courier-BoldOblique": True,
    }
    if safe in fonts:
        if bold and "Bold" not in safe:
            if safe.startswith("Helvetica"):
                return "Helvetica-Bold"
            if safe.startswith("Times"):
                return "Times-Bold"
            if safe.startswith("Courier"):
                return "Courier-Bold"
        return safe
    return "Helvetica-Bold" if bold else "Helvetica"


PAGE_SIZES = {
    "A5": (148 * mm, 210 * mm),
    "A4": (210 * mm, 297 * mm),
    "QUADRADO": (150 * mm, 150 * mm),
}


def gerar_pdf_da_analise(analysis_dict, formato="A5"):
    pa = analysis_dict.get("page_analysis", analysis_dict)
    elements = pa.get("elements", [])
    colors = pa.get("colors", [])

    w, h = PAGE_SIZES.get(formato.upper(), PAGE_SIZES["A5"])

    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=(w, h))
    pdf.setPageCompression(0)

    bg_color = "#FFFFFF"
    for c in colors:
        if c.get("role") in ("background", "secondary") and c.get("hex"):
            bg_color = c["hex"]
            break

    pdf.setFillColor(_parse_color(bg_color))
    pdf.rect(0, 0, w, h, fill=1, stroke=0)

    _draw_elements(pdf, elements, w, h)

    pdf.save()
    buffer.seek(0)
    return buffer


def _draw_elements(pdf, elements, page_w, page_h):
    for el in elements:
        etype = el.get("type", "rect")
        x_mm = float(el.get("x", 0) or 0)
        y_mm = float(el.get("y", 0) or 0)
        w_mm = float(el.get("w", 0) or 0)
        h_mm = float(el.get("h", 0) or 0)

        x = x_mm * mm
        y_pdf = page_h - (y_mm * mm) - (h_mm * mm)
        w = w_mm * mm
        h = h_mm * mm

        color = _parse_color(el.get("color", "#000000"))
        bg = _parse_color(el.get("bg_color")) if el.get("bg_color") else None
        border_color = _parse_color(el.get("border_color", "#E0E0E0"))
        border_w = float(el.get("border_width", 0.5) or 0.5)
        bold = bool(el.get("bold"))
        italic = bool(el.get("italic"))
        font_name = _font_name(el.get("font_name"), bold, italic)
        font_size = float(el.get("font_size", 10) or 10)
        opacity = float(el.get("opacity", 1.0) or 1.0)
        align = el.get("align", "left")

        if opacity < 1.0:
            pdf.saveState()
            pdf.setFillColor(color, opacity)
        else:
            pdf.setFillColor(color)

        if etype in ("rect", "box"):
            if bg:
                pdf.setFillColor(bg)
                pdf.rect(x, y_pdf, w, h, fill=1, stroke=0)
            if el.get("border"):
                pdf.setStrokeColor(border_color)
                pdf.setLineWidth(border_w)
                pdf.rect(x, y_pdf, w, h, fill=0, stroke=1)
            if opacity < 1.0:
                pdf.restoreState()

        elif etype == "line":
            pdf.setStrokeColor(color)
            pdf.setLineWidth(border_w)
            pdf.line(x, y_pdf, x + w, y_pdf + h)

        elif etype == "circle":
            if bg:
                pdf.setFillColor(bg)
                pdf.circle(x + w / 2, y_pdf + h / 2, min(w, h) / 2, fill=1, stroke=0)
            if el.get("border"):
                pdf.setStrokeColor(border_color)
                pdf.setLineWidth(border_w)
                pdf.circle(x + w / 2, y_pdf + h / 2, min(w, h) / 2, fill=0, stroke=1)

        elif etype == "text":
            text = el.get("text", "")
            if bg:
                pdf.setFillColor(bg)
                pdf.rect(x, y_pdf, w, h, fill=1, stroke=0)
            pdf.setFillColor(color)
            pdf.setFont(font_name, font_size)
            line_h = float(el.get("line_height", font_size + 4) or font_size + 4) * mm
            lines = text.split("\n")
            for i, line in enumerate(lines):
                ly = y_pdf + h - (i + 1) * line_h
                if ly < y_pdf:
                    break
                if align == "center":
                    pdf.drawCentredString(x + w / 2, ly, line)
                elif align == "right":
                    pdf.drawRightString(x + w, ly, line)
                else:
                    pdf.drawString(x + 2 * mm, ly, line)

        elif etype == "grid":
            if bg:
                pdf.setFillColor(bg)
                pdf.rect(x, y_pdf, w, h, fill=1, stroke=0)
            pdf.setStrokeColor(border_color)
            pdf.setLineWidth(border_w * 0.5)
            cols = int(float(el.get("cols", 7) or 7))
            rows = int(float(el.get("rows", 6) or 6))
            if cols > 0:
                cw = w / cols
                for ci in range(1, cols):
                    pdf.line(x + ci * cw, y_pdf, x + ci * cw, y_pdf + h)
            if rows > 0:
                rh = h / rows
                for ri in range(1, rows):
                    pdf.line(x, y_pdf + ri * rh, x + w, y_pdf + ri * rh)

        elif etype == "decorative":
            if bg:
                pdf.setFillColor(bg)
                pdf.circle(x + w / 2, y_pdf + h / 2, min(w, h) / 2, fill=1, stroke=0)
            pdf.setFillColor(color)
            pdf.circle(x + w / 2, y_pdf + h / 2, min(w, h) / 4, fill=1, stroke=0)

        if opacity < 1.0 and etype not in ("rect", "box", "text"):
            pdf.restoreState()


def _infer_pages(page_type, inferred):
    result = list(inferred or [])
    if not result:
        base = {
            "1dpp": ["dados_pessoais", "planejamento", "semanal"],
            "2dpp": ["dados_pessoais", "planejamento", "semanal"],
            "semanal": ["dados_pessoais", "mensal"],
            "mensal": ["dados_pessoais", "calendario"],
            "calendario": ["dados_pessoais", "planejamento"],
            "planejamento": ["dados_pessoais"],
        }
        result = base.get(page_type, ["dados_pessoais"])
    return result


def _generate_inferred_elements(inf_type, orig_elements, orig_colors, w, h):
    elements = []
    accent = "#4A90D9"
    text_color = "#333333"
    bg = "#FFFFFF"
    line_color = "#E0E0E0"

    for c in orig_colors:
        if c.get("role") == "accent":
            accent = c.get("hex", accent)
        elif c.get("role") == "text":
            text_color = c.get("hex", text_color)
        elif c.get("role") in ("background", "secondary"):
            bg = c.get("hex", bg)
        elif c.get("role") == "primary":
            text_color = c.get("hex", text_color)

    if inf_type == "dados_pessoais":
        elements.append({"type": "text", "x": 15, "y": 13, "w": 118, "h": 10,
                         "text": "DADOS PESSOAIS", "font_name": "Helvetica-Bold",
                         "font_size": 8, "color": accent, "bold": True, "align": "center"})
        fields = ["Nome:", "E-mail:", "Telefone:", "Endereco:", "Nascimento:", "Anotacoes:"]
        for i, f in enumerate(fields):
            fy = 30 + i * 18
            elements.append({"type": "text", "x": 15, "y": fy, "w": 118, "h": 12,
                             "text": f, "font_name": "Helvetica", "font_size": 7,
                             "color": text_color})
            elements.append({"type": "line", "x": 30, "y": fy + 10, "w": 103, "h": 0,
                             "color": line_color, "border_width": 0.3})

    elif inf_type == "planejamento":
        elements.append({"type": "text", "x": 15, "y": 13, "w": 118, "h": 10,
                         "text": "PLANEJAMENTO SEMANAL", "font_name": "Helvetica-Bold",
                         "font_size": 8, "color": accent, "bold": True, "align": "center"})
        days = ["SEG", "TER", "QUA", "QUI", "SEX", "SAB", "DOM"]
        col_w = 118 / 7
        for i, d in enumerate(days):
            dx = 15 + i * col_w
            elements.append({"type": "text", "x": dx, "y": 28, "w": col_w, "h": 8,
                             "text": d, "font_name": "Helvetica-Bold", "font_size": 6,
                             "color": accent, "bold": True, "align": "center"})
            elements.append({"type": "line", "x": dx + col_w / 2, "y": 38, "w": 0, "h": 170,
                             "color": line_color, "border_width": 0.3})

    elif inf_type == "semanal":
        elements.append({"type": "text", "x": 15, "y": 13, "w": 118, "h": 10,
                         "text": "AGENDA SEMANAL", "font_name": "Helvetica-Bold",
                         "font_size": 8, "color": accent, "bold": True, "align": "center"})
        elements.append({"type": "rect", "x": 15, "y": 30, "w": 118, "h": 170,
                         "border": True, "border_color": line_color, "border_width": 0.5})
        for i in range(7):
            ry = 30 + i * (170 / 7)
            elements.append({"type": "line", "x": 15, "y": ry, "w": 118, "h": 0,
                             "color": line_color, "border_width": 0.3})

    elif inf_type == "mensal":
        elements.append({"type": "text", "x": 15, "y": 13, "w": 118, "h": 10,
                         "text": "AGENDA MENSAL", "font_name": "Helvetica-Bold",
                         "font_size": 8, "color": accent, "bold": True, "align": "center"})
        elements.append({"type": "grid", "x": 15, "y": 30, "w": 118, "h": 170,
                         "cols": 7, "rows": 6, "border": True, "border_color": line_color})

    elif inf_type == "calendario":
        elements.append({"type": "text", "x": 15, "y": 13, "w": 118, "h": 10,
                         "text": "CALENDARIO", "font_name": "Helvetica-Bold",
                         "font_size": 8, "color": accent, "bold": True, "align": "center"})
        elements.append({"type": "grid", "x": 15, "y": 30, "w": 118, "h": 170,
                         "cols": 7, "rows": 6, "border": True, "border_color": line_color})

    else:
        elements.append({"type": "text", "x": 15, "y": 13, "w": 118, "h": 10,
                         "text": inf_type.upper().replace("_", " "),
                         "font_name": "Helvetica-Bold", "font_size": 8,
                         "color": accent, "bold": True, "align": "center"})
        elements.append({"type": "rect", "x": 15, "y": 30, "w": 118, "h": 170,
                         "border": True, "border_color": line_color})

    return elements

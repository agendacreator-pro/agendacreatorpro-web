from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
from reportlab.lib.colors import HexColor


def _parse_color(hex_str, fallback="#000000"):
    if not hex_str:
        return HexColor(fallback)
    try:
        return HexColor(hex_str)
    except Exception:
        return HexColor(fallback)


def _font_name(name, bold=False):
    safe = (name or "Helvetica").replace(" ", "-").replace("_", "-")
    valid = {
        "Helvetica", "Helvetica-Bold", "Helvetica-Oblique", "Helvetica-BoldOblique",
        "Times-Roman", "Times-Bold", "Times-Italic", "Times-BoldItalic",
        "Courier", "Courier-Bold", "Courier-Oblique", "Courier-BoldOblique",
    }
    if safe in valid:
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
    page_type = pa.get("page_type", "1dpp")
    inferred = pa.get("inferred_pages", [])

    w, h = PAGE_SIZES.get(formato.upper(), PAGE_SIZES["A5"])

    accent = "#4A90D9"
    text_color = "#333333"
    bg_color = "#FFFFFF"
    border_color = "#E0E0E0"

    for c in colors:
        if c.get("role") == "accent":
            accent = c.get("hex", accent)
        elif c.get("role") in ("primary",):
            text_color = c.get("hex", text_color)
        elif c.get("role") in ("background", "secondary"):
            bg_color = c.get("hex", bg_color)
        elif c.get("role") == "border":
            border_color = c.get("hex", border_color)

    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=(w, h))
    pdf.setPageCompression(0)

    pdf.setFillColor(_parse_color(bg_color))
    pdf.rect(0, 0, w, h, fill=1, stroke=0)
    _draw_elements(pdf, elements, w, h)

    for section_type in inferred:
        pdf.showPage()
        pdf.setFillColor(_parse_color(bg_color))
        pdf.rect(0, 0, w, h, fill=1, stroke=0)
        section_els = _build_section(section_type, elements, accent, text_color, border_color, w, h)
        _draw_elements(pdf, section_els, w, h)

    pdf.save()
    buffer.seek(0)
    return buffer


def _extract_sections_from_elements(elements):
    sections = []
    for el in elements:
        etype = el.get("type", "")
        text = (el.get("text") or "").lower()
        y = float(el.get("y", 0) or 0)
        h = float(el.get("h", 0) or 0)

        if etype == "text" and text:
            sections.append({
                "label": el.get("text", ""),
                "y": y, "h": h,
                "x": float(el.get("x", 0) or 0),
                "w": float(el.get("w", 0) or 0),
                "font_name": el.get("font_name", "Helvetica-Bold"),
                "font_size": float(el.get("font_size", 8) or 8),
                "color": el.get("color", "#000000"),
                "bold": bool(el.get("bold")),
                "align": el.get("align", "left"),
            })
    return sections


def _build_section(section_type, orig_elements, accent, text_color, border_color, w, h):
    sections = _extract_sections_from_elements(orig_elements)
    header_style = {}
    for s in sections:
        if s["bold"] and s["font_size"] >= 6:
            header_style = s
            break

    hdr_font = header_style.get("font_name", "Helvetica-Bold")
    hdr_size = header_style.get("font_size", 8)
    margin_l = 15
    margin_r = 15
    content_w = (w / mm) - margin_l - margin_r

    labels = {
        "dados_pessoais": "DADOS PESSOAIS",
        "planejamento": "PLANEJAMENTO SEMANAL",
        "semanal": "AGENDA SEMANAL",
        "mensal": "AGENDA MENSAL",
        "calendario": "CALENDARIO",
        "metas": "METAS E OBJETIVOS",
        "checklist": "CHECKLIST",
        "notas": "ANOTACOES",
    }
    title = labels.get(section_type, section_type.upper().replace("_", " "))

    els = []

    els.append({
        "type": "text", "x": margin_l, "y": 10, "w": content_w, "h": 10,
        "text": title, "font_name": hdr_font, "font_size": hdr_size,
        "color": accent, "bold": True, "align": "center",
    })

    els.append({
        "type": "line", "x": margin_l, "y": 22, "w": content_w, "h": 0,
        "color": border_color, "border_width": 0.5,
    })

    top_y = 28
    bottom_y = (h / mm) - 12
    area_h = bottom_y - top_y

    if section_type == "dados_pessoais":
        fields = ["Nome:", "E-mail:", "Telefone:", "Endereco:", "Nascimento:", "Observacoes:"]
        spacing = area_h / (len(fields) + 1)
        for i, f in enumerate(fields):
            fy = top_y + i * spacing
            els.append({"type": "text", "x": margin_l, "y": fy, "w": 40, "h": 8,
                        "text": f, "font_name": "Helvetica", "font_size": 7,
                        "color": text_color})
            els.append({"type": "line", "x": margin_l + 40, "y": fy + 7, "w": content_w - 40, "h": 0,
                        "color": border_color, "border_width": 0.3})

    elif section_type in ("planejamento", "semanal"):
        days = ["SEG", "TER", "QUA", "QUI", "SEX", "SAB", "DOM"]
        col_w = content_w / 7
        for i, d in enumerate(days):
            dx = margin_l + i * col_w
            els.append({"type": "text", "x": dx, "y": top_y, "w": col_w, "h": 8,
                        "text": d, "font_name": "Helvetica-Bold", "font_size": 6,
                        "color": accent, "bold": True, "align": "center"})
            els.append({"type": "line", "x": dx, "y": top_y + 10, "w": 0, "h": area_h - 10,
                        "color": border_color, "border_width": 0.3})
        els.append({"type": "line", "x": margin_l, "y": top_y + 10, "w": content_w, "h": 0,
                     "color": border_color, "border_width": 0.3})

    elif section_type in ("mensal", "calendario"):
        cols = 7
        rows = 6
        col_w = content_w / cols
        row_h = (area_h - 10) / rows
        for ci in range(cols):
            els.append({"type": "line", "x": margin_l + ci * col_w, "y": top_y + 10, "w": 0, "h": area_h - 10,
                        "color": border_color, "border_width": 0.3})
        for ri in range(rows + 1):
            els.append({"type": "line", "x": margin_l, "y": top_y + 10 + ri * row_h, "w": content_w, "h": 0,
                        "color": border_color, "border_width": 0.3})

    elif section_type == "metas":
        for i in range(8):
            fy = top_y + i * (area_h / 8)
            els.append({"type": "rect", "x": margin_l, "y": fy, "w": 5, "h": 5,
                        "border": True, "border_color": border_color, "border_width": 0.5})
            els.append({"type": "line", "x": margin_l + 10, "y": fy + 4, "w": content_w - 10, "h": 0,
                        "color": border_color, "border_width": 0.3})

    elif section_type == "checklist":
        for i in range(12):
            fy = top_y + i * (area_h / 12)
            els.append({"type": "rect", "x": margin_l, "y": fy, "w": 4, "h": 4,
                        "border": True, "border_color": border_color, "border_width": 0.5})
            els.append({"type": "line", "x": margin_l + 8, "y": fy + 3, "w": content_w - 8, "h": 0,
                        "color": border_color, "border_width": 0.3})

    else:
        els.append({"type": "rect", "x": margin_l, "y": top_y, "w": content_w, "h": area_h,
                    "border": True, "border_color": border_color, "border_width": 0.5})
        for i in range(int(area_h / 10)):
            fy = top_y + 8 + i * 10
            els.append({"type": "line", "x": margin_l + 5, "y": fy, "w": content_w - 10, "h": 0,
                        "color": border_color, "border_width": 0.2})

    return els


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
        font_name = _font_name(el.get("font_name"), bold)
        font_size = float(el.get("font_size", 10) or 10)
        align = el.get("align", "left")

        pdf.setFillColor(color)

        if etype in ("rect", "box"):
            if bg:
                pdf.setFillColor(bg)
                pdf.rect(x, y_pdf, w, h, fill=1, stroke=0)
            if el.get("border"):
                pdf.setStrokeColor(border_color)
                pdf.setLineWidth(border_w)
                pdf.rect(x, y_pdf, w, h, fill=0, stroke=1)

        elif etype == "line":
            pdf.setStrokeColor(color)
            pdf.setLineWidth(border_w)
            pdf.line(x, y_pdf, x + w, y_pdf + h)

        elif etype == "circle":
            if bg:
                pdf.setFillColor(bg)
                pdf.circle(x + w / 2, y_pdf + h / 2, min(w, h) / 2, fill=1, stroke=0)
            pdf.setFillColor(color)
            pdf.circle(x + w / 2, y_pdf + h / 2, min(w, h) / 4, fill=1, stroke=0)

        elif etype == "text":
            text = el.get("text", "")
            if bg:
                pdf.setFillColor(bg)
                pdf.rect(x, y_pdf, w, h, fill=1, stroke=0)
            pdf.setFillColor(color)
            pdf.setFont(font_name, font_size)
            line_h = max(font_size + 2, 10) * mm
            lines = text.split("\n")
            for i, line_text in enumerate(lines):
                ly = y_pdf + h - (i + 1) * line_h
                if ly < y_pdf:
                    break
                if align == "center":
                    pdf.drawCentredString(x + w / 2, ly, line_text)
                elif align == "right":
                    pdf.drawRightString(x + w, ly, line_text)
                else:
                    pdf.drawString(x + 2 * mm, ly, line_text)

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
            pdf.setFillColor(color)
            pdf.circle(x + w / 2, y_pdf + h / 2, min(w, h) / 3, fill=1, stroke=0)

from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
from reportlab.lib.colors import HexColor, Color
import copy
import math


def _pc(hex_str, fallback="#000000"):
    if not hex_str:
        return HexColor(fallback)
    try:
        return HexColor(hex_str)
    except Exception:
        return HexColor(fallback)


def _fn(name, bold=False, italic=False):
    safe = (name or "Helvetica").replace(" ", "-").replace("_", "-")
    valid = {
        "Helvetica", "Helvetica-Bold", "Helvetica-Oblique", "Helvetica-BoldOblique",
        "Times-Roman", "Times-Bold", "Times-Italic", "Times-BoldItalic",
        "Courier", "Courier-Bold", "Courier-Oblique", "Courier-BoldOblique",
        "ZapfDingbats",
    }
    if safe in valid:
        return safe
    if bold and italic:
        return "Helvetica-BoldOblique"
    if bold:
        return "Helvetica-Bold"
    if italic:
        return "Helvetica-Oblique"
    return "Helvetica"


PAGE_SIZES = {
    "A5": (148 * mm, 210 * mm),
    "A4": (210 * mm, 297 * mm),
    "QUADRADO": (150 * mm, 150 * mm),
}

SECTION_TEXT_MAP = {
    "dados_pessoais": {"title": "DADOS PESSOAIS"},
    "planejamento": {"title": "PLANEJAMENTO SEMANAL"},
    "semanal": {"title": "AGENDA SEMANAL"},
    "mensal": {"title": "AGENDA MENSAL"},
    "calendario": {"title": "CALENDARIO 2026"},
    "metas": {"title": "METAS E OBJETIVOS"},
    "checklist": {"title": "CHECKLIST"},
    "notas": {"title": "ANOTACOES"},
    "divisoria": {"title": "DIVISORIA"},
}


def gerar_pdf_da_analise(analysis_dict, formato="A5"):
    pa = analysis_dict.get("page_analysis", analysis_dict)
    orig_elements = pa.get("elements", [])
    colors = pa.get("colors", [])
    inferred = pa.get("inferred_pages", [])

    w, h = PAGE_SIZES.get(formato.upper(), PAGE_SIZES["A5"])

    bg = "#FFFFFF"
    accent = "#4A90D9"
    for c in colors:
        if c.get("role") in ("background", "secondary") and c.get("hex"):
            bg = c["hex"]
        if c.get("role") == "accent" and c.get("hex"):
            accent = c["hex"]

    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=(w, h))
    pdf.setPageCompression(0)

    pdf.setFillColor(_pc(bg))
    pdf.rect(0, 0, w, h, fill=1, stroke=0)
    _draw(pdf, orig_elements, w, h)

    for sec in inferred:
        pdf.showPage()
        pdf.setFillColor(_pc(bg))
        pdf.rect(0, 0, w, h, fill=1, stroke=0)
        new_els = _replicate_pattern(orig_elements, sec, accent, colors, w, h)
        _draw(pdf, new_els, w, h)

    pdf.save()
    buffer.seek(0)
    return buffer


def _replicate_pattern(orig_elements, section_type, accent, colors, page_w, page_h):
    section_info = SECTION_TEXT_MAP.get(section_type, {"title": section_type.upper().replace("_", " ")})
    title = section_info.get("title", section_type.upper().replace("_", " "))

    new_elements = []

    for el in orig_elements:
        new_el = copy.deepcopy(el)
        etype = new_el.get("type", "")
        text = (new_el.get("text") or "").strip()
        bold = bool(new_el.get("bold"))
        fs = float(new_el.get("font_size", 0) or 0)
        y = float(new_el.get("y", 0) or 0)

        if etype == "text" and text:
            is_header = bold and fs >= 6 and y < 60
            if is_header:
                new_el["text"] = title
                new_el["color"] = accent

        new_elements.append(new_el)

    return new_elements


def _draw(pdf, elements, page_w, page_h):
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

        color = _pc(el.get("color", "#000000"))
        bg = _pc(el.get("bg_color")) if el.get("bg_color") else None
        bc = _pc(el.get("border_color", "#E0E0E0"))
        bw = float(el.get("border_width", 0.5) or 0.5)
        bold = bool(el.get("bold"))
        italic = bool(el.get("italic"))
        fn = _fn(el.get("font_name"), bold, italic)
        fs = float(el.get("font_size", 10) or 10)
        align = el.get("align", "left")
        radius = float(el.get("radius", 0) or 0)
        opacity = float(el.get("opacity", 1.0) or 1.0)

        if opacity < 1.0:
            pdf.setFillColor(Color(color.red, color.green, color.blue, opacity))
        else:
            pdf.setFillColor(color)

        if etype in ("rect", "box"):
            if bg:
                if opacity < 1.0:
                    pdf.setFillColor(Color(bg.red, bg.green, bg.blue, opacity))
                else:
                    pdf.setFillColor(bg)
                if radius > 0:
                    pdf.roundRect(x, y_pdf, w, h, radius * mm, fill=1, stroke=0)
                else:
                    pdf.rect(x, y_pdf, w, h, fill=1, stroke=0)
            if el.get("border"):
                pdf.setStrokeColor(bc)
                pdf.setLineWidth(bw)
                if radius > 0:
                    pdf.roundRect(x, y_pdf, w, h, radius * mm, fill=0, stroke=1)
                else:
                    pdf.rect(x, y_pdf, w, h, fill=0, stroke=1)

        elif etype == "line":
            pdf.setStrokeColor(color)
            pdf.setLineWidth(bw)
            pdf.line(x, y_pdf, x + w, y_pdf + h)

        elif etype == "circle":
            r_outer = min(w, h) / 2
            r_inner = r_outer * 0.5
            if bg:
                pdf.setFillColor(bg)
                pdf.circle(x + w / 2, y_pdf + h / 2, r_outer, fill=1, stroke=0)
            pdf.setFillColor(color)
            pdf.circle(x + w / 2, y_pdf + h / 2, r_inner, fill=1, stroke=0)

        elif etype == "text":
            text = el.get("text", "")
            if not text:
                if bg:
                    pdf.setFillColor(bg)
                    pdf.rect(x, y_pdf, w, h, fill=1, stroke=0)
                continue
            if bg:
                pdf.setFillColor(bg)
                if radius > 0:
                    pdf.roundRect(x, y_pdf, w, h, radius * mm, fill=1, stroke=0)
                else:
                    pdf.rect(x, y_pdf, w, h, fill=1, stroke=0)
            pdf.setFillColor(color)
            pdf.setFont(fn, fs)
            lh = max(fs * 1.3, 8) * 0.35
            lines = text.split("\n")
            total_h = len(lines) * lh
            start_y = y_pdf + h - lh
            if total_h < h:
                start_y = y_pdf + h - (h - total_h) / 2 - lh
            for i, lt in enumerate(lines):
                ly = start_y - i * lh
                if ly < y_pdf - lh:
                    break
                if align == "center":
                    pdf.drawCentredString(x + w / 2, ly, lt)
                elif align == "right":
                    pdf.drawRightString(x + w, ly, lt)
                else:
                    pdf.drawString(x + 2 * mm, ly, lt)

        elif etype == "grid":
            if bg:
                pdf.setFillColor(bg)
                pdf.rect(x, y_pdf, w, h, fill=1, stroke=0)
            pdf.setStrokeColor(bc)
            pdf.setLineWidth(bw * 0.5)
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
            shape = el.get("shape", "circle_shape")
            if bg:
                pdf.setFillColor(bg)
                pdf.circle(x + w / 2, y_pdf + h / 2, min(w, h) / 2, fill=1, stroke=0)
            cx = x + w / 2
            cy = y_pdf + h / 2
            r = min(w, h) / 2.5
            if shape == "star":
                _draw_star(pdf, cx, cy, r, 5, color)
            elif shape == "heart":
                _draw_heart(pdf, cx, cy, r, color)
            elif shape == "flower":
                _draw_flower(pdf, cx, cy, r, color)
            elif shape == "bee":
                _draw_bee(pdf, cx, cy, r, color)
            elif shape == "butterfly":
                _draw_butterfly(pdf, cx, cy, r, color)
            elif shape == "leaf":
                _draw_leaf(pdf, cx, cy, r, color)
            elif shape == "diamond":
                _draw_diamond(pdf, cx, cy, r, color)
            else:
                pdf.setFillColor(color)
                pdf.circle(cx, cy, r, fill=1, stroke=0)

        elif etype == "strip":
            if bg:
                pdf.setFillColor(bg)
                pdf.rect(x, y_pdf, w, h, fill=1, stroke=0)


def _draw_star(pdf, cx, cy, r, points, color):
    pdf.setFillColor(color)
    path = pdf.beginPath()
    for i in range(points * 2):
        angle = math.pi / 2 + i * math.pi / points
        rad = r if i % 2 == 0 else r * 0.4
        px = cx + rad * math.cos(angle)
        py = cy + rad * math.sin(angle)
        if i == 0:
            path.moveTo(px, py)
        else:
            path.lineTo(px, py)
    path.close()
    pdf.drawPath(path, fill=1, stroke=0)


def _draw_heart(pdf, cx, cy, r, color):
    pdf.setFillColor(color)
    pdf.circle(cx - r * 0.3, cy + r * 0.15, r * 0.35, fill=1, stroke=0)
    pdf.circle(cx + r * 0.3, cy + r * 0.15, r * 0.35, fill=1, stroke=0)
    path = pdf.beginPath()
    path.moveTo(cx - r * 0.6, cy + r * 0.2)
    path.lineTo(cx, cy - r * 0.6)
    path.lineTo(cx + r * 0.6, cy + r * 0.2)
    path.close()
    pdf.drawPath(path, fill=1, stroke=0)


def _draw_flower(pdf, cx, cy, r, color):
    pdf.setFillColor(color)
    for i in range(5):
        angle = i * 2 * math.pi / 5
        px = cx + r * 0.5 * math.cos(angle)
        py = cy + r * 0.5 * math.sin(angle)
        pdf.circle(px, py, r * 0.3, fill=1, stroke=0)
    pdf.setFillColor(_pc("#FFD700"))
    pdf.circle(cx, cy, r * 0.2, fill=1, stroke=0)


def _draw_bee(pdf, cx, cy, r, color):
    pdf.setFillColor(_pc("#FFD700"))
    pdf.ellipse(cx - r * 0.4, cy - r * 0.3, r * 0.8, r * 0.6, fill=1, stroke=0)
    pdf.setFillColor(_pc("#2D2D2D"))
    pdf.ellipse(cx - r * 0.35, cy - r * 0.2, r * 0.25, r * 0.4, fill=1, stroke=0)
    pdf.ellipse(cx + r * 0.1, cy - r * 0.2, r * 0.25, r * 0.4, fill=1, stroke=0)
    pdf.setFillColor(_pc("#FFFFFF"))
    pdf.ellipse(cx - r * 0.2, cy + r * 0.3, r * 0.35, r * 0.25, fill=1, stroke=0)
    pdf.ellipse(cx + r * 0.05, cy + r * 0.35, r * 0.3, r * 0.2, fill=1, stroke=0)


def _draw_butterfly(pdf, cx, cy, r, color):
    pdf.setFillColor(color)
    pdf.circle(cx - r * 0.45, cy + r * 0.2, r * 0.4, fill=1, stroke=0)
    pdf.circle(cx + r * 0.45, cy + r * 0.2, r * 0.4, fill=1, stroke=0)
    pdf.circle(cx - r * 0.35, cy - r * 0.3, r * 0.3, fill=1, stroke=0)
    pdf.circle(cx + r * 0.35, cy - r * 0.3, r * 0.3, fill=1, stroke=0)
    pdf.setFillColor(_pc("#2D2D2D"))
    pdf.rect(cx - r * 0.05, cy - r * 0.6, r * 0.1, r * 1.2, fill=1, stroke=0)


def _draw_leaf(pdf, cx, cy, r, color):
    pdf.setFillColor(color)
    path = pdf.beginPath()
    path.moveTo(cx, cy + r)
    path.curveTo(cx + r * 0.8, cy + r * 0.5, cx + r * 0.8, cy - r * 0.5, cx, cy - r)
    path.curveTo(cx - r * 0.8, cy - r * 0.5, cx - r * 0.8, cy + r * 0.5, cx, cy + r)
    path.close()
    pdf.drawPath(path, fill=1, stroke=0)
    pdf.setStrokeColor(_pc("#2D2D2D"))
    pdf.setLineWidth(0.3)
    pdf.line(cx, cy + r, cx, cy - r)


def _draw_diamond(pdf, cx, cy, r, color):
    pdf.setFillColor(color)
    path = pdf.beginPath()
    path.moveTo(cx, cy + r)
    path.lineTo(cx + r * 0.6, cy)
    path.lineTo(cx, cy - r)
    path.lineTo(cx - r * 0.6, cy)
    path.close()
    pdf.drawPath(path, fill=1, stroke=0)

"""
Blueprint-based PDF generator.
Takes a Blueprint and generates pages by applying colors to objects
and substituting variable data (dates, days, numbers).
"""
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


COLOR_REFS = {
    "_accent_": "accent",
    "_primary_": "primary",
    "_text_": "text",
    "_white_": "#FFFFFF",
    "_border_": "border",
    "_highlight_": "highlight",
    "_secondary_": "secondary",
    "_background_": "background",
}


def _resolve_color(color_ref, palette):
    if not color_ref:
        return None
    if color_ref.startswith("#"):
        return color_ref
    role = COLOR_REFS.get(color_ref, "")
    if role == "#FFFFFF":
        return "#FFFFFF"
    return palette.get(role, color_ref)


def _build_color_map(palette):
    return palette


def _draw_object(pdf, obj, page_h, palette, substitutions=None):
    otype = obj.get("obj_type", obj.get("type", "rect"))
    x_mm = float(obj.get("x", 0) or 0)
    y_mm = float(obj.get("y", 0) or 0)
    w_mm = float(obj.get("w", 0) or 0)
    h_mm = float(obj.get("h", 0) or 0)

    x = x_mm * mm
    y_pdf = page_h - (y_mm * mm) - (h_mm * mm)
    w = w_mm * mm
    h = h_mm * mm

    color_ref = obj.get("color", "")
    bg_ref = obj.get("bg_color", "")
    bc_ref = obj.get("border_color", "")

    color = _pc(_resolve_color(color_ref, palette) or "#000000")
    bg = _pc(_resolve_color(bg_ref, palette)) if bg_ref else None
    bc = _pc(_resolve_color(bc_ref, palette) or "#E0E0E0") if bc_ref else _pc("#E0E0E0")

    bw = float(obj.get("border_width", 0.5) or 0.5)
    bold = bool(obj.get("bold"))
    italic = bool(obj.get("italic"))
    fn = _fn(obj.get("font_name", "Helvetica"), bold, italic)
    fs = float(obj.get("font_size", 6) or 6)
    align = obj.get("align", "left")
    radius = float(obj.get("radius", 0) or 0)
    value = obj.get("value", obj.get("text", ""))

    if substitutions and value in substitutions:
        value = substitutions[value]

    if otype == "RECTANGLE":
        if bg:
            pdf.setFillColor(bg)
            if radius > 0:
                pdf.roundRect(x, y_pdf, w, h, radius * mm, fill=1, stroke=0)
            else:
                pdf.rect(x, y_pdf, w, h, fill=1, stroke=0)
        if obj.get("border"):
            pdf.setStrokeColor(bc)
            pdf.setLineWidth(bw)
            if radius > 0:
                pdf.roundRect(x, y_pdf, w, h, radius * mm, fill=0, stroke=1)
            else:
                pdf.rect(x, y_pdf, w, h, fill=0, stroke=1)

    elif otype == "ROUNDED_RECTANGLE":
        if bg:
            pdf.setFillColor(bg)
            pdf.roundRect(x, y_pdf, w, h, max(radius, 2) * mm, fill=1, stroke=0)
        if obj.get("border"):
            pdf.setStrokeColor(bc)
            pdf.setLineWidth(bw)
            pdf.roundRect(x, y_pdf, w, h, max(radius, 2) * mm, fill=0, stroke=1)

    elif otype == "LINE":
        pdf.setStrokeColor(color)
        pdf.setLineWidth(bw)
        pdf.line(x, y_pdf, x + w, y_pdf + h)

    elif otype in ("CIRCLE", "CHECKBOX"):
        r_outer = min(w, h) / 2
        if bg:
            pdf.setFillColor(bg)
            pdf.circle(x + w / 2, y_pdf + h / 2, r_outer, fill=1, stroke=0)
        pdf.setFillColor(color)
        pdf.circle(x + w / 2, y_pdf + h / 2, r_outer * 0.5, fill=1, stroke=0)

    elif otype in ("TEXT", "SECTION_TITLE", "DAY_NAME", "DAY_NUMBER",
                    "MONTH_NAME", "TIME_SLOT", "TASK_TEXT", "NOTES_LABEL",
                    "PAGE_NUMBER"):
        text = value
        if not text:
            return
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

    elif otype == "DECORATION":
        shape = obj.get("shape", "circle")
        cx = x + w / 2
        cy = y_pdf + h / 2
        r = min(w, h) / 2.5
        pdf.setFillColor(color)
        if shape == "heart":
            pdf.circle(cx - r * 0.3, cy + r * 0.15, r * 0.35, fill=1, stroke=0)
            pdf.circle(cx + r * 0.3, cy + r * 0.15, r * 0.35, fill=1, stroke=0)
            path = pdf.beginPath()
            path.moveTo(cx - r * 0.6, cy + r * 0.2)
            path.lineTo(cx, cy - r * 0.6)
            path.lineTo(cx + r * 0.6, cy + r * 0.2)
            path.close()
            pdf.drawPath(path, fill=1, stroke=0)
        elif shape == "flower":
            for i in range(5):
                angle = i * 2 * math.pi / 5
                px = cx + r * 0.5 * math.cos(angle)
                py = cy + r * 0.5 * math.sin(angle)
                pdf.circle(px, py, r * 0.3, fill=1, stroke=0)
            pdf.setFillColor(_pc("#FFD700"))
            pdf.circle(cx, cy, r * 0.2, fill=1, stroke=0)
        elif shape == "star":
            path = pdf.beginPath()
            for i in range(10):
                angle = math.pi / 2 + i * math.pi / 5
                rad = r if i % 2 == 0 else r * 0.4
                px = cx + rad * math.cos(angle)
                py = cy + rad * math.sin(angle)
                if i == 0:
                    path.moveTo(px, py)
                else:
                    path.lineTo(px, py)
            path.close()
            pdf.drawPath(path, fill=1, stroke=0)
        elif shape == "bee":
            pdf.setFillColor(_pc("#FFD700"))
            pdf.ellipse(cx - r * 0.4, cy - r * 0.3, r * 0.8, r * 0.6, fill=1, stroke=0)
            pdf.setFillColor(_pc("#2D2D2D"))
            pdf.ellipse(cx - r * 0.35, cy - r * 0.2, r * 0.25, r * 0.4, fill=1, stroke=0)
            pdf.ellipse(cx + r * 0.1, cy - r * 0.2, r * 0.25, r * 0.4, fill=1, stroke=0)
        else:
            pdf.circle(cx, cy, r, fill=1, stroke=0)

    elif otype == "TABLE":
        if bg:
            pdf.setFillColor(bg)
            pdf.rect(x, y_pdf, w, h, fill=1, stroke=0)
        cols = int(float(obj.get("cols", 7) or 7))
        rows = int(float(obj.get("rows", 6) or 6))
        pdf.setStrokeColor(bc)
        pdf.setLineWidth(bw * 0.5)
        if cols > 0:
            cw = w / cols
            for ci in range(1, cols):
                pdf.line(x + ci * cw, y_pdf, x + ci * cw, y_pdf + h)
        if rows > 0:
            rh = h / rows
            for ri in range(1, rows):
                pdf.line(x, y_pdf + ri * rh, x + w, y_pdf + ri * rh)

    elif otype == "GRID":
        if bg:
            pdf.setFillColor(bg)
            pdf.rect(x, y_pdf, w, h, fill=1, stroke=0)
        cols = int(float(obj.get("cols", 7) or 7))
        rows = int(float(obj.get("rows", 6) or 6))
        pdf.setStrokeColor(bc)
        pdf.setLineWidth(bw * 0.5)
        if cols > 0:
            cw = w / cols
            for ci in range(1, cols):
                pdf.line(x + ci * cw, y_pdf, x + ci * cw, y_pdf + h)
        if rows > 0:
            rh = h / rows
            for ri in range(1, rows):
                pdf.line(x, y_pdf + ri * rh, x + w, y_pdf + ri * rh)


def _get_substitutions_for_page(page_index, page_type, base_date=None):
    import datetime
    if base_date is None:
        base_date = datetime.date(2026, 1, 1)

    day_offset = page_index
    current_date = base_date + datetime.timedelta(days=day_offset)

    days_pt = ["SEGUNDA", "TERCA", "QUARTA", "QUINTA", "SEXTA", "SABADO", "DOMINGO"]
    months_pt = ["janeiro", "fevereiro", "marco", "abril", "maio", "junho",
                 "julho", "agosto", "setembro", "outubro", "novembro", "dezembro"]

    day_name = days_pt[current_date.weekday()]
    month_name = months_pt[current_date.month - 1]
    day_num = str(current_date.day)
    month_year = f"{month_name} {current_date.year}"

    return {
        "TERCA": day_name,
        "15": day_num,
        "julho 2026": month_year,
        "1 / 365": f"{page_index + 1} / 365",
    }


def gerar_pdf_blueprint(blueprint_dict, formato="A5", num_pages=1, base_date=None):
    bp = blueprint_dict
    palette = bp.get("palette", {})
    if not palette and bp.get("colors"):
        if isinstance(bp["colors"], list):
            palette = {}
            for c in bp["colors"]:
                palette[c.get("role", "accent")] = c.get("hex", "#000000")
        else:
            palette = bp["colors"]

    editable = bp.get("editable_objects", [])
    if not editable:
        editable = bp.get("elements", [])

    w, h = PAGE_SIZES.get(formato.upper(), PAGE_SIZES["A5"])

    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=(w, h))
    pdf.setPageCompression(0)

    for page_idx in range(num_pages):
        if page_idx > 0:
            pdf.showPage()

        bg = _resolve_color("_background_", palette) or "#FFFFFF"
        pdf.setFillColor(_pc(bg))
        pdf.rect(0, 0, w, h, fill=1, stroke=0)

        subs = _get_substitutions_for_page(page_idx, bp.get("page_type", "1dpp"), base_date)

        for obj in editable:
            _draw_object(pdf, obj, h, palette, subs)

        sections = bp.get("sections", [])
        for sec in sections:
            sec_children = sec.get("children", [])
            for child in sec_children:
                already_drawn = any(
                    o.get("x") == child.get("x") and o.get("y") == child.get("y")
                    for o in editable
                )
                if not already_drawn:
                    _draw_object(pdf, child, h, palette, subs)

    pdf.save()
    buffer.seek(0)
    return buffer

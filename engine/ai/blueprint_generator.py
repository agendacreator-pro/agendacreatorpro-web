"""
Blueprint-based PDF generator.
Generates complete agenda: front matter (dados pessoais, calendário, planejamento)
then daily pages using the Blueprint pattern with date substitution.
"""
from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
from reportlab.lib.colors import HexColor, Color
import copy
import math
import datetime


def _pc(hex_str, fallback="#000000"):
    if not hex_str:
        return HexColor(fallback)
    try:
        return HexColor(hex_str)
    except Exception:
        return HexColor(fallback)


def _fn(name, bold=False, italic=False, family=None):
    if family:
        try:
            from fonts import resolve_font
        except Exception:
            resolve_font = None
        if resolve_font:
            rl = resolve_font(family, bold, italic)
            if rl:
                return rl
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


def _set_font(pdf, font_family, name, size):
    """Set the current font, overriding the family when one was chosen."""
    n = (name or "").lower()
    bold = "bold" in n
    italic = "italic" in n
    pdf.setFont(_fn(name, bold, italic, family=font_family), size)


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


def _get_palette(blueprint_dict):
    palette = blueprint_dict.get("palette", {})
    if not palette and blueprint_dict.get("colors"):
        if isinstance(blueprint_dict["colors"], list):
            for c in blueprint_dict["colors"]:
                palette[c.get("role", "accent")] = c.get("hex", "#000000")
        else:
            palette = blueprint_dict["colors"]
    return palette


ALLOWED_OBJECT_TYPES = {
    "RECTANGLE", "ROUNDED_RECTANGLE", "LINE", "CIRCLE", "CHECKBOX",
    "TEXT", "SECTION_TITLE", "DAY_NAME", "DAY_NUMBER", "MONTH_NAME",
    "TIME_SLOT", "TASK_TEXT", "NOTES_LABEL", "PAGE_NUMBER",
    "DECORATION", "TABLE", "GRID",
}

TEXT_OBJECT_TYPES = {
    "TEXT", "SECTION_TITLE", "DAY_NAME", "DAY_NUMBER", "MONTH_NAME",
    "TIME_SLOT", "TASK_TEXT", "NOTES_LABEL", "PAGE_NUMBER",
}


def sanitize_blueprint(objects, w_mm=148, h_mm=210):
    """Validate and clamp AI-generated objects to the page bounds.

    Drops malformed/out-of-page objects, coerces numeric fields,
    ensures unique ids and only known object types.
    """
    if not isinstance(objects, list):
        return []

    seen = set()
    out = []

    for obj in objects:
        if not isinstance(obj, dict):
            continue

        o = dict(obj)

        try:
            x = float(o.get("x", 0) or 0)
            y = float(o.get("y", 0) or 0)
            w = float(o.get("w", 0) or 0)
            h = float(o.get("h", 0) or 0)
        except (TypeError, ValueError):
            continue

        if w <= 0 and h <= 0:
            continue

        if x >= w_mm or y >= h_mm or x + w <= 0 or y + h <= 0:
            continue

        x = max(0.0, min(x, w_mm - 0.1))
        y = max(0.0, min(y, h_mm - 0.1))
        w = max(0.0, min(w, w_mm - x))
        h = max(0.0, min(h, h_mm - y))
        o["x"], o["y"], o["w"], o["h"] = round(x, 2), round(y, 2), round(w, 2), round(h, 2)

        otype = str(o.get("obj_type", o.get("type", "") or "RECTANGLE")).upper()
        if otype not in ALLOWED_OBJECT_TYPES:
            otype = "RECTANGLE"
        o["obj_type"] = otype

        for k in ("font_size", "border_width", "radius", "opacity", "line_height"):
            try:
                v = float(o.get(k) or 0)
                if v < 0:
                    v = 0
                o[k] = v
            except (TypeError, ValueError):
                o.pop(k, None)
        if not o.get("font_size"):
            o["font_size"] = 6
        if not o.get("border_width"):
            o["border_width"] = 0.5
        o["font_size"] = max(1.0, min(float(o.get("font_size") or 6), 60.0))
        o["border_width"] = max(0.05, min(float(o.get("border_width") or 0.5), 6.0))
        o["radius"] = max(0.0, min(float(o.get("radius") or 0), 20.0))
        o["opacity"] = max(0.0, min(float(o.get("opacity") or 1.0), 1.0))

        if otype in ("TABLE", "GRID"):
            try:
                o["cols"] = max(1, min(int(float(o.get("cols") or 7)), 50))
            except (TypeError, ValueError):
                o["cols"] = 7
            try:
                o["rows"] = max(1, min(int(float(o.get("rows") or 6)), 50))
            except (TypeError, ValueError):
                o["rows"] = 6

        if otype in TEXT_OBJECT_TYPES:
            text_val = str(o.get("value", o.get("text", "")) or "").strip()
            if not text_val:
                continue
            o["value"] = text_val

        oid = str(o.get("id") or "")
        if not oid:
            oid = f"obj_{len(out)}"
        base_id = oid
        i = 1
        while oid in seen:
            oid = f"{base_id}_{i}"
            i += 1
        seen.add(oid)
        o["id"] = oid

        out.append(o)

    return out


def _draw_object(pdf, obj, page_h, palette, substitutions=None, font_family=None):
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
    fn = _fn(obj.get("font_name", "Helvetica"), bold, italic, family=font_family)
    fs = float(obj.get("font_size", 6) or 6)
    align = obj.get("align", "left")
    radius = float(obj.get("radius", 0) or 0)
    value = obj.get("value", obj.get("text", ""))

    if substitutions:
        sem = obj.get("semantic", "")
        if sem:
            slot = 1 if (y_mm + h_mm / 2) > (page_h / mm) / 2 else 0
            slot_key = f"{sem}_{slot}"
            if substitutions.get(slot_key):
                value = substitutions[slot_key]
            elif substitutions.get(sem):
                value = substitutions[sem]
        elif value in substitutions:
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

    elif otype in ("TABLE", "GRID"):
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


# ── Front matter pages ──────────────────────────────────────────────────

MONTHS_PT = ["Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
             "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"]
MONTHS_SHORT = ["JAN", "FEV", "MAR", "ABR", "MAI", "JUN",
                "JUL", "AGO", "SET", "OUT", "NOV", "DEZ"]
DAYS_SHORT = ["SEG", "TER", "QUA", "QUI", "SEX", "SÁB", "DOM"]


def _draw_dados_pessoais(pdf, w, h, palette, font_family=None):
    accent = _pc(_resolve_color("_accent_", palette) or "#4A90D9")
    text_c = _pc(_resolve_color("_text_", palette) or "#333333")
    border_c = _pc(_resolve_color("_border_", palette) or "#E0E0E0")
    bg = _pc(_resolve_color("_background_", palette) or "#FFFFFF")

    pdf.setFillColor(bg)
    pdf.rect(0, 0, w, h, fill=1, stroke=0)

    top_bar = 25 * mm
    pdf.setFillColor(accent)
    pdf.rect(0, h - top_bar, w, top_bar, fill=1, stroke=0)
    pdf.setFillColor(_pc("#FFFFFF"))
    _set_font(pdf, font_family, "Helvetica-Bold", 14)
    pdf.drawCentredString(w / 2, h - 16 * mm, "DADOS PESSOAIS")

    y = h - top_bar - 20 * mm
    fields = [
        ("Nome", 30), ("E-mail", 25), ("Telefone", 20),
        ("Endereço", 30), ("Data de Nascimento", 20),
        ("Profissão", 25), ("Empresa", 25),
        ("Observações", 50),
    ]
    line_h = 8 * mm
    label_h = 5 * mm

    for label, field_h_mm in fields:
        pdf.setFillColor(text_c)
        _set_font(pdf, font_family, "Helvetica-Bold", 7)
        pdf.drawString(15 * mm, y, label)
        y -= label_h
        pdf.setStrokeColor(border_c)
        pdf.setLineWidth(0.4)
        pdf.line(15 * mm, y, w - 15 * mm, y)
        y -= (field_h_mm - label_h) * mm

    pdf.setFillColor(border_c)
    _set_font(pdf, font_family, "Helvetica", 5)
    pdf.drawCentredString(w / 2, 8 * mm, "Agenda Creator Pro")


def _draw_calendario_anual(pdf, w, h, palette, base_date, font_family=None):
    accent = _pc(_resolve_color("_accent_", palette) or "#4A90D9")
    text_c = _pc(_resolve_color("_text_", palette) or "#333333")
    border_c = _pc(_resolve_color("_border_", palette) or "#E0E0E0")
    bg = _pc(_resolve_color("_background_", palette) or "#FFFFFF")

    pdf.setFillColor(bg)
    pdf.rect(0, 0, w, h, fill=1, stroke=0)

    top_bar = 20 * mm
    pdf.setFillColor(accent)
    pdf.rect(0, h - top_bar, w, top_bar, fill=1, stroke=0)
    pdf.setFillColor(_pc("#FFFFFF"))
    _set_font(pdf, font_family, "Helvetica-Bold", 12)
    pdf.drawCentredString(w / 2, h - 14 * mm, f"CALENDARIO {base_date.year}")

    margin = 8 * mm
    gap = 3 * mm
    grid_w = w - 2 * margin
    grid_h = h - top_bar - 2 * margin - 6 * mm
    cell_w = (grid_w - 3 * gap) / 4
    cell_h = (grid_h - 2 * gap) / 3

    for row in range(3):
        for col in range(4):
            month_idx = row * 4 + col
            if month_idx >= 12:
                break
            cx = margin + col * (cell_w + gap)
            cy = h - top_bar - margin - (row + 1) * cell_h - row * gap

            pdf.setFillColor(accent)
            pdf.rect(cx, cy + cell_h - 5 * mm, cell_w, 5 * mm, fill=1, stroke=0)
            pdf.setFillColor(_pc("#FFFFFF"))
            _set_font(pdf, font_family, "Helvetica-Bold", 5)
            pdf.drawCentredString(cx + cell_w / 2, cy + cell_h - 3.8 * mm, MONTHS_PT[month_idx])

            pdf.setStrokeColor(border_c)
            pdf.setLineWidth(0.3)
            pdf.rect(cx, cy, cell_w, cell_h, fill=0, stroke=1)

            col_w = cell_w / 7
            header_y = cy + cell_h - 7 * mm
            _set_font(pdf, font_family, "Helvetica", 3)
            pdf.setFillColor(text_c)
            for d in range(7):
                pdf.drawCentredString(cx + col_w * d + col_w / 2, header_y, DAYS_SHORT[d])

            try:
                first_day = datetime.date(base_date.year, month_idx + 1, 1)
                if month_idx + 1 < 12:
                    next_month = datetime.date(base_date.year, month_idx + 2, 1)
                else:
                    next_month = datetime.date(base_date.year + 1, 1, 1)
                days_in_month = (next_month - first_day).days
                start_weekday = (first_day.weekday()) % 7
            except ValueError:
                continue

            _set_font(pdf, font_family, "Helvetica", 3)
            for day in range(1, days_in_month + 1):
                pos = start_weekday + day - 1
                dr = pos // 7
                dc = pos % 7
                dx = cx + col_w * dc + col_w / 2
                dy = header_y - 3 * mm - dr * 3 * mm
                if dy < cy + 1 * mm:
                    break
                pdf.setFillColor(text_c)
                pdf.drawCentredString(dx, dy, str(day))


def _draw_planejamento_anual(pdf, w, h, palette, base_date, font_family=None):
    accent = _pc(_resolve_color("_accent_", palette) or "#4A90D9")
    text_c = _pc(_resolve_color("_text_", palette) or "#333333")
    border_c = _pc(_resolve_color("_border_", palette) or "#E0E0E0")
    bg = _pc(_resolve_color("_background_", palette) or "#FFFFFF")

    pdf.setFillColor(bg)
    pdf.rect(0, 0, w, h, fill=1, stroke=0)

    top_bar = 18 * mm
    pdf.setFillColor(accent)
    pdf.rect(0, h - top_bar, w, top_bar, fill=1, stroke=0)
    pdf.setFillColor(_pc("#FFFFFF"))
    _set_font(pdf, font_family, "Helvetica-Bold", 12)
    pdf.drawCentredString(w / 2, h - 13 * mm, f"PLANEJAMENTO {base_date.year}")

    margin = 10 * mm
    y = h - top_bar - margin
    available_h = y - margin
    row_h = available_h / 12

    for m in range(12):
        pdf.setStrokeColor(border_c)
        pdf.setLineWidth(0.3)
        pdf.line(margin, y, w - margin, y)
        y -= row_h

        pdf.setFillColor(accent)
        pdf.roundRect(margin, y + 1 * mm, 22 * mm, 6 * mm, 2 * mm, fill=1, stroke=0)
        pdf.setFillColor(_pc("#FFFFFF"))
        _set_font(pdf, font_family, "Helvetica-Bold", 5)
        pdf.drawCentredString(margin + 11 * mm, y + 2.8 * mm, MONTHS_SHORT[m])

        pdf.setStrokeColor(border_c)
        pdf.setLineWidth(0.2)
        for li in range(2):
            ly = y + 1.5 * mm + li * 2 * mm
            pdf.line(margin + 24 * mm, ly, w - margin, ly)

    pdf.setFillColor(border_c)
    _set_font(pdf, font_family, "Helvetica", 5)
    pdf.drawCentredString(w / 2, 8 * mm, "Agenda Creator Pro")


# ── Pre-built daily templates ──────────────────────────────────────────

def _build_1dpp_objects(palette, w_mm=148, h_mm=210, style="minimalista"):
    if style == "executivo":
        return _build_1dpp_executivo(palette, w_mm, h_mm)
    elif style == "kawaii":
        return _build_1dpp_kawaii(palette, w_mm, h_mm)
    elif style == "floral":
        return _build_1dpp_floral(palette, w_mm, h_mm)
    return _build_1dpp_minimalista(palette, w_mm, h_mm)


def _build_2dpp_objects(palette, w_mm=148, h_mm=210, style="minimalista"):
    if style == "executivo":
        return _build_2dpp_executivo(palette, w_mm, h_mm)
    elif style == "kawaii":
        return _build_2dpp_kawaii(palette, w_mm, h_mm)
    elif style == "floral":
        return _build_2dpp_floral(palette, w_mm, h_mm)
    return _build_2dpp_minimalista(palette, w_mm, h_mm)


def _build_1dpp_minimalista(palette, w_mm=148, h_mm=210):
    objs = []
    m, ac, tx, bd, wh, hi, sec, bg = 8, "_accent_", "_text_", "_border_", "_white_", "_highlight_", "_secondary_", "_background_"
    lh = (w_mm - 2*m - 4) * 0.6
    rx = m + lh + 4
    rw = w_mm - 2*m - lh - 4
    by = 31
    bh = h_mm - 47

    objs.append({"id": "bg", "obj_type": "RECTANGLE", "x": 0, "y": 0, "w": w_mm, "h": h_mm, "bg_color": bg})
    objs.append({"id": "hdr", "obj_type": "RECTANGLE", "x": 0, "y": 0, "w": w_mm, "h": 28, "bg_color": ac})
    objs.append({"id": "dn", "obj_type": "TEXT", "semantic": "DAY_NAME", "value": "TERCA", "x": m, "y": 3, "w": 60, "h": 8, "font_name": "Helvetica-Bold", "font_size": 10, "color": wh, "bold": True})
    objs.append({"id": "dd", "obj_type": "TEXT", "semantic": "DAY_NUMBER", "value": "15", "x": m, "y": 11, "w": 25, "h": 14, "font_name": "Helvetica-Bold", "font_size": 22, "color": wh, "bold": True})
    objs.append({"id": "my", "obj_type": "TEXT", "semantic": "MONTH_NAME", "value": "julho 2026", "x": 38, "y": 14, "w": 50, "h": 7, "font_name": "Helvetica", "font_size": 9, "color": wh})
    objs.append({"id": "al", "obj_type": "LINE", "x": 0, "y": 28, "w": w_mm, "h": 0, "color": ac, "border_width": 1.5})
    objs.append({"id": "sp", "obj_type": "TEXT", "semantic": "SECTION_TITLE", "value": "PRIORIDADES", "x": m, "y": by, "w": 35, "h": 6, "font_name": "Helvetica-Bold", "font_size": 7, "color": ac, "bold": True})
    for i in range(5):
        cy = by + 8 + i * 10
        objs.append({"id": f"cb{i}", "obj_type": "CHECKBOX", "x": m, "y": cy, "w": 3.5, "h": 3.5, "color": ac})
        objs.append({"id": f"tk{i}", "obj_type": "TEXT", "semantic": "TASK_TEXT", "value": "", "x": m+5, "y": cy-0.5, "w": lh-8, "h": 5, "font_name": "Helvetica", "font_size": 6, "color": tx})
    objs.append({"id": "vd", "obj_type": "LINE", "x": m+lh+2, "y": by, "w": 0, "h": bh, "color": bd, "border_width": 0.5})
    objs.append({"id": "sa", "obj_type": "TEXT", "semantic": "SECTION_TITLE", "value": "AGENDA CREATOR PRO", "x": rx, "y": by, "w": 35, "h": 6, "font_name": "Helvetica-Bold", "font_size": 7, "color": ac, "bold": True})
    for i, t_str in enumerate(["08:00","09:00","10:00","11:00","12:00","13:00","14:00","15:00","16:00","17:00","18:00"]):
        ty = by + 8 + i * 10
        objs.append({"id": f"tm{i}", "obj_type": "TEXT", "semantic": "TIME_SLOT", "value": t_str, "x": rx, "y": ty, "w": 12, "h": 5, "font_name": "Helvetica", "font_size": 5, "color": tx})
        objs.append({"id": f"tl{i}", "obj_type": "LINE", "x": rx+14, "y": ty+3, "w": rw-16, "h": 0, "color": bd, "border_width": 0.2})
    objs.append({"id": "pn", "obj_type": "TEXT", "semantic": "PAGE_NUMBER", "value": "1 / 365", "x": 0, "y": h_mm-10, "w": w_mm, "h": 5, "font_name": "Helvetica", "font_size": 5, "color": tx, "align": "center"})
    return objs


def _build_1dpp_executivo(palette, w_mm=148, h_mm=210):
    objs = []
    m, a, t, b, w, bg = 10, "_accent_", "_text_", "_border_", "_white_", "_background_"
    objs.append({"id": "bg", "obj_type": "RECTANGLE", "x": 0, "y": 0, "w": w_mm, "h": h_mm, "bg_color": bg})
    objs.append({"id": "hdr", "obj_type": "RECTANGLE", "x": 0, "y": 0, "w": w_mm, "h": 24, "bg_color": a})
    objs.append({"id": "dd", "obj_type": "TEXT", "semantic": "DAY_NUMBER", "value": "15", "x": m, "y": 8, "w": 22, "h": 18, "font_name": "Helvetica-Bold", "font_size": 20, "color": w, "bold": True})
    objs.append({"id": "dn", "obj_type": "TEXT", "semantic": "DAY_NAME", "value": "TERCA", "x": m+24, "y": 4, "w": 50, "h": 8, "font_name": "Helvetica-Bold", "font_size": 12, "color": w, "bold": True})
    objs.append({"id": "my", "obj_type": "TEXT", "semantic": "MONTH_NAME", "value": "julho 2026", "x": m+24, "y": 13, "w": 50, "h": 6, "font_name": "Helvetica", "font_size": 8, "color": w})
    objs.append({"id": "al", "obj_type": "LINE", "x": 0, "y": 24, "w": w_mm, "h": 0, "color": a, "border_width": 2})
    by = 30
    objs.append({"id": "sp", "obj_type": "TEXT", "semantic": "SECTION_TITLE", "value": "TAREFAS DO DIA", "x": m, "y": by, "w": 50, "h": 5, "font_name": "Helvetica-Bold", "font_size": 6, "color": a, "bold": True})
    for i in range(8):
        cy = by + 7 + i * 8
        objs.append({"id": f"cb{i}", "obj_type": "CHECKBOX", "x": m, "y": cy, "w": 3, "h": 3, "color": a})
        objs.append({"id": f"tk{i}", "obj_type": "TEXT", "semantic": "TASK_TEXT", "value": "", "x": m+5, "y": cy-0.5, "w": w_mm-2*m-8, "h": 4, "font_name": "Helvetica", "font_size": 5, "color": t})
    sy = by + 75
    objs.append({"id": "hl", "obj_type": "LINE", "x": m, "y": sy, "w": w_mm-2*m, "h": 0, "color": b, "border_width": 0.3})
    objs.append({"id": "sa", "obj_type": "TEXT", "semantic": "SECTION_TITLE", "value": "HORARIOS", "x": m, "y": sy-7, "w": 40, "h": 5, "font_name": "Helvetica-Bold", "font_size": 6, "color": a, "bold": True})
    for i, t_str in enumerate(["08:00","09:00","10:00","11:00","12:00","13:00","14:00","15:00","16:00","17:00","18:00"]):
        ty = sy - 14 - i * 7
        objs.append({"id": f"tm{i}", "obj_type": "TEXT", "semantic": "TIME_SLOT", "value": t_str, "x": m, "y": ty, "w": 12, "h": 4, "font_name": "Helvetica", "font_size": 5, "color": t})
        objs.append({"id": f"tl{i}", "obj_type": "LINE", "x": m+14, "y": ty+2, "w": w_mm-2*m-16, "h": 0, "color": b, "border_width": 0.15})
    objs.append({"id": "pn", "obj_type": "TEXT", "semantic": "PAGE_NUMBER", "value": "1 / 365", "x": 0, "y": h_mm-8, "w": w_mm, "h": 4, "font_name": "Helvetica", "font_size": 5, "color": t, "align": "center"})
    return objs


def _build_1dpp_kawaii(palette, w_mm=148, h_mm=210):
    objs = []
    m, a, t, w, hi, bg = 10, "_accent_", "_text_", "_white_", "_highlight_", "_background_"
    objs.append({"id": "bg", "obj_type": "RECTANGLE", "x": 0, "y": 0, "w": w_mm, "h": h_mm, "bg_color": bg})
    objs.append({"id": "hdr", "obj_type": "ROUNDED_RECTANGLE", "x": m, "y": h_mm-30, "w": w_mm-2*m, "h": 26, "bg_color": a, "radius": 5})
    objs.append({"id": "dn", "obj_type": "TEXT", "semantic": "DAY_NAME", "value": "TERCA", "x": m+8, "y": h_mm-28, "w": 60, "h": 7, "font_name": "Helvetica-Bold", "font_size": 10, "color": w, "bold": True})
    objs.append({"id": "dd", "obj_type": "TEXT", "semantic": "DAY_NUMBER", "value": "15", "x": m+8, "y": h_mm-24, "w": 20, "h": 14, "font_name": "Helvetica-Bold", "font_size": 14, "color": w, "bold": True})
    objs.append({"id": "my", "obj_type": "TEXT", "semantic": "MONTH_NAME", "value": "julho 2026", "x": m+30, "y": h_mm-16, "w": 50, "h": 6, "font_name": "Helvetica", "font_size": 8, "color": w})
    objs.append({"id": "d1", "obj_type": "DECORATION", "shape": "heart", "x": w_mm-m-16, "y": h_mm-26, "w": 10, "h": 10, "color": w})
    by = h_mm - 36
    objs.append({"id": "sp", "obj_type": "TEXT", "semantic": "SECTION_TITLE", "value": "tarefinhas", "x": m, "y": by, "w": 40, "h": 5, "font_name": "Helvetica", "font_size": 7, "color": a})
    for i in range(6):
        cy = by - 8 - i * 11
        objs.append({"id": f"cb{i}", "obj_type": "CHECKBOX", "x": m, "y": cy, "w": 4, "h": 4, "color": a})
        objs.append({"id": f"tk{i}", "obj_type": "TEXT", "semantic": "TASK_TEXT", "value": "", "x": m+6, "y": cy-0.5, "w": w_mm-2*m-10, "h": 5, "font_name": "Helvetica", "font_size": 6, "color": t})
    ny = by - 80
    objs.append({"id": "sn", "obj_type": "TEXT", "semantic": "SECTION_TITLE", "value": "notas", "x": m, "y": ny, "w": 30, "h": 5, "font_name": "Helvetica", "font_size": 7, "color": a})
    for i in range(8):
        ly = ny - 7 - i * 6
        objs.append({"id": f"rl{i}", "obj_type": "LINE", "x": m, "y": ly, "w": w_mm-2*m, "h": 0, "color": "_border_", "border_width": 0.2})
    objs.append({"id": "d2", "obj_type": "DECORATION", "shape": "star", "x": w_mm/2-5, "y": 4, "w": 10, "h": 10, "color": a})
    objs.append({"id": "pn", "obj_type": "TEXT", "semantic": "PAGE_NUMBER", "value": "1 / 365", "x": 0, "y": 14, "w": w_mm, "h": 4, "font_name": "Helvetica", "font_size": 5, "color": t, "align": "center"})
    return objs


def _build_1dpp_floral(palette, w_mm=148, h_mm=210):
    objs = []
    m, a, t, b, w, hi, bg = 10, "_accent_", "_text_", "_border_", "_white_", "_highlight_", "_background_"
    objs.append({"id": "bg", "obj_type": "RECTANGLE", "x": 0, "y": 0, "w": w_mm, "h": h_mm, "bg_color": bg})
    objs.append({"id": "tl", "obj_type": "LINE", "x": m, "y": h_mm-8, "w": w_mm-2*m, "h": 0, "color": a, "border_width": 0.5})
    objs.append({"id": "dn", "obj_type": "TEXT", "semantic": "DAY_NAME", "value": "TERCA", "x": m, "y": h_mm-22, "w": 60, "h": 8, "font_name": "Times-Bold", "font_size": 12, "color": a, "bold": True})
    objs.append({"id": "dd", "obj_type": "TEXT", "semantic": "DAY_NUMBER", "value": "15", "x": m, "y": h_mm-46, "w": 25, "h": 16, "font_name": "Times-Bold", "font_size": 16, "color": t, "bold": True})
    objs.append({"id": "my", "obj_type": "TEXT", "semantic": "MONTH_NAME", "value": "julho 2026", "x": m+28, "y": h_mm-36, "w": 50, "h": 6, "font_name": "Times-Italic", "font_size": 9, "color": t})
    objs.append({"id": "bl", "obj_type": "LINE", "x": m, "y": h_mm-48, "w": w_mm-2*m, "h": 0, "color": a, "border_width": 1})
    objs.append({"id": "d1", "obj_type": "DECORATION", "shape": "flower", "x": w_mm-m-14, "y": h_mm-44, "w": 12, "h": 12, "color": a})
    by = h_mm - 56
    objs.append({"id": "sp", "obj_type": "TEXT", "semantic": "SECTION_TITLE", "value": "PRIORIDADES", "x": m, "y": by, "w": 40, "h": 5, "font_name": "Times-Bold", "font_size": 6, "color": a, "bold": True})
    for i in range(5):
        cy = by - 8 - i * 10
        objs.append({"id": f"d{i}", "obj_type": "DECORATION", "shape": "flower", "x": m, "y": cy, "w": 4, "h": 4, "color": a})
        objs.append({"id": f"tk{i}", "obj_type": "TEXT", "semantic": "TASK_TEXT", "value": "", "x": m+6, "y": cy-0.5, "w": w_mm-2*m-10, "h": 5, "font_name": "Times-Roman", "font_size": 6, "color": t})
    objs.append({"id": "hl", "obj_type": "LINE", "x": m, "y": by-60, "w": w_mm-2*m, "h": 0, "color": b, "border_width": 0.3})
    objs.append({"id": "sa", "obj_type": "TEXT", "semantic": "SECTION_TITLE", "value": "HORARIOS", "x": m, "y": by-68, "w": 40, "h": 5, "font_name": "Times-Bold", "font_size": 6, "color": a, "bold": True})
    for i, t_str in enumerate(["08:00","09:00","10:00","11:00","12:00","13:00","14:00","15:00","16:00","17:00","18:00"]):
        ty = by - 76 - i * 7
        objs.append({"id": f"tm{i}", "obj_type": "TEXT", "semantic": "TIME_SLOT", "value": t_str, "x": m, "y": ty, "w": 12, "h": 4, "font_name": "Times-Roman", "font_size": 5, "color": t})
        objs.append({"id": f"tl{i}", "obj_type": "LINE", "x": m+14, "y": ty+2, "w": w_mm-2*m-16, "h": 0, "color": b, "border_width": 0.15})
    objs.append({"id": "bl2", "obj_type": "LINE", "x": m, "y": 20, "w": w_mm-2*m, "h": 0, "color": a, "border_width": 0.5})
    objs.append({"id": "d2", "obj_type": "DECORATION", "shape": "flower", "x": w_mm/2-6, "y": 4, "w": 12, "h": 12, "color": a})
    objs.append({"id": "pn", "obj_type": "TEXT", "semantic": "PAGE_NUMBER", "value": "1 / 365", "x": 0, "y": 24, "w": w_mm, "h": 4, "font_name": "Times-Roman", "font_size": 5, "color": t, "align": "center"})
    return objs


def _build_2dpp_minimalista(palette, w_mm=148, h_mm=210):
    objs = []
    m, a, t, b, w, bg = 8, "_accent_", "_text_", "_border_", "_white_", "_background_"
    pg = 6
    ph = (h_mm - 26 - 2*m - pg) / 2
    objs.append({"id": "bg", "obj_type": "RECTANGLE", "x": 0, "y": 0, "w": w_mm, "h": h_mm, "bg_color": bg})
    objs.append({"id": "tb", "obj_type": "RECTANGLE", "x": 0, "y": 0, "w": w_mm, "h": 20, "bg_color": a})
    objs.append({"id": "tt", "obj_type": "TEXT", "value": "AGENDA DIARIA", "x": 0, "y": 5, "w": w_mm, "h": 10, "font_name": "Helvetica-Bold", "font_size": 10, "color": w, "align": "center"})
    for s in range(2):
        py = 20 + m + s * (ph + pg)
        hh = 20
        objs.append({"id": f"p{s}bg", "obj_type": "ROUNDED_RECTANGLE", "x": m, "y": py, "w": w_mm-2*m, "h": ph, "bg_color": bg, "border": True, "border_color": b, "border_width": 0.3, "radius": 2})
        objs.append({"id": f"p{s}hd", "obj_type": "RECTANGLE", "x": m, "y": py, "w": w_mm-2*m, "h": hh, "bg_color": a})
        objs.append({"id": f"dn{s}", "obj_type": "TEXT", "semantic": "DAY_NAME", "value": "TERCA" if s==0 else "QUARTA", "x": m+3, "y": py+2, "w": 50, "h": 7, "font_name": "Helvetica-Bold", "font_size": 8, "color": w, "bold": True})
        objs.append({"id": f"dd{s}", "obj_type": "TEXT", "semantic": "DAY_NUMBER", "value": "15" if s==0 else "16", "x": m+3, "y": py+9, "w": 20, "h": 12, "font_name": "Helvetica-Bold", "font_size": 22, "color": w, "bold": True})
        objs.append({"id": f"my{s}", "obj_type": "TEXT", "semantic": "MONTH_NAME", "value": "julho 2026" if s==0 else "agosto 2026", "x": m+25, "y": py+12, "w": 40, "h": 6, "font_name": "Helvetica", "font_size": 7, "color": w})
        by = py + hh + 2
        cw = (w_mm - 2*m - 4) / 2
        rx = m + cw + 4
        objs.append({"id": f"st{s}", "obj_type": "TEXT", "semantic": "SECTION_TITLE", "value": "TAREFAS", "x": m+2, "y": by, "w": 25, "h": 5, "font_name": "Helvetica-Bold", "font_size": 5, "color": a, "bold": True})
        for i in range(4):
            cy = by + 7 + i * 8
            objs.append({"id": f"cb{s}{i}", "obj_type": "CHECKBOX", "x": m+2, "y": cy, "w": 3, "h": 3, "color": a})
            objs.append({"id": f"tk{s}{i}", "obj_type": "TEXT", "semantic": "TASK_TEXT", "value": "", "x": m+7, "y": cy-0.5, "w": cw-10, "h": 4, "font_name": "Helvetica", "font_size": 5, "color": t})
        objs.append({"id": f"vd{s}", "obj_type": "LINE", "x": m+cw+2, "y": by, "w": 0, "h": ph-hh-8, "color": b, "border_width": 0.3})
        objs.append({"id": f"sn{s}", "obj_type": "TEXT", "semantic": "SECTION_TITLE", "value": "ANOTACOES", "x": rx, "y": by, "w": 25, "h": 5, "font_name": "Helvetica-Bold", "font_size": 5, "color": a, "bold": True})
        for i in range(8):
            ly = by + 8 + i * 5
            if ly > py + ph - 8: break
            objs.append({"id": f"rl{s}{i}", "obj_type": "LINE", "x": rx, "y": ly, "w": cw-2, "h": 0, "color": b, "border_width": 0.2})
    objs.append({"id": "pn", "obj_type": "TEXT", "semantic": "PAGE_NUMBER", "value": "1 / 365", "x": 0, "y": h_mm-6, "w": w_mm, "h": 4, "font_name": "Helvetica", "font_size": 4, "color": t, "align": "center"})
    return objs


def _build_2dpp_executivo(palette, w_mm=148, h_mm=210):
    objs = []
    m, a, t, b, w, bg = 8, "_accent_", "_text_", "_border_", "_white_", "_background_"
    objs.append({"id": "bg", "obj_type": "RECTANGLE", "x": 0, "y": 0, "w": w_mm, "h": h_mm, "bg_color": bg})
    objs.append({"id": "tb", "obj_type": "RECTANGLE", "x": 0, "y": 0, "w": w_mm, "h": 16, "bg_color": a})
    objs.append({"id": "tt", "obj_type": "TEXT", "value": "AGENDA CREATOR PRO", "x": 0, "y": 3, "w": w_mm, "h": 10, "font_name": "Helvetica-Bold", "font_size": 9, "color": w, "align": "center"})
    for s in range(2):
        py = 20 + s * ((h_mm-24)/2)
        objs.append({"id": f"p{s}hd", "obj_type": "RECTANGLE", "x": m, "y": py, "w": 24, "h": 24, "bg_color": a})
        objs.append({"id": f"dd{s}", "obj_type": "TEXT", "semantic": "DAY_NUMBER", "value": "15" if s==0 else "16", "x": m+2, "y": py+2, "w": 20, "h": 20, "font_name": "Helvetica-Bold", "font_size": 22, "color": w, "bold": True})
        objs.append({"id": f"dn{s}", "obj_type": "TEXT", "semantic": "DAY_NAME", "value": "TERCA" if s==0 else "QUARTA", "x": m+28, "y": py+2, "w": 50, "h": 7, "font_name": "Helvetica-Bold", "font_size": 8, "color": t, "bold": True})
        objs.append({"id": f"my{s}", "obj_type": "TEXT", "semantic": "MONTH_NAME", "value": "julho 2026" if s==0 else "agosto 2026", "x": m+28, "y": py+10, "w": 40, "h": 5, "font_name": "Helvetica", "font_size": 6, "color": t})
        by = py + 28
        objs.append({"id": f"sp{s}", "obj_type": "TEXT", "semantic": "SECTION_TITLE", "value": "TAREFAS", "x": m, "y": by, "w": 30, "h": 4, "font_name": "Helvetica-Bold", "font_size": 5, "color": a, "bold": True})
        for i in range(3):
            cy = by + 6 + i * 7
            objs.append({"id": f"cb{s}{i}", "obj_type": "CHECKBOX", "x": m, "y": cy, "w": 3, "h": 3, "color": a})
            objs.append({"id": f"tk{s}{i}", "obj_type": "TEXT", "semantic": "TASK_TEXT", "value": "", "x": m+5, "y": cy-0.5, "w": w_mm-2*m-8, "h": 4, "font_name": "Helvetica", "font_size": 5, "color": t})
        sy = by + 30
        objs.append({"id": f"hl{s}", "obj_type": "LINE", "x": m, "y": sy, "w": w_mm-2*m, "h": 0, "color": b, "border_width": 0.2})
        for i, t_str in enumerate(["08:00","10:00","12:00","14:00","16:00","18:00"]):
            ty = sy + 5 + i * 5
            if ty > py + (h_mm-24)/2 - 10: break
            objs.append({"id": f"tm{s}{i}", "obj_type": "TEXT", "semantic": "TIME_SLOT", "value": t_str, "x": m, "y": ty, "w": 10, "h": 4, "font_name": "Helvetica", "font_size": 4, "color": t})
            objs.append({"id": f"tl{s}{i}", "obj_type": "LINE", "x": m+12, "y": ty+2, "w": w_mm-2*m-14, "h": 0, "color": b, "border_width": 0.15})
    objs.append({"id": "pn", "obj_type": "TEXT", "semantic": "PAGE_NUMBER", "value": "1 / 365", "x": 0, "y": h_mm-6, "w": w_mm, "h": 4, "font_name": "Helvetica", "font_size": 4, "color": t, "align": "center"})
    return objs


def _build_2dpp_kawaii(palette, w_mm=148, h_mm=210):
    objs = []
    m, a, t, w, hi, bg = 10, "_accent_", "_text_", "_white_", "_highlight_", "_background_"
    objs.append({"id": "bg", "obj_type": "RECTANGLE", "x": 0, "y": 0, "w": w_mm, "h": h_mm, "bg_color": bg})
    objs.append({"id": "d1", "obj_type": "DECORATION", "shape": "heart", "x": w_mm/2-6, "y": h_mm-14, "w": 12, "h": 12, "color": a})
    for s in range(2):
        py = 6 + s * ((h_mm-18)/2)
        ph2 = (h_mm-18)/2 - 6
        objs.append({"id": f"p{s}bg", "obj_type": "ROUNDED_RECTANGLE", "x": m, "y": py, "w": w_mm-2*m, "h": ph2, "bg_color": hi, "border": True, "border_color": a, "border_width": 0.3, "radius": 4})
        objs.append({"id": f"p{s}hd", "obj_type": "ROUNDED_RECTANGLE", "x": m, "y": py+ph2-18, "w": w_mm-2*m, "h": 18, "bg_color": a, "radius": 3})
        objs.append({"id": f"dn{s}", "obj_type": "TEXT", "semantic": "DAY_NAME", "value": "TERCA" if s==0 else "QUARTA", "x": m+5, "y": py+ph2-16, "w": 45, "h": 6, "font_name": "Helvetica-Bold", "font_size": 7, "color": w, "bold": True})
        objs.append({"id": f"dd{s}", "obj_type": "TEXT", "semantic": "DAY_NUMBER", "value": "15" if s==0 else "16", "x": m+5, "y": py+ph2-10, "w": 18, "h": 10, "font_name": "Helvetica-Bold", "font_size": 18, "color": w, "bold": True})
        objs.append({"id": f"my{s}", "obj_type": "TEXT", "semantic": "MONTH_NAME", "value": "julho 2026" if s==0 else "agosto 2026", "x": m+25, "y": py+ph2-8, "w": 40, "h": 5, "font_name": "Helvetica", "font_size": 6, "color": w})
        by = py + ph2 - 24
        objs.append({"id": f"sp{s}", "obj_type": "TEXT", "semantic": "SECTION_TITLE", "value": "tarefas", "x": m+5, "y": by, "w": 25, "h": 4, "font_name": "Helvetica", "font_size": 5, "color": a})
        for i in range(3):
            cy = by - 6 - i * 7
            objs.append({"id": f"cb{s}{i}", "obj_type": "CHECKBOX", "x": m+5, "y": cy, "w": 3, "h": 3, "color": a})
            objs.append({"id": f"tk{s}{i}", "obj_type": "TEXT", "semantic": "TASK_TEXT", "value": "", "x": m+10, "y": cy-0.5, "w": w_mm-2*m-15, "h": 4, "font_name": "Helvetica", "font_size": 5, "color": t})
        objs.append({"id": f"sn{s}", "obj_type": "TEXT", "semantic": "SECTION_TITLE", "value": "notas", "x": m+5, "y": py+5, "w": 20, "h": 4, "font_name": "Helvetica", "font_size": 5, "color": a})
        for i in range(4):
            ly = py + 1 + i * 4
            objs.append({"id": f"rl{s}{i}", "obj_type": "LINE", "x": m+5, "y": ly, "w": w_mm-2*m-10, "h": 0, "color": "_border_", "border_width": 0.15})
    objs.append({"id": "pn", "obj_type": "TEXT", "semantic": "PAGE_NUMBER", "value": "1 / 365", "x": 0, "y": 2, "w": w_mm, "h": 4, "font_name": "Helvetica", "font_size": 4, "color": t, "align": "center"})
    return objs


def _build_2dpp_floral(palette, w_mm=148, h_mm=210):
    objs = []
    m, a, t, b, w, bg = 10, "_accent_", "_text_", "_border_", "_white_", "_background_"
    objs.append({"id": "bg", "obj_type": "RECTANGLE", "x": 0, "y": 0, "w": w_mm, "h": h_mm, "bg_color": bg})
    objs.append({"id": "bl", "obj_type": "LINE", "x": m, "y": h_mm-6, "w": w_mm-2*m, "h": 0, "color": a, "border_width": 0.5})
    objs.append({"id": "d1", "obj_type": "DECORATION", "shape": "flower", "x": 4, "y": h_mm-16, "w": 8, "h": 8, "color": a})
    objs.append({"id": "d2", "obj_type": "DECORATION", "shape": "flower", "x": w_mm-12, "y": h_mm-16, "w": 8, "h": 8, "color": a})
    for s in range(2):
        py = 8 + s * ((h_mm-20)/2)
        ph2 = (h_mm-20)/2 - 6
        objs.append({"id": f"p{s}ln", "obj_type": "LINE", "x": m, "y": py+ph2, "w": w_mm-2*m, "h": 0, "color": b, "border_width": 0.3})
        objs.append({"id": f"dn{s}", "obj_type": "TEXT", "semantic": "DAY_NAME", "value": "TERCA" if s==0 else "QUARTA", "x": m, "y": py+ph2-8, "w": 50, "h": 6, "font_name": "Times-Bold", "font_size": 8, "color": a, "bold": True})
        objs.append({"id": f"dd{s}", "obj_type": "TEXT", "semantic": "DAY_NUMBER", "value": "15" if s==0 else "16", "x": m, "y": py+ph2-20, "w": 20, "h": 12, "font_name": "Times-Bold", "font_size": 18, "color": t, "bold": True})
        objs.append({"id": f"my{s}", "obj_type": "TEXT", "semantic": "MONTH_NAME", "value": "julho 2026" if s==0 else "agosto 2026", "x": m+22, "y": py+ph2-16, "w": 40, "h": 5, "font_name": "Times-Italic", "font_size": 6, "color": t})
        objs.append({"id": f"fd{s}", "obj_type": "DECORATION", "shape": "flower", "x": w_mm-m-12, "y": py+ph2-16, "w": 10, "h": 10, "color": a})
        by = py + ph2 - 26
        objs.append({"id": f"sp{s}", "obj_type": "TEXT", "semantic": "SECTION_TITLE", "value": "PRIORIDADES", "x": m, "y": by, "w": 40, "h": 4, "font_name": "Times-Bold", "font_size": 5, "color": a, "bold": True})
        for i in range(3):
            cy = by - 6 - i * 7
            objs.append({"id": f"d{s}{i}", "obj_type": "DECORATION", "shape": "flower", "x": m, "y": cy, "w": 3, "h": 3, "color": a})
            objs.append({"id": f"tk{s}{i}", "obj_type": "TEXT", "semantic": "TASK_TEXT", "value": "", "x": m+5, "y": cy-0.5, "w": w_mm-2*m-10, "h": 4, "font_name": "Times-Roman", "font_size": 5, "color": t})
        objs.append({"id": f"hl{s}", "obj_type": "LINE", "x": m, "y": py+4, "w": w_mm-2*m, "h": 0, "color": b, "border_width": 0.2})
        for i, t_str in enumerate(["08:00","10:00","12:00","14:00","16:00"]):
            ty = py - 2 - i * 4
            if ty < py + 2: break
            objs.append({"id": f"tm{s}{i}", "obj_type": "TEXT", "semantic": "TIME_SLOT", "value": t_str, "x": m, "y": ty, "w": 10, "h": 3, "font_name": "Times-Roman", "font_size": 4, "color": t})
            objs.append({"id": f"tl{s}{i}", "obj_type": "LINE", "x": m+11, "y": ty+1.5, "w": w_mm-2*m-13, "h": 0, "color": b, "border_width": 0.15})
    objs.append({"id": "pn", "obj_type": "TEXT", "semantic": "PAGE_NUMBER", "value": "1 / 365", "x": 0, "y": 4, "w": w_mm, "h": 4, "font_name": "Times-Roman", "font_size": 4, "color": t, "align": "center"})
    return objs


def _build_2dpp_substitutions(page_index, base_date):
    days_pt = ["SEGUNDA", "TERCA", "QUARTA", "QUINTA", "SEXTA", "SABADO", "DOMINGO"]
    months_pt = ["janeiro", "fevereiro", "marco", "abril", "maio", "junho",
                 "julho", "agosto", "setembro", "outubro", "novembro", "dezembro"]

    day_a = base_date + datetime.timedelta(days=page_index * 2)
    day_b = base_date + datetime.timedelta(days=page_index * 2 + 1)

    return {
        "DAY_NAME_0": days_pt[day_a.weekday()],
        "DAY_NUMBER_0": str(day_a.day),
        "MONTH_NAME_0": f"{months_pt[day_a.month - 1]} {day_a.year}",
        "DAY_NAME_1": days_pt[day_b.weekday()],
        "DAY_NUMBER_1": str(day_b.day),
        "MONTH_NAME_1": f"{months_pt[day_b.month - 1]} {day_b.year}",
        "TERCA": days_pt[day_a.weekday()],
        "15": str(day_a.day),
        "julho 2026": f"{months_pt[day_a.month - 1]} {day_a.year}",
        "QUARTA": days_pt[day_b.weekday()],
        "16": str(day_b.day),
        "agosto 2026": f"{months_pt[day_b.month - 1]} {day_b.year}",
        "1 / 365": f"{page_index * 2 + 1} / {page_index * 2 + 2}",
        "PAGE_NUMBER": f"{page_index * 2 + 1} / {page_index * 2 + 2}",
        "PAGE_NUMBER_0": f"{page_index * 2 + 1} / {page_index * 2 + 2}",
        "PAGE_NUMBER_1": f"{page_index * 2 + 1} / {page_index * 2 + 2}",
    }


def _build_1dpp_substitutions(page_index, base_date):
    days_pt = ["SEGUNDA", "TERCA", "QUARTA", "QUINTA", "SEXTA", "SABADO", "DOMINGO"]
    months_pt = ["janeiro", "fevereiro", "marco", "abril", "maio", "junho",
                 "julho", "agosto", "setembro", "outubro", "novembro", "dezembro"]

    d = base_date + datetime.timedelta(days=page_index)
    day_name = days_pt[d.weekday()]
    day_num = str(d.day)
    month_year = f"{months_pt[d.month - 1]} {d.year}"
    page_num = f"{page_index + 1} / 365"
    return {
        "TERCA": day_name,
        "15": day_num,
        "julho 2026": month_year,
        "1 / 365": page_num,
        "DAY_NAME": day_name,
        "DAY_NUMBER": day_num,
        "MONTH_NAME": month_year,
        "PAGE_NUMBER": page_num,
    }


# ── Substitutions ───────────────────────────────────────────────────────

def _get_substitutions_for_page(page_index, page_type, base_date=None, lang="pt"):
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
    page_num = f"{page_index + 1} / 365"

    return {
        "TERCA": day_name,
        "15": day_num,
        "julho 2026": month_year,
        "1 / 365": page_num,
        "DAY_NAME": day_name,
        "DAY_NUMBER": day_num,
        "MONTH_NAME": month_year,
        "PAGE_NUMBER": page_num,
    }


def _get_substitutions_for_2dpp(page_index, base_date, lang="pt"):
    days_pt = ["SEGUNDA", "TERCA", "QUARTA", "QUINTA", "SEXTA", "SABADO", "DOMINGO"]
    months_pt = ["janeiro", "fevereiro", "marco", "abril", "maio", "junho",
                 "julho", "agosto", "setembro", "outubro", "novembro", "dezembro"]

    day_a = base_date + datetime.timedelta(days=page_index * 2)
    day_b = base_date + datetime.timedelta(days=page_index * 2 + 1)

    subs = {}
    subs["DAY_NAME_0"] = days_pt[day_a.weekday()]
    subs["DAY_NUMBER_0"] = str(day_a.day)
    subs["MONTH_NAME_0"] = f"{months_pt[day_a.month - 1]} {day_a.year}"
    subs["DAY_NAME_1"] = days_pt[day_b.weekday()]
    subs["DAY_NUMBER_1"] = str(day_b.day)
    subs["MONTH_NAME_1"] = f"{months_pt[day_b.month - 1]} {day_b.year}"

    subs["TERCA"] = days_pt[day_a.weekday()]
    subs["15"] = str(day_a.day)
    subs["julho 2026"] = f"{months_pt[day_a.month - 1]} {day_a.year}"
    subs["1 / 365"] = f"{page_index * 2 + 1} / 365"

    subs["QUARTA"] = days_pt[day_b.weekday()]
    subs["16"] = str(day_b.day)
    subs["agosto 2026"] = f"{months_pt[day_b.month - 1]} {day_b.year}"
    subs["2 / 365"] = f"{page_index * 2 + 2} / 365"

    return subs


# ── Image-layout generator ─────────────────────────────────────────────

IMAGE_OVERLAY_SEMANTICS = {"DAY_NAME", "DAY_NUMBER", "MONTH_NAME", "PAGE_NUMBER"}
DAY_HEADER_SEMANTICS = {"DAY_NAME", "DAY_NUMBER", "MONTH_NAME"}
DAILY_PAGE_TYPES = {"1dpp", "2dpp"}


def _resolve_daily_templates(templates, page_type):
    """Return the templates that match the agenda's daily page type.

    When several example pages are uploaded, the ones matching the chosen
    daily type are used (rotating). If none match, all are used.
    """
    matching = []
    for img_bytes, bp in templates:
        bp_pt = (bp or {}).get("page_type")
        if bp_pt == page_type or bp_pt not in DAILY_PAGE_TYPES:
            matching.append((img_bytes, bp))
    return matching if matching else templates


def _overlays_for_bp(bp, w_mm, h_mm, style):
    editable = sanitize_blueprint(bp.get("editable_objects", []), w_mm, h_mm)
    overlays = [o for o in editable if o.get("semantic") in IMAGE_OVERLAY_SEMANTICS]
    if not any(o.get("semantic") in DAY_HEADER_SEMANTICS for o in overlays):
        have = {o.get("semantic") for o in overlays}
        for o in _fallback_date_overlays(bp, w_mm, h_mm, style):
            if o.get("semantic") not in have:
                overlays.append(o)
    return overlays


def _fallback_date_overlays(bp, w_mm, h_mm, style):
    """Default date objects when the layout has no detected day-header fields.

    They sit on an unknown image background, so never render them white:
    recolor so the auto-generated dates stay visible on a light layout.
    """
    page_type = bp.get("page_type", "1dpp")
    if page_type == "2dpp":
        template = _build_2dpp_objects(bp.get("palette", {}), w_mm, h_mm, style)
    else:
        template = _build_1dpp_objects(bp.get("palette", {}), w_mm, h_mm, style)
    overlays = [o for o in template if o.get("semantic") in IMAGE_OVERLAY_SEMANTICS]
    fallback_colors = {
        "DAY_NAME": "_text_",
        "DAY_NUMBER": "_accent_",
        "MONTH_NAME": "_text_",
        "PAGE_NUMBER": "_text_",
    }
    for o in overlays:
        new_color = fallback_colors.get(o.get("semantic"))
        if new_color:
            o["color"] = new_color
        if o.get("semantic") == "DAY_NUMBER":
            # White chip behind the day number keeps it visible even on a
            # colored header band.
            o["bg_color"] = "_white_"
            o["radius"] = max(float(o.get("radius") or 0), 2)
    return overlays


def gerar_pdf_imagens_layout(templates, formato="A5", num_pages=7, base_date=None, page_type=None, font=None):
    """Generate a PDF using the user's own example page images as the exact layout.

    ``templates`` is a list of ``(image_bytes, blueprint_dict_or_None)``. Each
    daily page draws the example image full-page and overlays only the dynamic
    date fields at the positions detected by the AI blueprint. Multiple
    example pages rotate in order across the days of the chosen year, keeping
    the Jan-1-to-Dec-31 sequence.
    """
    from PIL import Image
    from reportlab.lib.utils import ImageReader

    if not templates:
        raise ValueError("No image templates provided")

    first_bp = templates[0][1] or {}
    palette = _get_palette(first_bp)
    style = first_bp.get("style", "minimalista")

    if page_type is None:
        page_type = first_bp.get("page_type", "1dpp")
        if page_type not in DAILY_PAGE_TYPES:
            page_type = "1dpp"

    templates = _resolve_daily_templates(templates, page_type)

    w, h = PAGE_SIZES.get(formato.upper(), PAGE_SIZES["A5"])
    w_mm = w / mm
    h_mm = h / mm

    if base_date is None:
        base_date = datetime.date(2026, 1, 1)

    cache = {}
    for img_bytes, bp in templates:
        key = id(img_bytes)
        img = Image.open(BytesIO(img_bytes)).convert("RGB")
        iw, ih = img.size
        scale = min(w / iw, h / ih)
        cache[key] = (img, (iw * scale), (ih * scale), (w - iw * scale) / 2, (h - ih * scale) / 2)

    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=(w, h))
    pdf.setPageCompression(0)

    _draw_dados_pessoais(pdf, w, h, palette, font_family=font)
    pdf.showPage()

    _draw_calendario_anual(pdf, w, h, palette, base_date, font_family=font)
    pdf.showPage()

    _draw_planejamento_anual(pdf, w, h, palette, base_date, font_family=font)
    pdf.showPage()

    if page_type == "2dpp":
        daily_pages = (num_pages + 1) // 2
    else:
        daily_pages = num_pages

    for page_idx in range(daily_pages):
        if page_idx > 0:
            pdf.showPage()

        img_bytes, bp = templates[page_idx % len(templates)]
        img, dw, dh, dx, dy = cache[id(img_bytes)]
        bp = bp or {}
        bpal = _get_palette(bp) or palette

        pdf.setFillColor(_pc("#FFFFFF"))
        pdf.rect(0, 0, w, h, fill=1, stroke=0)
        pdf.drawImage(ImageReader(img), dx, dy, dw, dh)

        if page_type == "2dpp":
            subs = _build_2dpp_substitutions(page_idx, base_date)
        else:
            subs = _build_1dpp_substitutions(page_idx, base_date)

        for obj in _overlays_for_bp(bp, w_mm, h_mm, style):
            _draw_object(pdf, obj, h, bpal, subs, font_family=font)

    pdf.save()
    buffer.seek(0)
    return buffer


def gerar_pdf_imagem_layout(blueprint_dict, image_bytes, formato="A5", num_pages=7, base_date=None, font=None):
    """Single-template wrapper around gerar_pdf_imagens_layout."""
    return gerar_pdf_imagens_layout([(image_bytes, blueprint_dict or {})],
                                    formato=formato, num_pages=num_pages, base_date=base_date, font=font)



# ── Main generator ──────────────────────────────────────────────────────

def gerar_pdf_blueprint(blueprint_dict, formato="A5", num_pages=7, base_date=None, font=None):
    bp = blueprint_dict
    palette = _get_palette(bp)
    editable = bp.get("editable_objects", [])
    style = bp.get("style", "minimalista")

    w, h = PAGE_SIZES.get(formato.upper(), PAGE_SIZES["A5"])
    w_mm = w / mm
    h_mm = h / mm

    if base_date is None:
        base_date = datetime.date(2026, 1, 1)

    page_type = bp.get("page_type", "1dpp")

    if not editable:
        if page_type == "2dpp":
            editable = _build_2dpp_objects(palette, style=style)
        else:
            editable = _build_1dpp_objects(palette, style=style)

    editable = sanitize_blueprint(editable, w_mm, h_mm)
    if not editable:
        editable = _build_1dpp_objects(palette, style=style)
    elif not any(o.get("semantic") in DAY_HEADER_SEMANTICS for o in editable):
        have = {o.get("semantic") for o in editable}
        for o in _fallback_date_overlays(bp, w_mm, h_mm, style):
            if o.get("semantic") not in have:
                editable.append(o)

    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=(w, h))
    pdf.setPageCompression(0)

    _draw_dados_pessoais(pdf, w, h, palette, font_family=font)
    pdf.showPage()

    _draw_calendario_anual(pdf, w, h, palette, base_date, font_family=font)
    pdf.showPage()

    _draw_planejamento_anual(pdf, w, h, palette, base_date, font_family=font)
    pdf.showPage()

    if page_type == "2dpp":
        daily_pages = (num_pages + 1) // 2
    else:
        daily_pages = num_pages

    for page_idx in range(daily_pages):
        if page_idx > 0:
            pdf.showPage()

        bg = _resolve_color("_background_", palette) or "#FFFFFF"
        pdf.setFillColor(_pc(bg))
        pdf.rect(0, 0, w, h, fill=1, stroke=0)

        if page_type == "2dpp":
            subs = _build_2dpp_substitutions(page_idx, base_date)
        else:
            subs = _build_1dpp_substitutions(page_idx, base_date)

        for obj in editable:
            _draw_object(pdf, obj, h, palette, subs, font_family=font)

    pdf.save()
    buffer.seek(0)
    return buffer

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


def _get_palette(blueprint_dict):
    palette = blueprint_dict.get("palette", {})
    if not palette and blueprint_dict.get("colors"):
        if isinstance(blueprint_dict["colors"], list):
            for c in blueprint_dict["colors"]:
                palette[c.get("role", "accent")] = c.get("hex", "#000000")
        else:
            palette = blueprint_dict["colors"]
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


def _draw_dados_pessoais(pdf, w, h, palette):
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
    pdf.setFont("Helvetica-Bold", 14)
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
        pdf.setFont("Helvetica-Bold", 7)
        pdf.drawString(15 * mm, y, label)
        y -= label_h
        pdf.setStrokeColor(border_c)
        pdf.setLineWidth(0.4)
        pdf.line(15 * mm, y, w - 15 * mm, y)
        y -= (field_h_mm - label_h) * mm

    pdf.setFillColor(border_c)
    pdf.setFont("Helvetica", 5)
    pdf.drawCentredString(w / 2, 8 * mm, "Agenda Creator Pro")


def _draw_calendario_anual(pdf, w, h, palette, base_date):
    accent = _pc(_resolve_color("_accent_", palette) or "#4A90D9")
    text_c = _pc(_resolve_color("_text_", palette) or "#333333")
    border_c = _pc(_resolve_color("_border_", palette) or "#E0E0E0")
    highlight = _pc(_resolve_color("_highlight_", palette) or "#F0F0F0")
    bg = _pc(_resolve_color("_background_", palette) or "#FFFFFF")

    pdf.setFillColor(bg)
    pdf.rect(0, 0, w, h, fill=1, stroke=0)

    top_bar = 20 * mm
    pdf.setFillColor(accent)
    pdf.rect(0, h - top_bar, w, top_bar, fill=1, stroke=0)
    pdf.setFillColor(_pc("#FFFFFF"))
    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawCentredString(w / 2, h - 14 * mm, f"CALENDÁRIO {base_date.year}")

    margin = 10 * mm
    grid_w = w - 2 * margin
    grid_h = h - top_bar - 2 * margin - 10 * mm
    cell_w = grid_w / 4
    cell_h = grid_h / 3

    for row in range(3):
        for col in range(4):
            month_idx = row * 4 + col
            if month_idx >= 12:
                break
            cx = margin + col * cell_w
            cy = h - top_bar - margin - (row + 1) * cell_h

            pdf.setFillColor(accent)
            pdf.rect(cx, cy + cell_h - 6 * mm, cell_w, 6 * mm, fill=1, stroke=0)
            pdf.setFillColor(_pc("#FFFFFF"))
            pdf.setFont("Helvetica-Bold", 6)
            pdf.drawCentredString(cx + cell_w / 2, cy + cell_h - 4.5 * mm, MONTHS_PT[month_idx])

            pdf.setStrokeColor(border_c)
            pdf.setLineWidth(0.3)
            pdf.rect(cx, cy, cell_w, cell_h, fill=0, stroke=1)

            col_w = cell_w / 7
            header_y = cy + cell_h - 9 * mm
            pdf.setFont("Helvetica", 3.5)
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

            pdf.setFont("Helvetica", 3.5)
            for day in range(1, days_in_month + 1):
                pos = start_weekday + day - 1
                dr = pos // 7
                dc = pos % 7
                dx = cx + col_w * dc + col_w / 2
                dy = header_y - 3 * mm - dr * 3.8 * mm
                if dy < cy + 1 * mm:
                    break
                pdf.setFillColor(text_c)
                pdf.drawCentredString(dx, dy, str(day))


def _draw_planejamento_anual(pdf, w, h, palette, base_date):
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
    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawCentredString(w / 2, h - 14 * mm, f"PLANEJAMENTO {base_date.year}")

    margin = 12 * mm
    y = h - top_bar - margin
    row_h = 14 * mm

    for m in range(12):
        if y - row_h < margin:
            break
        pdf.setStrokeColor(border_c)
        pdf.setLineWidth(0.3)
        pdf.line(margin, y, w - margin, y)
        y -= row_h

        pdf.setFillColor(accent)
        pdf.roundRect(margin, y + 2 * mm, 25 * mm, 8 * mm, 2 * mm, fill=1, stroke=0)
        pdf.setFillColor(_pc("#FFFFFF"))
        pdf.setFont("Helvetica-Bold", 5)
        pdf.drawCentredString(margin + 12.5 * mm, y + 4.5 * mm, MONTHS_SHORT[m])

        pdf.setStrokeColor(border_c)
        pdf.setLineWidth(0.2)
        for li in range(3):
            ly = y + 2 * mm + li * 2.5 * mm
            pdf.line(margin + 28 * mm, ly, w - margin, ly)

    pdf.setFillColor(border_c)
    pdf.setFont("Helvetica", 5)
    pdf.drawCentredString(w / 2, 8 * mm, "Agenda Creator Pro")


# ── Pre-built daily templates ──────────────────────────────────────────

def _build_1dpp_objects(palette, w_mm=148, h_mm=210):
    """Build a 1DPP page layout: header + 2-column body with checkboxes/schedule."""
    objs = []
    accent = "_accent_"
    text = "_text_"
    border = "_border_"
    white = "_white_"
    highlight = "_highlight_"
    secondary = "_secondary_"
    bg = "_background_"

    margin = 8
    col_gap = 4
    header_h = 28
    body_y = header_h + 3
    body_h = h_mm - header_h - 16
    left_w = (w_mm - 2 * margin - col_gap) * 0.6
    right_x = margin + left_w + col_gap
    right_w = w_mm - 2 * margin - left_w - col_gap

    objs.append({"id": "bg_rect", "obj_type": "RECTANGLE", "x": 0, "y": 0, "w": w_mm, "h": h_mm, "bg_color": bg})
    objs.append({"id": "header_bg", "obj_type": "RECTANGLE", "x": 0, "y": 0, "w": w_mm, "h": header_h, "bg_color": accent})
    objs.append({"id": "day_name", "obj_type": "TEXT", "semantic": "DAY_NAME", "value": "TERCA",
                 "x": margin, "y": 3, "w": 60, "h": 8, "font_name": "Helvetica-Bold", "font_size": 10,
                 "color": white, "bold": True})
    objs.append({"id": "day_number", "obj_type": "TEXT", "semantic": "DAY_NUMBER", "value": "15",
                 "x": margin, "y": 11, "w": 25, "h": 14, "font_name": "Helvetica-Bold", "font_size": 28,
                 "color": white, "bold": True})
    objs.append({"id": "month_year", "obj_type": "TEXT", "semantic": "MONTH_NAME", "value": "julho 2026",
                 "x": 38, "y": 14, "w": 50, "h": 7, "font_name": "Helvetica", "font_size": 9,
                 "color": white})
    objs.append({"id": "accent_line", "obj_type": "LINE", "x": 0, "y": header_h, "w": w_mm, "h": 0,
                 "color": accent, "border_width": 1.5})

    objs.append({"id": "section_pri", "obj_type": "TEXT", "semantic": "SECTION_TITLE", "value": "PRIORIDADES",
                 "x": margin, "y": body_y, "w": 35, "h": 6,
                 "font_name": "Helvetica-Bold", "font_size": 7, "color": accent, "bold": True})

    for i in range(5):
        cy = body_y + 8 + i * 10
        objs.append({"id": f"cb_{i}", "obj_type": "CHECKBOX", "x": margin, "y": cy, "w": 3.5, "h": 3.5, "color": accent})
        objs.append({"id": f"task_{i}", "obj_type": "TEXT", "semantic": "TASK_TEXT", "value": "",
                     "x": margin + 5, "y": cy - 0.5, "w": left_w - 8, "h": 5,
                     "font_name": "Helvetica", "font_size": 6, "color": text})

    objs.append({"id": "vdivider", "obj_type": "LINE", "x": margin + left_w + col_gap / 2, "y": body_y,
                 "w": 0, "h": body_h, "color": border, "border_width": 0.5})

    objs.append({"id": "section_sched", "obj_type": "TEXT", "semantic": "SECTION_TITLE", "value": "AGENDA",
                 "x": right_x, "y": body_y, "w": 35, "h": 6,
                 "font_name": "Helvetica-Bold", "font_size": 7, "color": accent, "bold": True})

    times = ["08:00", "09:00", "10:00", "11:00", "12:00", "13:00", "14:00", "15:00", "16:00", "17:00", "18:00"]
    for i, t in enumerate(times):
        ty = body_y + 8 + i * 10
        objs.append({"id": f"time_{i}", "obj_type": "TEXT", "semantic": "TIME_SLOT", "value": t,
                     "x": right_x, "y": ty, "w": 12, "h": 5, "font_name": "Helvetica", "font_size": 5, "color": text})
        objs.append({"id": f"tline_{i}", "obj_type": "LINE", "x": right_x + 14, "y": ty + 3,
                     "w": right_w - 16, "h": 0, "color": border, "border_width": 0.2})

    objs.append({"id": "page_num", "obj_type": "TEXT", "semantic": "PAGE_NUMBER", "value": "1 / 365",
                 "x": 0, "y": h_mm - 10, "w": w_mm, "h": 5, "font_name": "Helvetica", "font_size": 5,
                 "color": text, "align": "center"})

    return objs


def _build_2dpp_objects(palette, w_mm=148, h_mm=210):
    """Build a 2DPP page layout: two day panels stacked vertically."""
    objs = []
    accent = "_accent_"
    text = "_text_"
    border = "_border_"
    white = "_white_"
    bg = "_background_"

    margin = 8
    panel_gap = 6
    top_bar = 20
    panel_h = (h_mm - top_bar - 2 * margin - panel_gap) / 2

    objs.append({"id": "bg_rect", "obj_type": "RECTANGLE", "x": 0, "y": 0, "w": w_mm, "h": h_mm, "bg_color": bg})
    objs.append({"id": "title_bar", "obj_type": "RECTANGLE", "x": 0, "y": 0, "w": w_mm, "h": top_bar, "bg_color": accent})
    objs.append({"id": "title_text", "obj_type": "TEXT", "value": "AGENDA DIARIA",
                 "x": 0, "y": 5, "w": w_mm, "h": 10, "font_name": "Helvetica-Bold", "font_size": 10,
                 "color": white, "align": "center"})

    for side in range(2):
        panel_y = top_bar + margin + side * (panel_h + panel_gap)
        header_h = 22

        objs.append({"id": f"panel_{side}_bg", "obj_type": "ROUNDED_RECTANGLE",
                     "x": margin, "y": panel_y, "w": w_mm - 2 * margin, "h": panel_h,
                     "bg_color": bg, "border": True, "border_color": border, "border_width": 0.3, "radius": 2})
        objs.append({"id": f"panel_{side}_header", "obj_type": "RECTANGLE",
                     "x": margin, "y": panel_y, "w": w_mm - 2 * margin, "h": header_h,
                     "bg_color": accent})
        objs.append({"id": f"day_name_{side}", "obj_type": "TEXT", "semantic": "DAY_NAME",
                     "value": "TERCA" if side == 0 else "QUARTA",
                     "x": margin + 3, "y": panel_y + 2, "w": 50, "h": 7,
                     "font_name": "Helvetica-Bold", "font_size": 8, "color": white, "bold": True})
        objs.append({"id": f"day_num_{side}", "obj_type": "TEXT", "semantic": "DAY_NUMBER",
                     "value": "15" if side == 0 else "16",
                     "x": margin + 3, "y": panel_y + 9, "w": 20, "h": 12,
                     "font_name": "Helvetica-Bold", "font_size": 22, "color": white, "bold": True})
        objs.append({"id": f"month_{side}", "obj_type": "TEXT", "semantic": "MONTH_NAME",
                     "value": "julho 2026" if side == 0 else "agosto 2026",
                     "x": margin + 25, "y": panel_y + 12, "w": 40, "h": 6,
                     "font_name": "Helvetica", "font_size": 7, "color": white})

        body_y = panel_y + header_h + 2
        body_h_inner = panel_h - header_h - 6
        col_w = (w_mm - 2 * margin - 4) / 2
        right_x = margin + col_w + 4

        objs.append({"id": f"section_pri_{side}", "obj_type": "TEXT", "semantic": "SECTION_TITLE",
                     "value": "TAREFAS",
                     "x": margin + 2, "y": body_y, "w": 25, "h": 5,
                     "font_name": "Helvetica-Bold", "font_size": 5, "color": accent, "bold": True})

        for i in range(4):
            cy = body_y + 7 + i * 8
            objs.append({"id": f"cb_{side}_{i}", "obj_type": "CHECKBOX",
                         "x": margin + 2, "y": cy, "w": 3, "h": 3, "color": accent})
            objs.append({"id": f"task_{side}_{i}", "obj_type": "TEXT", "semantic": "TASK_TEXT", "value": "",
                         "x": margin + 7, "y": cy - 0.5, "w": col_w - 10, "h": 4,
                         "font_name": "Helvetica", "font_size": 5, "color": text})

        objs.append({"id": f"vdiv_{side}", "obj_type": "LINE",
                     "x": margin + col_w + 2, "y": body_y, "w": 0, "h": body_h_inner - 4,
                     "color": border, "border_width": 0.3})

        objs.append({"id": f"section_notes_{side}", "obj_type": "TEXT", "semantic": "SECTION_TITLE",
                     "value": "ANOTACOES",
                     "x": right_x, "y": body_y, "w": 25, "h": 5,
                     "font_name": "Helvetica-Bold", "font_size": 5, "color": accent, "bold": True})

        for i in range(8):
            ly = body_y + 8 + i * 5
            if ly > panel_y + panel_h - 8:
                break
            objs.append({"id": f"rule_{side}_{i}", "obj_type": "LINE",
                         "x": right_x, "y": ly, "w": col_w - 2, "h": 0,
                         "color": border, "border_width": 0.2})

    objs.append({"id": "page_num", "obj_type": "TEXT", "semantic": "PAGE_NUMBER", "value": "1 / 365",
                 "x": 0, "y": h_mm - 6, "w": w_mm, "h": 4, "font_name": "Helvetica", "font_size": 4,
                 "color": text, "align": "center"})

    return objs


def _build_2dpp_substitutions(page_index, base_date):
    days_pt = ["SEGUNDA", "TERCA", "QUARTA", "QUINTA", "SEXTA", "SABADO", "DOMINGO"]
    months_pt = ["janeiro", "fevereiro", "marco", "abril", "maio", "junho",
                 "julho", "agosto", "setembro", "outubro", "novembro", "dezembro"]

    day_a = base_date + datetime.timedelta(days=page_index * 2)
    day_b = base_date + datetime.timedelta(days=page_index * 2 + 1)

    return {
        "TERCA": days_pt[day_a.weekday()],
        "15": str(day_a.day),
        "julho 2026": f"{months_pt[day_a.month - 1]} {day_a.year}",
        "QUARTA": days_pt[day_b.weekday()],
        "16": str(day_b.day),
        "agosto 2026": f"{months_pt[day_b.month - 1]} {day_b.year}",
        "1 / 365": f"{page_index * 2 + 1} / {page_index * 2 + 2}",
    }


def _build_1dpp_substitutions(page_index, base_date):
    days_pt = ["SEGUNDA", "TERCA", "QUARTA", "QUINTA", "SEXTA", "SABADO", "DOMINGO"]
    months_pt = ["janeiro", "fevereiro", "marco", "abril", "maio", "junho",
                 "julho", "agosto", "setembro", "outubro", "novembro", "dezembro"]

    d = base_date + datetime.timedelta(days=page_index)
    return {
        "TERCA": days_pt[d.weekday()],
        "15": str(d.day),
        "julho 2026": f"{months_pt[d.month - 1]} {d.year}",
        "1 / 365": f"{page_index + 1} / 365",
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

    return {
        "TERCA": day_name,
        "15": day_num,
        "julho 2026": month_year,
        "1 / 365": f"{page_index + 1} / 365",
    }


def _get_substitutions_for_2dpp(page_index, base_date, lang="pt"):
    days_pt = ["SEGUNDA", "TERCA", "QUARTA", "QUINTA", "SEXTA", "SABADO", "DOMINGO"]
    months_pt = ["janeiro", "fevereiro", "marco", "abril", "maio", "junho",
                 "julho", "agosto", "setembro", "outubro", "novembro", "dezembro"]

    day_a = base_date + datetime.timedelta(days=page_index * 2)
    day_b = base_date + datetime.timedelta(days=page_index * 2 + 1)

    subs = {}
    subs["TERCA"] = days_pt[day_a.weekday()]
    subs["15"] = str(day_a.day)
    subs["julho 2026"] = f"{months_pt[day_a.month - 1]} {day_a.year}"
    subs["1 / 365"] = f"{page_index * 2 + 1} / 365"

    subs["QUARTA"] = days_pt[day_b.weekday()]
    subs["16"] = str(day_b.day)
    subs["agosto 2026"] = f"{months_pt[day_b.month - 1]} {day_b.year}"
    subs["2 / 365"] = f"{page_index * 2 + 2} / 365"

    return subs


# ── Main generator ──────────────────────────────────────────────────────

def gerar_pdf_blueprint(blueprint_dict, formato="A5", num_pages=7, base_date=None):
    bp = blueprint_dict
    palette = _get_palette(bp)
    editable = bp.get("editable_objects", [])

    w, h = PAGE_SIZES.get(formato.upper(), PAGE_SIZES["A5"])

    if base_date is None:
        base_date = datetime.date(2026, 1, 1)

    page_type = bp.get("page_type", "1dpp")

    if not editable:
        if page_type == "2dpp":
            editable = _build_2dpp_objects(palette)
        else:
            editable = _build_1dpp_objects(palette)

    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=(w, h))
    pdf.setPageCompression(0)

    _draw_dados_pessoais(pdf, w, h, palette)
    pdf.showPage()

    _draw_calendario_anual(pdf, w, h, palette, base_date)
    pdf.showPage()

    _draw_planejamento_anual(pdf, w, h, palette, base_date)
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
            _draw_object(pdf, obj, h, palette, subs)

    pdf.save()
    buffer.seek(0)
    return buffer

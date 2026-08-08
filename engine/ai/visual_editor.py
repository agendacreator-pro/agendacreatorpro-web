"""
Visual Layout Editor backend.

Renders a user-built page model (JSON layout) into a faithful PDF using
real page coordinates (mm). The user positions every element in the visual
editor; the renderer only repeats the model for every day, replacing the
dynamic tokens ({DIA}, {DATA}, {MES}, {ANO}, {NOME}, {FRASE}, {VERSICULO}...).
"""
import base64
import copy
import datetime
import io
import math
import os
import re
import sys
from io import BytesIO

_ENGINE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_AI_DIR = os.path.dirname(os.path.abspath(__file__))
_DATA_DIR = os.path.join(_ENGINE_DIR, "data")
for _p in (_ENGINE_DIR, _AI_DIR, _DATA_DIR):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
from reportlab.lib.colors import HexColor

from blueprint_generator import PAGE_SIZES, _pc, _fn, _resolve_color

try:
    from fonts import resolve_font
except Exception:  # pragma: no cover
    resolve_font = None


# ── Layout schema ───────────────────────────────────────────────────────

DEFAULT_LAYOUT = {
    "version": 1,
    "formato": "A5",
    "page_type": "1dpp",
    "background": {
        "type": "color",
        "color": "#FFFFFF",
        "image": None,
        "visible": True,
        "include_in_pdf": True,
    },
    "elements": [],
}

ELEMENT_TYPES = {
    "text", "image", "line", "rect", "rounded_rect", "circle",
    "ellipse", "table", "grid", "calendar", "decoration",
}

TOKEN_PATTERN = re.compile(r"\{([A-Z0-9_]+)\}")


def _num(v, default=0.0):
    try:
        return float(v)
    except (TypeError, ValueError):
        return default


def _clamp(v, lo, hi):
    return max(lo, min(hi, v))


def sanitize_layout(layout, w_mm=None, h_mm=None):
    """Validate and clamp a user layout to the page bounds."""
    if not isinstance(layout, dict):
        layout = {}
    formato = str(layout.get("formato", "A5")).upper()
    if formato not in PAGE_SIZES:
        formato = "A5"
    pw, ph = PAGE_SIZES[formato]
    if w_mm is None:
        w_mm = pw / mm
    if h_mm is None:
        h_mm = ph / mm

    page_type = str(layout.get("page_type", "1dpp"))
    if page_type not in ("1dpp", "2dpp"):
        page_type = "1dpp"

    bg = layout.get("background") or {}
    background = {
        "type": "color" if bg.get("type") != "image" else "image",
        "color": bg.get("color") or "#FFFFFF",
        "image": bg.get("image") or None,
        "visible": bool(bg.get("visible", True)),
        "include_in_pdf": bool(bg.get("include_in_pdf", True)),
    }

    elements = []
    seen = set()
    raw = layout.get("elements") or []
    if not isinstance(raw, list):
        raw = []
    for el in raw:
        if not isinstance(el, dict):
            continue
        e = dict(el)
        etype = str(e.get("type", "text")).lower()
        if etype not in ELEMENT_TYPES:
            etype = "text"
        e["type"] = etype

        e["x"] = round(_clamp(_num(e.get("x")), -50.0, w_mm + 50.0), 2)
        e["y"] = round(_clamp(_num(e.get("y")), -50.0, h_mm + 50.0), 2)
        e["w"] = round(_clamp(_num(e.get("w"), 5.0), 0.5, 600.0), 2)
        e["h"] = round(_clamp(_num(e.get("h"), 5.0), 0.5, 600.0), 2)
        e["rotation"] = round(_num(e.get("rotation")), 2) % 360
        e["opacity"] = round(_clamp(_num(e.get("opacity"), 1.0), 0.0, 1.0), 3)
        e["layer"] = _num(e.get("layer"), 0)
        e["locked"] = bool(e.get("locked"))

        if etype == "text":
            e["text"] = str(e.get("text", "") or "")
            e["font"] = e.get("font") or "Helvetica"
            e["font_size"] = _clamp(_num(e.get("font_size"), 12.0), 1.0, 200.0)
            e["bold"] = bool(e.get("bold"))
            e["italic"] = bool(e.get("italic"))
            e["color"] = e.get("color") or "#333333"
            e["align"] = e.get("align") in ("center", "right") and e["align"] or "left"
            e["line_height"] = _clamp(_num(e.get("line_height"), 1.2), 0.6, 3.0)
            e["dynamic"] = bool(e.get("dynamic"))

        elif etype in ("image", "calendar", "decoration"):
            if etype == "image":
                e["image"] = e.get("image") or None
            elif etype == "calendar":
                e["show_header"] = bool(e.get("show_header", True))
            else:
                e["shape"] = e.get("shape") or "circle"
            e.setdefault("color", "#333333")

        elif etype == "line":
            e["color"] = e.get("color") or "#999999"
            e["border_width"] = _clamp(_num(e.get("border_width"), 0.5), 0.05, 12.0)
            e["dashed"] = e.get("dashed") or "none"

        else:  # shapes / table / grid
            e["fill"] = e.get("fill") or "#FFFFFF"
            e["border_color"] = e.get("border_color") or "#CCCCCC"
            e["border_width"] = _clamp(_num(e.get("border_width"), 0.5), 0.05, 12.0)
            e["radius"] = _clamp(_num(e.get("radius")), 0.0, 40.0)
            e["dashed"] = e.get("dashed") or "none"
            if etype in ("table", "grid"):
                e["cols"] = int(_clamp(_num(e.get("cols"), 7), 1, 60))
                e["rows"] = int(_clamp(_num(e.get("rows"), 6), 1, 60))

        eid = str(e.get("id") or "")
        if not eid:
            eid = "el_%d" % len(elements)
        base = eid
        i = 1
        while eid in seen:
            eid = "%s_%d" % (base, i)
            i += 1
        seen.add(eid)
        e["id"] = eid
        elements.append(e)

    elements.sort(key=lambda o: _num(o.get("layer")))

    return {
        "version": 1,
        "formato": formato,
        "page_type": page_type,
        "background": background,
        "elements": elements,
    }


# ── Dynamic data ────────────────────────────────────────────────────────

def _day_of_year(d):
    return (d - datetime.date(d.year, 1, 1)).days + 1


def build_substitutions(d, page_index, total_pages, nome="", extra=None, lang="pt"):
    """Tokens replaced on every daily page."""
    days = ["SEGUNDA", "TERCA", "QUARTA", "QUINTA", "SEXTA", "SABADO", "DOMINGO"]
    days_long = ["SEGUNDA-FEIRA", "TERCA-FEIRA", "QUARTA-FEIRA",
                 "QUINTA-FEIRA", "SEXTA-FEIRA", "SABADO", "DOMINGO"]
    months = ["janeiro", "fevereiro", "marco", "abril", "maio", "junho",
              "julho", "agosto", "setembro", "outubro", "novembro", "dezembro"]

    doy = _day_of_year(d)
    frase = ""
    versiculo = ""
    ref = ""
    try:
        from data.frases_prosperidade import obter_frase
        frase = obter_frase(doy, idioma=lang)
    except Exception:
        try:
            from frases_prosperidade import obter_frase
            frase = obter_frase(doy, idioma=lang)
        except Exception:
            pass
    try:
        from data.versiculos import obter_versiculo
        v = obter_versiculo(doy, idioma=lang)
        versiculo = v.get("texto", "")
        ref = v.get("referencia", "")
    except Exception:
        try:
            from versiculos import obter_versiculo
            v = obter_versiculo(doy, idioma=lang)
            versiculo = v.get("texto", "")
            ref = v.get("referencia", "")
        except Exception:
            pass

    mes_num = str(d.month).zfill(2)
    subs = {
        "DIA": str(d.day),
        "DIA_NUM": str(d.day).zfill(2),
        "DATA": "%02d/%02d/%d" % (d.day, d.month, d.year),
        "DATA_EXTENSO": "%d de %s de %d" % (d.day, months[d.month - 1], d.year),
        "DIA_SEMANA": days[d.weekday()],
        "DIA_SEMANA_EXTENSO": days_long[d.weekday()],
        "MES": months[d.month - 1],
        "MES_CAP": months[d.month - 1].capitalize(),
        "MES_NUM": mes_num,
        "ANO": str(d.year),
        "NOME": nome or "",
        "FRASE": frase,
        "VERSICULO": versiculo,
        "REFERENCIA": ref,
        "PAGINA": "%d / %d" % (page_index + 1, total_pages),
        "ANO_CAL": "%d" % d.year,
    }
    if isinstance(extra, dict):
        for k, v in extra.items():
            subs[str(k).upper()] = str(v or "")
    return subs


def _substitute_text(text, subs):
    def repl(m):
        key = m.group(1)
        return subs.get(key, m.group(0))
    return TOKEN_PATTERN.sub(repl, text)


# ── Drawing helpers ─────────────────────────────────────────────────────

def _resolve(c, palette):
    if not c:
        return None
    if c.startswith("#"):
        return c
    return palette.get(c, c)


def _set_dash(pdf, style, width):
    if style in ("dashed", "dash"):
        pdf.setDash(_clamp(width * 2.0, 1.0, 20.0), _clamp(width * 2.0, 1.0, 20.0))
    elif style in ("dotted", "dot"):
        pdf.setDash(0.5, _clamp(width * 3.0, 2.0, 30.0))
    else:
        pdf.setDash()


def _wrap_text(text, font_name, size, max_w_pt):
    lines = []
    for raw in text.split("\n"):
        line = ""
        for word in raw.split(" "):
            trial = (line + " " + word).strip() if line else word
            if _sw(font_name, trial, size) <= max_w_pt or not line:
                line = trial
            else:
                lines.append(line)
                line = word
        lines.append(line)
    return lines


def _sw(font_name, text, size):
    from reportlab.pdfbase.pdfmetrics import stringWidth
    try:
        return stringWidth(text, font_name, size)
    except Exception:
        return len(text) * size * 0.6


def _draw_text(pdf, el, x, y, w, h, font_name, palette, subs):
    text = _substitute_text(el.get("text", ""), subs)
    if not text.strip():
        return
    size = _num(el.get("font_size"), 12)
    align = el.get("align", "left")
    lh = _num(el.get("line_height"), 1.2)
    color = _pc(_resolve(el.get("color"), palette) or "#000000")

    bold = bool(el.get("bold"))
    italic = bool(el.get("italic"))
    try:
        fn = _fn(el.get("font") or "Helvetica", bold, italic, family=font_name)
    except Exception:
        fn = "Helvetica"
    lines = _wrap_text(text, fn, size, w)
    line_h = size * 1.25 * lh
    total_h = len(lines) * line_h
    top = y + h
    start = top - line_h
    if total_h < h:
        start = top - (h - total_h) / 2 - line_h

    pdf.setFillColor(color)
    for i, lt in enumerate(lines):
        ly = start - i * line_h
        if ly < y - line_h:
            break
        if align == "center":
            pdf.drawCentredString(x + w / 2, ly, lt)
        elif align == "right":
            pdf.drawRightString(x + w, ly, lt)
        else:
            pdf.drawString(x + 2 * mm, ly, lt)


def _draw_calendar(pdf, el, x, y, w, h, font_name, palette, subs, d):
    size = 7
    color = _pc(_resolve(el.get("color") or "#333333", palette) or "#333333")
    fn = _fn(el.get("font") or "Helvetica", False, False, family=font_name)

    year, month = d.year, d.month
    first = datetime.date(year, month, 1)
    start_wd = (first.weekday() + 1) % 7  # Sunday=0
    import calendar as _cal
    n_days = _cal.monthrange(year, month)[1]

    if el.get("show_header", True):
        pdf.setFont(fn, size + 1)
        pdf.setFillColor(color)
        pdf.drawCentredString(x + w / 2, y + h - size * 1.4, _substitute_text(el.get("text") or "%s/%d" % (month, year), subs))
        top = y + h - size * 2.6
        body_h = top - y
    else:
        body_h = h
        top = y + h

    cols = 7
    rows = max(1, math.ceil((start_wd + n_days) / 7))
    cw = w / cols
    ch = body_h / max(rows, 1)

    pdf.setFont(fn, size * 0.8)
    pdf.setFillColor(color)
    pdf.setStrokeColor(color)
    pdf.setLineWidth(0.2)
    for c in range(cols):
        pdf.drawCentredString(x + c * cw + cw / 2, top - ch * 0.7,
                              ["D", "S", "T", "Q", "Q", "S", "S"][c])
    pdf.setFont(fn, size)
    for i in range(n_days):
        r = (start_wd + i) // cols
        c = (start_wd + i) % cols
        if r >= rows:
            break
        cx = x + c * cw + cw / 2
        cy = top - (r + 1) * ch + ch * 0.35
        if (i + 1) == d.day:
            pdf.setFillColor(_pc(_resolve(el.get("fill") or "#FFFFFF", palette) or "#FFFFFF"))
            pdf.circle(cx, cy, ch * 0.42, fill=1, stroke=0)
            pdf.setFillColor(_pc(_resolve(el.get("border_color") or "#CCCCCC", palette) or "#CCCCCC"))
            pdf.circle(cx, cy, ch * 0.42, fill=0, stroke=1)
            pdf.setFillColor(color)
        pdf.drawCentredString(cx, cy - size * 0.35, str(i + 1))


def _draw_element(pdf, el, page_h, palette, subs, font_name=None, d=None):
    etype = el.get("type", "text")
    x_mm = _num(el.get("x"))
    y_mm = _num(el.get("y"))
    w_mm = _num(el.get("w"), 5)
    h_mm = _num(el.get("h"), 5)
    rot = _num(el.get("rotation")) % 360
    opacity = _num(el.get("opacity"), 1.0)

    if opacity <= 0:
        return

    if rot != 0:
        pdf.saveState()
        cx = (x_mm + w_mm / 2) * mm
        cy = page_h - (y_mm + h_mm / 2) * mm
        pdf.translate(cx, cy)
        pdf.rotate(-rot)
        x, y = -w_mm * mm / 2, -h_mm * mm / 2
        w, h = w_mm * mm, h_mm * mm
    else:
        x = x_mm * mm
        y = page_h - (y_mm * mm) - (h_mm * mm)
        w = w_mm * mm
        h = h_mm * mm

    color = _pc(_resolve(el.get("color"), palette) or "#000000")
    fill = _pc(_resolve(el.get("fill"), palette) or "#FFFFFF") if el.get("fill") else None
    bc = _pc(_resolve(el.get("border_color"), palette) or "#CCCCCC") if el.get("border_color") else color
    bw = _num(el.get("border_width"), 0.5)

    try:
        if etype == "text":
            _draw_text(pdf, el, x, y, w, h, font_name, palette, subs)

        elif etype == "image":
            img = el.get("image")
            if not img:
                return
            try:
                b64 = img.split(",", 1)[-1] if img.startswith("data:") else img
                data = base64.b64decode(b64)
                from reportlab.lib.utils import ImageReader
                ir = ImageReader(BytesIO(data))
                pdf.drawImage(ir, x, y, w, h, preserveAspectRatio=False)
            except Exception:
                pass

        elif etype == "line":
            pdf.setStrokeColor(color)
            pdf.setLineWidth(bw)
            _set_dash(pdf, el.get("dashed") or "none", bw)
            if _num(el.get("vertical")):
                pdf.line(x + w / 2, y, x + w / 2, y + h)
            else:
                pdf.line(x, y + h / 2, x + w, y + h / 2)
            pdf.setDash()

        elif etype in ("rect", "rounded_rect"):
            radius = _num(el.get("radius"))
            if fill:
                pdf.setFillColor(fill)
            pdf.setStrokeColor(bc)
            pdf.setLineWidth(bw)
            _set_dash(pdf, el.get("dashed") or "none", bw)
            if etype == "rounded_rect" or radius > 0:
                pdf.roundRect(x, y, w, h, max(radius, 2) * mm, fill=1 if fill else 0, stroke=1)
            else:
                pdf.rect(x, y, w, h, fill=1 if fill else 0, stroke=1)
            pdf.setDash()

        elif etype in ("circle", "ellipse"):
            if fill:
                pdf.setFillColor(fill)
            pdf.setStrokeColor(bc)
            pdf.setLineWidth(bw)
            _set_dash(pdf, el.get("dashed") or "none", bw)
            if etype == "circle":
                pdf.circle(x + w / 2, y + h / 2, min(w, h) / 2, fill=1 if fill else 0, stroke=1)
            else:
                pdf.ellipse(x, y, x + w, y + h, fill=1 if fill else 0, stroke=1)
            pdf.setDash()

        elif etype in ("table", "grid"):
            if fill:
                pdf.setFillColor(fill)
                pdf.rect(x, y, w, h, fill=1, stroke=0)
            pdf.setStrokeColor(bc)
            pdf.setLineWidth(bw)
            _set_dash(pdf, el.get("dashed") or "none", bw)
            cols = int(_num(el.get("cols"), 7))
            rows = int(_num(el.get("rows"), 6))
            for c in range(cols + 1):
                lx = x + w * c / cols
                pdf.line(lx, y, lx, y + h)
            for r in range(rows + 1):
                ly = y + h * r / rows
                pdf.line(x, ly, x + w, ly)
            pdf.setDash()

        elif etype == "calendar":
            if d is not None:
                _draw_calendar(pdf, el, x, y, w, h, font_name, palette, subs, d)
            else:
                if fill:
                    pdf.setFillColor(fill)
                    pdf.rect(x, y, w, h, fill=1, stroke=0)

        elif etype == "decoration":
            shape = el.get("shape") or "circle"
            cx = x + w / 2
            cy = y + h / 2
            r = min(w, h) / 2.5
            pdf.setFillColor(color)
            pdf.setStrokeColor(color)
            if shape == "heart":
                pdf.circle(cx - r * 0.3, cy + r * 0.15, r * 0.35, fill=1, stroke=0)
                pdf.circle(cx + r * 0.3, cy + r * 0.15, r * 0.35, fill=1, stroke=0)
                path = pdf.beginPath()
                path.moveTo(cx - r * 0.6, cy + r * 0.2)
                path.lineTo(cx, cy - r * 0.6)
                path.lineTo(cx + r * 0.6, cy + r * 0.2)
                path.close()
                pdf.drawPath(path, fill=1, stroke=0)
            elif shape == "star":
                path = pdf.beginPath()
                for i in range(10):
                    ang = math.pi / 2 + i * math.pi / 5
                    rad = r if i % 2 == 0 else r * 0.4
                    px = cx + rad * math.cos(ang)
                    py = cy + rad * math.sin(ang)
                    if i == 0:
                        path.moveTo(px, py)
                    else:
                        path.lineTo(px, py)
                path.close()
                pdf.drawPath(path, fill=1, stroke=0)
            elif shape == "circle":
                pdf.circle(cx, cy, r, fill=1, stroke=0)
            else:
                pdf.circle(cx, cy, r, fill=1, stroke=0)
    finally:
        if rot != 0:
            pdf.restoreState()


# ── PDF generation ──────────────────────────────────────────────────────

def _decode_image_data(img):
    if not img:
        return None
    try:
        if isinstance(img, str) and img.startswith("data:"):
            img = img.split(",", 1)[-1]
        return base64.b64decode(img)
    except Exception:
        return None


def _draw_background(pdf, layout, w, h, w_mm, h_mm):
    bg = layout.get("background") or {}
    color = bg.get("color") or "#FFFFFF"
    pdf.setFillColor(_pc(color))
    pdf.rect(0, 0, w, h, fill=1, stroke=0)
    if bg.get("type") == "image" and bg.get("include_in_pdf") and bg.get("image"):
        data = _decode_image_data(bg.get("image"))
        if data:
            try:
                from PIL import Image as PILImage
                from reportlab.lib.utils import ImageReader
                img = PILImage.open(BytesIO(data)).convert("RGB")
                iw, ih = img.size
                scale = min(w / iw, h / ih)
                dw, dh = iw * scale, ih * scale
                dx, dy = (w - dw) / 2, (h - dh) / 2
                pdf.drawImage(ImageReader(img), dx, dy, dw, dh)
            except Exception:
                pass


def _daily_subs_for_slot(page_type, page_index, base_date, total_days, nome, extra, lang, slot):
    d = base_date + datetime.timedelta(days=page_index * (2 if page_type == "2dpp" else 1) + slot)
    return build_substitutions(d, page_index, total_days, nome=nome, extra=extra, lang=lang)


def gerar_pdf_editor(layout, formato="A5", num_days=365, base_date=None, nome="",
                     extra=None, font=None, page_type=None):
    """Generate the full agenda PDF from a visual-editor layout."""
    pw, ph = PAGE_SIZES.get(str(formato).upper(), PAGE_SIZES["A5"])
    w, h = pw, ph
    w_mm = w / mm
    h_mm = h / mm

    layout = sanitize_layout(layout, w_mm, h_mm)
    pt = page_type or layout.get("page_type") or "1dpp"
    if pt not in ("1dpp", "2dpp"):
        pt = "1dpp"

    if base_date is None:
        base_date = datetime.date(2026, 1, 1)

    if pt == "2dpp":
        pages = max(1, math.ceil(num_days / 2))
    else:
        pages = max(1, num_days)

    palette = {"accent": "#4A90D9", "text": "#333333", "primary": "#333333",
               "border": "#CCCCCC", "highlight": "#EEF5FF",
               "secondary": "#A0A0A0", "background": "#FFFFFF"}

    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=(w, h))
    pdf.setPageCompression(0)

    for p in range(pages):
        if p > 0:
            pdf.showPage()
        _draw_background(pdf, layout, w, h, w_mm, h_mm)

        for el in layout.get("elements", []):
            if not el.get("visible", True):
                continue
            if el.get("type") == "text":
                el = dict(el)
                if pt == "2dpp":
                    slot = 1 if (_num(el.get("y")) + _num(el.get("h"), 5) / 2) > h_mm / 2 else 0
                    subs = _daily_subs_for_slot(pt, p, base_date, pages, nome, extra, "pt", slot)
                else:
                    subs = _daily_subs_for_slot(pt, p, base_date, num_days, nome, extra, "pt", 0)
            else:
                subs = build_substitutions(base_date, p, pages, nome=nome, extra=extra)
            d = base_date + datetime.timedelta(days=p * (2 if pt == "2dpp" else 1))
            _draw_element(pdf, el, h, palette, subs, font_name=font, d=d)

    pdf.save()
    buffer.seek(0)
    return buffer


def gerar_preview_editor(layout, formato="A5", num_days=365, base_date=None, nome="",
                         extra=None, font=None, page_type=None):
    """Generate a short PDF: page 1, a middle page, and the last page."""
    pw, ph = PAGE_SIZES.get(str(formato).upper(), PAGE_SIZES["A5"])
    w, h = pw, ph
    w_mm = w / mm
    h_mm = h / mm
    layout = sanitize_layout(layout, w_mm, h_mm)
    pt = page_type or layout.get("page_type") or "1dpp"
    if pt not in ("1dpp", "2dpp"):
        pt = "1dpp"
    if base_date is None:
        base_date = datetime.date(2026, 1, 1)
    pages = max(1, math.ceil(num_days / 2)) if pt == "2dpp" else max(1, num_days)

    samples = [0]
    mid = pages // 2
    if mid not in samples:
        samples.append(mid)
    last = pages - 1
    if last not in samples:
        samples.append(last)
    samples.sort()

    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=(w, h))
    pdf.setPageCompression(0)
    palette = {"accent": "#4A90D9", "text": "#333333", "primary": "#333333",
               "border": "#CCCCCC", "highlight": "#EEF5FF",
               "secondary": "#A0A0A0", "background": "#FFFFFF"}

    for idx, p in enumerate(samples):
        if idx > 0:
            pdf.showPage()
        _draw_background(pdf, layout, w, h, w_mm, h_mm)
        for el in layout.get("elements", []):
            if not el.get("visible", True):
                continue
            if el.get("type") == "text":
                el = dict(el)
                if pt == "2dpp":
                    slot = 1 if (_num(el.get("y")) + _num(el.get("h"), 5) / 2) > h_mm / 2 else 0
                    subs = _daily_subs_for_slot(pt, p, base_date, pages, nome, extra, "pt", slot)
                else:
                    subs = _daily_subs_for_slot(pt, p, base_date, num_days, nome, extra, "pt", 0)
            else:
                subs = build_substitutions(base_date, p, pages, nome=nome, extra=extra)
            d = base_date + datetime.timedelta(days=p * (2 if pt == "2dpp" else 1))
            _draw_element(pdf, el, h, palette, subs, font_name=font, d=d)

    pdf.save()
    buffer.seek(0)
    return buffer


def render_page_png(layout, formato="A5", num_days=365, base_date=None, page_index=0,
                    nome="", extra=None, font=None, page_type=None, dpi=60):
    """Render a single page as PNG (for thumbnails/preview in the browser)."""
    try:
        import fitz
    except Exception:
        try:
            import pymupdf as fitz
        except Exception:
            return None
    pdf_bytes = gerar_preview_editor(layout, formato=formato, num_days=num_days,
                                     base_date=base_date, nome=nome, extra=extra,
                                     font=font, page_type=page_type)
    doc = fitz.open("pdf", pdf_bytes.getvalue())
    samples = doc.page_count
    idx = min(max(page_index, 0), samples - 1)
    pix = doc[idx].get_pixmap(dpi=dpi)
    import base64 as _b64
    return _b64.b64encode(pix.tobytes("png")).decode()

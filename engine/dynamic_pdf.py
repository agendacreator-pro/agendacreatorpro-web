from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
from reportlab.lib.colors import HexColor
import copy


def _pc(hex_str, fallback="#000000"):
    if not hex_str:
        return HexColor(fallback)
    try:
        return HexColor(hex_str)
    except Exception:
        return HexColor(fallback)


def _fn(name, bold=False):
    safe = (name or "Helvetica").replace(" ", "-").replace("_", "-")
    valid = {
        "Helvetica", "Helvetica-Bold", "Helvetica-Oblique", "Helvetica-BoldOblique",
        "Times-Roman", "Times-Bold", "Times-Italic", "Times-BoldItalic",
        "Courier", "Courier-Bold", "Courier-Oblique", "Courier-BoldOblique",
    }
    return safe if safe in valid else ("Helvetica-Bold" if bold else "Helvetica")


PAGE_SIZES = {
    "A5": (148 * mm, 210 * mm),
    "A4": (210 * mm, 297 * mm),
    "QUADRADO": (150 * mm, 150 * mm),
}

SECTION_TEXT_MAP = {
    "dados_pessoais": {
        "fields": [
            ("Nome:", ""),
            ("E-mail:", ""),
            ("Telefone:", ""),
            ("Endereco:", ""),
            ("Nascimento:", ""),
            ("Observacoes:", ""),
        ]
    },
    "planejamento": {"title": "PLANEJAMENTO SEMANAL"},
    "semanal": {"title": "AGENDA SEMANAL"},
    "mensal": {"title": "AGENDA MENSAL"},
    "calendario": {"title": "CALENDARIO 2026"},
    "metas": {"title": "METAS E OBJETIVOS"},
    "checklist": {"title": "CHECKLIST"},
    "notas": {"title": "ANOTACOES"},
}


def gerar_pdf_da_analise(analysis_dict, formato="A5"):
    pa = analysis_dict.get("page_analysis", analysis_dict)
    orig_elements = pa.get("elements", [])
    colors = pa.get("colors", [])
    page_type = pa.get("page_type", "1dpp")
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
        new_els = _replicate_pattern(orig_elements, sec, accent, w, h)
        _draw(pdf, new_els, w, h)

    pdf.save()
    buffer.seek(0)
    return buffer


def _find_header_elements(elements):
    headers = []
    for el in elements:
        text = (el.get("text") or "").strip()
        bold = bool(el.get("bold"))
        fs = float(el.get("font_size", 0) or 0)
        y = float(el.get("y", 0) or 0)
        if text and bold and fs >= 6 and y < 40:
            headers.append(el)
    return headers


def _find_text_elements(elements):
    return [el for el in elements if el.get("type") == "text" and (el.get("text") or "").strip()]


def _find_structure_elements(elements):
    return [el for el in elements if el.get("type") in ("line", "rect", "box", "grid")]


def _replicate_pattern(orig_elements, section_type, accent, page_w, page_h):
    new_elements = []

    section_info = SECTION_TEXT_MAP.get(section_type, {"title": section_type.upper().replace("_", " ")})
    title = section_info.get("title", section_type.upper().replace("_", " "))

    for el in orig_elements:
        new_el = copy.deepcopy(el)
        etype = new_el.get("type", "")
        text = (new_el.get("text") or "").strip()
        bold = bool(new_el.get("bold"))
        fs = float(new_el.get("font_size", 0) or 0)
        y = float(new_el.get("y", 0) or 0)

        if etype == "text" and text:
            if bold and fs >= 6 and y < 40:
                new_el["text"] = title
                new_el["color"] = accent
            elif not bold and section_type == "dados_pessoais":
                new_el["text"] = ""
            elif not bold and section_type not in ("dados_pessoais",):
                new_el["text"] = ""

        new_elements.append(new_el)

    if section_type == "dados_pessoais":
        fields = ["Nome:", "E-mail:", "Telefone:", "Endereco:", "Nascimento:", "Observacoes:"]
        line_els = [e for e in orig_elements if e.get("type") == "line"]
        text_els = [e for e in orig_elements if e.get("type") == "text" and not bool(e.get("bold"))]
        text_els_sorted = sorted(text_els, key=lambda e: float(e.get("y", 999) or 999))
        data_els = [e for e in text_els_sorted if float(e.get("y", 0) or 0) >= 25]

        spacing = 16
        for i, f in enumerate(fields):
            fy = 28 + i * spacing
            ref = data_els[i] if i < len(data_els) else (data_els[0] if data_els else {})
            new_elements.append({
                "type": "text", "x": ref.get("x", 15), "y": fy, "w": 35, "h": 8,
                "text": f, "font_name": "Helvetica", "font_size": 7,
                "color": "#333333",
            })
            new_elements.append({
                "type": "line", "x": float(ref.get("x", 15) or 15) + 35, "y": fy + 6,
                "w": 83, "h": 0,
                "color": "#E0E0E0", "border_width": 0.3,
            })

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
        fn = _fn(el.get("font_name"), bold)
        fs = float(el.get("font_size", 10) or 10)
        align = el.get("align", "left")

        pdf.setFillColor(color)

        if etype in ("rect", "box"):
            if bg:
                pdf.setFillColor(bg)
                pdf.rect(x, y_pdf, w, h, fill=1, stroke=0)
            if el.get("border"):
                pdf.setStrokeColor(bc)
                pdf.setLineWidth(bw)
                pdf.rect(x, y_pdf, w, h, fill=0, stroke=1)

        elif etype == "line":
            pdf.setStrokeColor(color)
            pdf.setLineWidth(bw)
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
            pdf.setFont(fn, fs)
            lh = max(fs + 2, 10) * mm
            for i, lt in enumerate(text.split("\n")):
                ly = y_pdf + h - (i + 1) * lh
                if ly < y_pdf:
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
            pdf.setFillColor(color)
            pdf.circle(x + w / 2, y_pdf + h / 2, min(w, h) / 3, fill=1, stroke=0)

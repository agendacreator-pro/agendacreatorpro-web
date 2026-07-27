"""
Consistency Pass.

Compare the reconstructed layout with the original image.
Scan in 64x64 pixel blocks, calculate structural similarity.
If difference > ~5%, reconstruct that region.
Repeat until high similarity or max iterations reached.
"""
import io
import math
from typing import List, Tuple, Dict, Any, Optional


def consistency_pass(blueprint, original_image_bytes, max_iterations=3, threshold=0.05):
    try:
        from PIL import Image
    except ImportError:
        return blueprint

    try:
        orig_img = Image.open(io.BytesIO(original_image_bytes))
    except Exception:
        return blueprint

    orig_rgb = orig_img.convert("RGB")
    orig_w, orig_h = orig_rgb.size

    for iteration in range(max_iterations):
        preview_img = _render_blueprint_to_image(blueprint, orig_w, orig_h)
        if preview_img is None:
            break

        diff_blocks = _compare_images(preview_img, orig_rgb, block_size=64, threshold=threshold)

        if not diff_blocks:
            break

        blueprint = _fix_blocks(blueprint, diff_blocks, orig_w, orig_h)

    return blueprint


def _render_blueprint_to_image(blueprint, target_w, target_h):
    try:
        from PIL import Image, ImageDraw
    except ImportError:
        return None

    try:
        from ai.blueprint_generator import gerar_pdf_blueprint
        buffer = gerar_pdf_blueprint(blueprint, formato="A5", num_pages=1)
    except Exception:
        return None

    try:
        from reportlab.graphics import renderPM
        from reportlab.lib.units import mm
        from reportlab.pdfgen import canvas as pdf_canvas

        pdf_bytes = buffer.getvalue()
        pdf_buf = io.BytesIO(pdf_bytes)

        try:
            import fitz
            doc = fitz.open(stream=pdf_bytes, filetype="pdf")
            page = doc[0]
            mat = fitz.Matrix(2, 2)
            pix = page.get_pixmap(matrix=mat)
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            return img.resize((target_w, target_h), Image.LANCZOS)
        except ImportError:
            pass

        try:
            from pdf2image import convert_from_bytes
            images = convert_from_bytes(pdf_bytes, first_page=1, last_page=1,
                                        dpi=150, fmt="png")
            if images:
                return images[0].resize((target_w, target_h), Image.LANCZOS)
        except ImportError:
            pass

        return _render_blueprint_fallback(blueprint, target_w, target_h)

    except Exception:
        return _render_blueprint_fallback(blueprint, target_w, target_h)


def _render_blueprint_fallback(blueprint, target_w, target_h):
    try:
        from PIL import Image, ImageDraw
    except ImportError:
        return None

    img = Image.new("RGB", (target_w, target_h), (255, 255, 255))
    draw = ImageDraw.Draw(img)

    objects = blueprint.get("editable_objects", [])
    palette = blueprint.get("palette", {})

    page_w_mm = 148
    page_h_mm = 210
    scale_x = target_w / page_w_mm
    scale_y = target_h / page_h_mm

    for obj in objects:
        otype = obj.get("obj_type", "rect")
        x = float(obj.get("x", 0) or 0) * scale_x
        y = float(obj.get("y", 0) or 0) * scale_y
        w = float(obj.get("w", 0) or 0) * scale_x
        h = float(obj.get("h", 0) or 0) * scale_y

        color_ref = obj.get("color", obj.get("bg_color", "#000000"))
        color = _resolve_color(color_ref, palette)

        try:
            r = int(color[1:3], 16)
            g = int(color[3:5], 16)
            b = int(color[5:7], 16)
        except (ValueError, IndexError):
            r, g, b = 0, 0, 0

        if otype in ("RECTANGLE", "ROUNDED_RECTANGLE"):
            draw.rectangle([x, y, x + w, y + h], fill=(r, g, b))
        elif otype == "LINE":
            draw.line([x, y, x + w, y + h], fill=(r, g, b), width=max(1, int(float(obj.get("border_width", 0.5)) * scale_x)))
        elif otype in ("CIRCLE", "CHECKBOX"):
            cx, cy = x + w / 2, y + h / 2
            radius = min(w, h) / 2
            draw.ellipse([cx - radius, cy - radius, cx + radius, cy + radius], fill=(r, g, b))
        elif otype in ("TEXT", "SECTION_TITLE"):
            try:
                draw.rectangle([x, y, x + w, y + h], fill=(r, g, b))
            except Exception:
                pass

    return img


def _compare_images(img1, img2, block_size=64, threshold=0.05):
    w1, h1 = img1.size
    w2, h2 = img2.size
    w = min(w1, w2)
    h = min(h1, h2)

    try:
        small1 = img1.resize((w // 4, h // 4))
        small2 = img2.resize((w // 4, h // 4))
    except Exception:
        return []

    diff_blocks = []
    sw, sh = small1.size
    bw = max(block_size // 4, 16)
    bh = max(block_size // 4, 16)

    for by in range(0, sh, bh):
        for bx in range(0, sw, bw):
            block1_pixels = []
            block2_pixels = []
            for py in range(by, min(by + bh, sh)):
                for px in range(bx, min(bx + bw, sw)):
                    try:
                        p1 = small1.getpixel((px, py))
                        p2 = small2.getpixel((px, py))
                        block1_pixels.append(p1)
                        block2_pixels.append(p2)
                    except Exception:
                        continue

            if not block1_pixels:
                continue

            diff = _block_similarity(block1_pixels, block2_pixels)
            if diff > threshold:
                orig_x = bx * 4
                orig_y = by * 4
                diff_blocks.append({
                    "x": orig_x,
                    "y": orig_y,
                    "w": bw * 4,
                    "h": bh * 4,
                    "diff": diff,
                })

    return diff_blocks


def _block_similarity(pixels1, pixels2):
    if not pixels1 or not pixels2:
        return 0

    total_diff = 0
    for p1, p2 in zip(pixels1, pixels2):
        r1, g1, b1 = p1[0], p1[1], p1[2]
        r2, g2, b2 = p2[0], p2[1], p2[2]
        total_diff += abs(r1 - r2) + abs(g1 - g2) + abs(b1 - b2)

    avg_diff = total_diff / (len(pixels1) * 3 * 255)
    return avg_diff


def _fix_blocks(blueprint, diff_blocks, img_w, img_h):
    objects = blueprint.get("editable_objects", [])
    palette = blueprint.get("palette", {})
    page_w_mm = 148
    page_h_mm = 210
    scale_x = page_w_mm / img_w
    scale_y = page_h_mm / img_h

    sorted_blocks = sorted(diff_blocks, key=lambda b: b["diff"], reverse=True)
    blocks_to_fix = sorted_blocks[:5]

    for block in blocks_to_fix:
        bx_mm = block["x"] * scale_x
        by_mm = block["y"] * scale_y
        bw_mm = block["w"] * scale_x
        bh_mm = block["h"] * scale_y

        existing_in_region = [
            o for o in objects
            if _rects_overlap(
                float(o.get("x", 0)), float(o.get("y", 0)),
                float(o.get("w", 0)), float(o.get("h", 0)),
                bx_mm, by_mm, bw_mm, bh_mm
            )
        ]

        if not existing_in_region:
            objects.append({
                "id": f"consistency_fill_{block['x']}_{block['y']}",
                "obj_type": "RECTANGLE",
                "x": round(bx_mm, 1), "y": round(by_mm, 1),
                "w": round(bw_mm, 1), "h": round(bh_mm, 1),
                "bg_color": "_secondary_",
                "border": False,
            })

    blueprint["editable_objects"] = objects
    return blueprint


def _rects_overlap(x1, y1, w1, h1, x2, y2, w2, h2):
    return not (x1 + w1 < x2 or x2 + w2 < x1 or y1 + h1 < y2 or y2 + h2 < y1)


def _resolve_color(color_ref, palette):
    if not color_ref:
        return "#000000"
    if color_ref.startswith("#"):
        return color_ref

    color_map = {
        "_accent_": palette.get("accent", "#4A90D9"),
        "_primary_": palette.get("primary", "#2D2D2D"),
        "_text_": palette.get("text", "#555555"),
        "_white_": "#FFFFFF",
        "_border_": palette.get("border", "#E0E0E0"),
        "_highlight_": palette.get("highlight", "#F0F6FF"),
        "_secondary_": palette.get("secondary", "#F5F5F5"),
        "_background_": palette.get("background", "#FFFFFF"),
    }
    return color_map.get(color_ref, color_ref)

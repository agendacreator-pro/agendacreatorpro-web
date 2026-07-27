"""
Extract dominant colors from an image using Pillow k-means.
Maps extracted colors to Blueprint palette roles.
"""
import io
from collections import Counter
from typing import Dict, List, Tuple


def _hex(r, g, b):
    return f"#{r:02x}{g:02x}{b:02x}"


def _brightness(r, g, b):
    return 0.299 * r + 0.587 * g + 0.114 * b


def _hue(r, g, b):
    import colorsys
    return colorsys.rgb_to_hsv(r / 255, g / 255, b / 255)[0]


def extract_colors(image_bytes: bytes, num_colors: int = 8) -> Dict[str, str]:
    """Extract dominant colors from image bytes. Returns palette dict."""
    try:
        from PIL import Image
    except ImportError:
        raise RuntimeError("Pillow not installed")

    img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    img_small = img.copy()
    img_small.thumbnail((200, 200))
    pixels = list(img_small.getdata())

    if len(pixels) < num_colors:
        num_colors = max(3, len(pixels) // 10)

    from collections import Counter
    quantized = img_small.quantize(colors=num_colors, method=2)
    palette_raw = quantized.getpalette()
    if not palette_raw:
        palette_raw = []

    colors_rgb = []
    for i in range(0, min(len(palette_raw), num_colors * 3), 3):
        if i + 2 < len(palette_raw):
            colors_rgb.append((palette_raw[i], palette_raw[i + 1], palette_raw[i + 2]))

    counter = Counter(quantized.getdata())
    total = sum(counter.values())

    color_info = []
    for idx, count in counter.most_common():
        if idx < len(colors_rgb):
            r, g, b = colors_rgb[idx]
            pct = count / total
            color_info.append({
                "rgb": (r, g, b),
                "hex": _hex(r, g, b),
                "brightness": _brightness(r, g, b),
                "pct": pct,
            })

    color_info.sort(key=lambda c: c["brightness"])

    palette = _map_to_palette(color_info)
    return palette


def _map_to_palette(color_info: List[dict]) -> Dict[str, str]:
    """Map extracted colors to Blueprint palette roles."""
    palette = {
        "background": "#FFFFFF",
        "accent": "#4A90D9",
        "primary": "#2D2D2D",
        "text": "#555555",
        "border": "#E0E0E0",
        "highlight": "#F0F6FF",
        "secondary": "#F5F5F5",
    }

    if not color_info:
        return palette

    dark_colors = [c for c in color_info if c["brightness"] < 100]
    mid_colors = [c for c in color_info if 100 <= c["brightness"] < 200]
    light_colors = [c for c in color_info if c["brightness"] >= 200]

    bg_candidates = sorted(light_colors + mid_colors, key=lambda c: c["brightness"], reverse=True)
    accent_candidates = sorted(mid_colors + dark_colors, key=lambda c: c["pct"], reverse=True)

    if bg_candidates:
        bg = bg_candidates[0]
        palette["background"] = bg["hex"]
        lighter = _brighten(bg["rgb"], 20)
        palette["highlight"] = lighter
        lighter2 = _brighten(bg["rgb"], 10)
        palette["secondary"] = lighter2

    if accent_candidates:
        accent = accent_candidates[0]
        palette["accent"] = accent["hex"]
    elif color_info:
        palette["accent"] = color_info[0]["hex"]

    if dark_colors:
        palette["primary"] = dark_colors[0]["hex"]
        palette["text"] = dark_colors[0]["hex"]
    elif color_info:
        darkest = color_info[0]
        palette["primary"] = darkest["hex"]
        palette["text"] = darkest["hex"]

    accent_rgb = _hex_to_rgb(palette["accent"])
    palette["border"] = _lighten(accent_rgb, 80)

    return palette


def _brighten(rgb, amount):
    r = min(255, rgb[0] + amount)
    g = min(255, rgb[1] + amount)
    b = min(255, rgb[2] + amount)
    return _hex(r, g, b)


def _lighten(rgb, amount):
    r = min(255, rgb[0] + amount)
    g = min(255, rgb[1] + amount)
    b = min(255, rgb[2] + amount)
    return _hex(r, g, b)


def _hex_to_rgb(hex_str):
    h = hex_str.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def extract_image_info(image_bytes: bytes) -> dict:
    """Full image analysis: colors + dimensions + dominant color count."""
    try:
        from PIL import Image
    except ImportError:
        raise RuntimeError("Pillow not installed")

    img = Image.open(io.BytesIO(image_bytes))
    w, h = img.size

    palette = extract_colors(image_bytes)

    return {
        "width": w,
        "height": h,
        "aspect_ratio": round(w / h, 2) if h > 0 else 1,
        "palette": palette,
        "success": True,
    }

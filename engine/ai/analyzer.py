import json
import logging
from typing import Optional, Dict, Any, Callable, List
from .models import (
    AnalysisResult, PageAnalysis, DetectedElement,
    LayoutColor, PageType,
)
from .cache import AnalysisCache
from .providers import get_provider

logger = logging.getLogger(__name__)

ANALYSIS_PROMPT = """You are an expert planner/agenda layout analyzer. You will map EVERY visual element on this page into JSON.

CRITICAL RULES:
1. MINIMUM 30 elements. Most pages have 40-60. If under 25 you FAILED.
2. You MUST cover the ENTIRE page from y=0 to y=210mm. If nothing below y=100mm you missed HALF the page.
3. CIRCLES use type="circle". CHECKBOXES are circles. NEVER use type="rect" for a circle/checkbox.
4. DECORATIVE elements (bees, hearts, flowers, stars, butterflies, dots, icons) use type="decorative" with a "shape" field.
5. All coordinates in MILLIMETERS. A5 = 148mm wide × 210mm tall. (0,0)=top-left.

VALID TYPES: "rect", "line", "circle", "text", "grid", "decorative", "strip"

VALID SHAPES FOR decorative: "heart", "bee", "flower", "star", "butterfly", "dot", "leaf", "diamond", "circle_shape"

Return ONLY valid JSON (no markdown):
{
  "page_type": "1dpp",
  "page_type_label": "Um por Pagina",
  "confidence": 0.95,
  "title": "Title on page",
  "description": "Describe full layout",
  "margins": {"top": 8, "bottom": 8, "left": 8, "right": 8},
  "colors": [
    {"name": "background", "hex": "#FFFFFF", "role": "background"},
    {"name": "accent", "hex": "#FF5FA2", "role": "accent"},
    {"name": "text_dark", "hex": "#2D2D2D", "role": "primary"},
    {"name": "text_light", "hex": "#888888", "role": "text"},
    {"name": "border", "hex": "#E0E0E0", "role": "border"},
    {"name": "highlight", "hex": "#FFF0F5", "role": "highlight"},
    {"name": "fill", "hex": "#F5F5F5", "role": "secondary"}
  ],
  "fonts_detected": ["Helvetica", "Helvetica-Bold"],
  "inferred_pages": ["planejamento", "semanal", "notas"],
  "elements": []
}

ELEMENT FORMAT - each element MUST have ALL fields:
{"type":"TYPE","x":0,"y":0,"w":10,"h":10,"text":"","font_name":"","font_size":0,"color":"#000000","bg_color":"","border":false,"border_color":"","border_width":0.5,"bold":false,"italic":false,"align":"left","line_height":0,"opacity":1.0,"radius":0,"shape":"","cols":0,"rows":0}

DETECT THESE ZONES (top to bottom, cover ALL 210mm):

ZONE 1 — HEADER (y=0 to y=30mm):
- Full-width colored rect (bg_color fills it, no text)
- Day name text (bold, big, e.g. "TERCA")
- Day number text (very bold, huge, e.g. "15")
- Month/year text (e.g. "julho 2026")
- Any decorative elements in header area
- Accent line below header

ZONE 2 — LEFT COLUMN TOP (x=5 to x=72mm, y=30 to y=100mm):
- Section title "PRIORIDADES" (bold text)
- Background rect behind priority boxes
- Checkbox 1: type="circle" with x,y,w,h (small, ~3-4mm)
- Task text next to checkbox 1
- Checkbox 2: type="circle"
- Task text next to checkbox 2
- Checkbox 3: type="circle"
- Task text next to checkbox 3
- Divider line

ZONE 3 — LEFT COLUMN BOTTOM (x=5 to x=72mm, y=100 to y=200mm):
- Section title "ANOTACOES" (bold text)
- Background rect for notes area
- Each horizontal ruled line (type="line", w≈60mm, h=0)
- You MUST count and create ALL ruled lines (typically 7-12)

ZONE 4 — RIGHT COLUMN (x=75 to x=143mm, y=30 to y=200mm):
- Section title "AGENDAMENTOS" (bold text)
- For EACH time slot:
  - Time text "08:00", "09:00", etc. (type="text", font_size=5-6)
  - Horizontal line next to it (type="line", w≈55mm, h=0)
- Minimum 8 time slots (08:00 to 15:00)

ZONE 5 — BOTTOM (y=190 to y=210mm):
- Any decorative elements (hearts, bees, flowers, stars)
- Page number or footer text
- Background fills

SHAPE DETECTION:
- Round checkbox → type="circle", shape=""
- Heart illustration → type="decorative", shape="heart"
- Bee illustration → type="decorative", shape="bee"
- Flower illustration → type="decorative", shape="flower"
- Star illustration → type="decorative", shape="star"
- Small colored dot → type="circle", w=2, h=2

FINAL CHECK before returning:
- Count your elements. Under 25? Add more.
- Highest y value in your elements? Must be > 180mm.
- Any circle/checkbox marked as "rect"? Fix to "circle".
- Any decorative illustration missing? Add it.
- inferred_pages should have MAX 4 entries."""

PAGE_TYPE_MAP = {
    "1dpp": PageType.ONE_PER_PAGE,
    "2dpp": PageType.TWO_PER_PAGE,
    "semanal": PageType.WEEKLY,
    "mensal": PageType.MONTHLY,
    "calendario": PageType.CALENDAR,
    "planejamento": PageType.PLANNING,
    "metas": PageType.GOALS,
    "checklist": PageType.CHECKLIST,
    "dados_pessoais": PageType.PERSONAL_DATA,
    "notas": PageType.NOTES,
    "divisoria": PageType.DIVIDER,
    "desconhecido": PageType.UNKNOWN,
}


class SmartAnalyzer:
    """Main orchestrator for AI layout analysis."""

    def __init__(self, provider_name: str = "openai", api_key: Optional[str] = None,
                 model: Optional[str] = None):
        self._provider_name = provider_name
        self._api_key = api_key
        self._model = model
        self._cache = AnalysisCache(ttl_seconds=3600, max_entries=100)
        self._provider = None

    def _get_provider(self):
        if self._provider is None:
            kwargs = {}
            if self._api_key:
                kwargs["api_key"] = self._api_key
            if self._model:
                kwargs["model"] = self._model
            self._provider = get_provider(self._provider_name, **kwargs)
        return self._provider

    def analyze(self, image_bytes: bytes, content_type: str = "image/png",
                on_progress: Optional[Callable] = None) -> AnalysisResult:
        result = AnalysisResult(provider=self._provider_name, model=self._model or "")

        if on_progress:
            on_progress({"stage": "upload", "progress": 10, "message": "Validating image..."})

        if len(image_bytes) < 100:
            result.error = "Invalid image: file too small"
            return result

        if len(image_bytes) > 20_000_000:
            result.error = "Image too large (max 20MB)"
            return result

        result.image_hash = self._cache._key(image_bytes)

        if on_progress:
            on_progress({"stage": "cache", "progress": 20, "message": "Checking cache..."})

        cached = self._cache.get(image_bytes)
        if cached:
            cached.cached = True
            if on_progress:
                on_progress({"stage": "complete", "progress": 100, "message": "Loaded from cache"})
            return cached

        try:
            provider = self._get_provider()
        except Exception as e:
            result.error = f"Provider init error: {str(e)}"
            return result

        if on_progress:
            on_progress({"stage": "ocr", "progress": 30, "message": "Running OCR and visual analysis..."})

        try:
            raw = provider.analyze_image(
                image_bytes,
                ANALYSIS_PROMPT,
                content_type=content_type,
            )
            result.raw_response = raw
        except Exception as e:
            result.error = f"AI analysis failed: {str(e)}"
            return result

        if on_progress:
            on_progress({"stage": "elements", "progress": 60, "message": "Detecting elements..."})

        try:
            parsed = self._parse_response(raw)
        except Exception as e:
            import traceback
            traceback.print_exc()
            print(f"[PARSE ERROR] Raw response: {json.dumps(raw)[:500]}")
            result.error = f"Parse error: {str(e)}"
            result.raw_response = raw
            return result
        result.page_analysis = parsed

        if on_progress:
            on_progress({"stage": "colors", "progress": 80, "message": "Extracting color palette..."})

        if on_progress:
            on_progress({"stage": "structure", "progress": 90, "message": "Building project structure..."})

        result.success = True
        self._cache.put(image_bytes, result)

        if on_progress:
            on_progress({"stage": "complete", "progress": 100, "message": "Analysis complete"})

        return result

    def _parse_response(self, raw: Dict[str, Any]) -> PageAnalysis:
        def _float(val, default=0):
            if val is None:
                return default
            try:
                return float(val)
            except (TypeError, ValueError):
                return default

        analysis = PageAnalysis()

        pt = raw.get("page_type", "desconhecido")
        analysis.page_type = PAGE_TYPE_MAP.get(pt, PageType.UNKNOWN)
        analysis.page_type_label = raw.get("page_type_label", pt)
        analysis.confidence = _float(raw.get("confidence"), 0.5)
        analysis.title = raw.get("title", "")
        analysis.description = raw.get("description", "")
        analysis.margins = raw.get("margins", {"top": 10, "bottom": 10, "left": 8, "right": 8})
        analysis.inferred_pages = raw.get("inferred_pages", [])
        analysis.fonts_detected = raw.get("fonts_detected", [])

        for c in raw.get("colors", []):
            analysis.colors.append(LayoutColor(
                name=c.get("name", "accent"),
                hex=c.get("hex", "#000000"),
                role=c.get("role", "accent"),
            ))

        for e in raw.get("elements", []):
            etype = e.get("type", "rect")
            w_val = _float(e.get("w"))
            h_val = _float(e.get("h"))

            if etype == "rect" and w_val > 0 and h_val > 0:
                ratio = w_val / h_val if h_val else 0
                if 0.7 < ratio < 1.4 and w_val < 8:
                    etype = "circle"

            analysis.elements.append(DetectedElement(
                type=etype,
                x=_float(e.get("x")),
                y=_float(e.get("y")),
                w=w_val,
                h=h_val,
                text=e.get("text", ""),
                font_name=e.get("font_name", "Helvetica"),
                font_size=_float(e.get("font_size"), 10),
                color=e.get("color", "#000000"),
                bg_color=e.get("bg_color"),
                border=bool(e.get("border")),
                border_color=e.get("border_color"),
                border_width=_float(e.get("border_width"), 0.5),
                bold=bool(e.get("bold")),
                italic=bool(e.get("italic")),
                align=e.get("align", "left"),
                line_height=_float(e.get("line_height"), 14),
                opacity=_float(e.get("opacity"), 1.0),
                radius=_float(e.get("radius"), 0),
                shape=e.get("shape", ""),
                cols=int(e.get("cols", 0) or 0),
                rows=int(e.get("rows", 0) or 0),
            ))

        return analysis

    @property
    def cache(self) -> AnalysisCache:
        return self._cache

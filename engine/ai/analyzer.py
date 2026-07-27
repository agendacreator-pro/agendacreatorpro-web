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

ANALYSIS_PROMPT = """Analyze this planner/agenda page image. Return a JSON object describing every visual element.

PAGE: A5 = 148mm wide × 210mm tall. Origin (0,0) = top-left. All values in mm.

Return ONLY valid JSON:
{
  "page_type": "1dpp",
  "page_type_label": "Um por Pagina",
  "confidence": 0.9,
  "title": "Title visible on page",
  "description": "What the page looks like",
  "margins": {"top": 8, "bottom": 8, "left": 8, "right": 8},
  "colors": [
    {"name": "bg", "hex": "#FFFFFF", "role": "background"},
    {"name": "accent", "hex": "#FF5FA2", "role": "accent"},
    {"name": "dark", "hex": "#2D2D2D", "role": "primary"},
    {"name": "light", "hex": "#888888", "role": "text"},
    {"name": "border", "hex": "#E0E0E0", "role": "border"},
    {"name": "fill", "hex": "#FFF0F5", "role": "highlight"}
  ],
  "fonts_detected": ["Helvetica", "Helvetica-Bold"],
  "inferred_pages": ["planejamento", "semanal", "notas"],
  "elements": []
}

Each element in "elements" array:
{"type":"TYPE","x":0,"y":0,"w":10,"h":10,"text":"","font_name":"","font_size":0,"color":"#000000","bg_color":"","border":false,"border_color":"","border_width":0.5,"bold":false,"italic":false,"align":"left","line_height":0,"opacity":1.0,"radius":0,"shape":"","cols":0,"rows":0}

TYPES: rect, line, circle, text, grid, decorative, strip

RULES:
1. Detect EVERY visual element from top (y=0) to bottom (y=210). Missing the bottom half = FAILED.
2. Checkboxes and small round things = type "circle", NOT "rect"
3. Illustrations (bees, hearts, flowers, stars) = type "decorative", shape = "bee"/"heart"/"flower"/"star"
4. For each time slot (08:00-17:00) create a text element AND a line element
5. For each checkbox create a circle element AND a text element next to it
6. For each ruled line in notes area create a line element
7. MINIMUM 30 elements. Count before returning.
8. inferred_pages: MAX 4 entries
9. All coordinates must be accurate mm positions from the image edges
10. Detect the ACTUAL colors, text, and positions visible in the image"""

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

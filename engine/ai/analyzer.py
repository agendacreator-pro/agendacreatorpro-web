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

ANALYSIS_PROMPT = """You are an expert visual layout analyzer. Analyze the uploaded agenda/planner/planner image and reconstruct EVERY visual element precisely.

Return ONLY valid JSON (no markdown, no code blocks) with this exact structure:
{
  "page_type": "1dpp|2dpp|semanal|mensal|calendario|planejamento|metas|checklist|dados_pessoais|notas|divisoria",
  "page_type_label": "Label in Portuguese",
  "confidence": 0.95,
  "title": "Title of the page",
  "description": "Description of the layout",
  "margins": {"top": 10, "bottom": 10, "left": 8, "right": 8},
  "colors": [
    {"name": "primary", "hex": "#2D2D2D", "role": "primary"},
    {"name": "background", "hex": "#FFFFFF", "role": "background"},
    {"name": "accent", "hex": "#FF5FA2", "role": "accent"},
    {"name": "text", "hex": "#666666", "role": "text"},
    {"name": "border", "hex": "#E0E0E0", "role": "border"},
    {"name": "highlight", "hex": "#FFF0F5", "role": "highlight"}
  ],
  "fonts_detected": ["font name 1", "font name 2"],
  "inferred_pages": ["page_type_1", "page_type_2"],
  "elements": [
    {
      "type": "rect",
      "x": 15, "y": 10, "w": 118, "h": 8,
      "text": "",
      "font_name": "Helvetica",
      "font_size": 1,
      "color": "#000000",
      "bg_color": "#FF5FA2",
      "border": false,
      "border_color": null,
      "border_width": 0.5,
      "bold": false,
      "italic": false,
      "align": "left",
      "line_height": 14,
      "opacity": 1.0
    }
  ]
}

DETECT EVERY VISUAL ELEMENT - be extremely thorough:
- HEADER BAR at top: colored rectangles, date area, day name area
- SECTION HEADERS: "PRIORIDADES", "ANOTACOES", "AGENDAMENTOS", any text titles
- DIVIDER LINES: horizontal lines, vertical lines separating sections
- BOXES with borders: priority boxes, notes areas, task areas
- CHECKBOXES: small squares/circles with text next to them
- TIME SCHEDULE: rows with times (08:00, 09:00...) and lines
- GRIDS/TABLES: rows and columns with separators
- DECORATIVE ELEMENTS: flowers, hearts, stars, shapes, icons
- DATE/DAY displays: large day number, month name, day of week
- TEXT BLOCKS: placeholder lines, sample text, labels
- SMALL DETAILS: corner decorations, colored dots, background patterns

COORDINATE SYSTEM:
- Origin (0,0) is TOP-LEFT of the page
- All values in MILLIMETERS (mm)
- A5 page = 148mm wide × 210mm tall
- Measure positions carefully from the image edges

CRITICAL RULES:
- Detect the ACTUAL text visible in the image (not placeholders)
- Detect actual hex colors from the image
- Include EVERY element, even small ones (dots, thin lines, tiny icons)
- Position accuracy is essential for faithful recreation
- If you see a pink header bar at the top with date, create a rect element for it
- If you see time slots, create line elements for each one
- If you see decorative flowers/hearts, create decorative elements for them
- Each element must have complete attributes (no nulls for required fields)"""

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
            analysis.elements.append(DetectedElement(
                type=e.get("type", "rect"),
                x=_float(e.get("x")),
                y=_float(e.get("y")),
                w=_float(e.get("w")),
                h=_float(e.get("h")),
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
            ))

        return analysis

    @property
    def cache(self) -> AnalysisCache:
        return self._cache

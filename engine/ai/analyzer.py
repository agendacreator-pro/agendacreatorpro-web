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

ANALYSIS_PROMPT = """You are an expert layout analyzer for agenda/planner page designs.

Analyze the uploaded image and return a detailed JSON description of the layout.

Return ONLY valid JSON (no markdown, no explanation) with this exact structure:
{
  "page_type": "1dpp|2dpp|semanal|mensal|calendario|planejamento|metas|checklist|dados_pessoais|notas|divisoria|desconhecido",
  "page_type_label": "Human readable name of the page type",
  "confidence": 0.95,
  "title": "Detected title or section name",
  "description": "Brief description of the page layout",
  "margins": {"top": 10, "bottom": 10, "left": 8, "right": 8},
  "colors": [
    {"name": "primary", "hex": "#2D2D2D", "role": "primary"},
    {"name": "secondary", "hex": "#FFFFFF", "role": "background"},
    {"name": "accent", "hex": "#FF5FA2", "role": "accent"}
  ],
  "fonts_detected": ["Helvetica-Bold", "Helvetica"],
  "inferred_pages": ["dados_pessoais", "planejamento", "diarias", "semanal"],
  "elements": [
    {
      "type": "rect|line|text|circle|box",
      "x": 15,
      "y": 20,
      "w": 118,
      "h": 28,
      "text": "PRIORIDADES",
      "font_name": "Helvetica-Bold",
      "font_size": 7,
      "color": "#2D2D2D",
      "bg_color": null,
      "border": true,
      "border_color": "#E0E0E0",
      "border_width": 0.5,
      "bold": true,
      "italic": false,
      "align": "left",
      "line_height": 14,
      "opacity": 1.0
    }
  ]
}

IMPORTANT RULES:
- All coordinates and sizes are in MILLIMETERS (mm), relative to A5 page (148x210mm) unless specified
- Detect ALL visible elements: lines, boxes, text blocks, headers, separators, icons, checkboxes, grids
- For each text element, detect the actual text content
- Detect colors as hex values (#RRGGBB)
- If the page has a time schedule/horario, mark it as "schedule_detected": true
- Infer what other pages this agenda would logically contain based on the detected type
- Be precise with element positions (x, y from top-left origin)"""

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

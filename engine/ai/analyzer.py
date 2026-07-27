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

ANALYSIS_PROMPT = """You are an expert visual layout analyzer specializing in planner/agenda page design. Your task is to map EVERY SINGLE visual element on this page with extreme precision.

IMPORTANT: You MUST detect a MINIMUM of 25 elements. Most planner pages have 30-50+ elements. If you detect fewer than 20, you are MISSING elements. Look again more carefully.

PAGE SIZE REFERENCE: A5 = 148mm wide × 210mm tall. Coordinates: (0,0) = top-left corner. X goes right, Y goes down. All values in MILLIMETERS.

SCAN THE IMAGE SYSTEMATICALLY from top to bottom, left to right. For each visual component you see, create an element.

Return ONLY valid JSON (no markdown, no code blocks) with this exact structure:
{
  "page_type": "1dpp",
  "page_type_label": "Um por Pagina",
  "confidence": 0.95,
  "title": "Title visible on page",
  "description": "Detailed description of the layout",
  "margins": {"top": 8, "bottom": 8, "left": 8, "right": 8},
  "colors": [
    {"name": "primary", "hex": "#2D2D2D", "role": "primary"},
    {"name": "background", "hex": "#FFFFFF", "role": "background"},
    {"name": "accent", "hex": "#FF5FA2", "role": "accent"},
    {"name": "light", "hex": "#FFF0F5", "role": "highlight"},
    {"name": "text", "hex": "#555555", "role": "text"},
    {"name": "border", "hex": "#E0E0E0", "role": "border"},
    {"name": "secondary", "hex": "#F5F5F5", "role": "secondary"}
  ],
  "fonts_detected": ["Helvetica", "Helvetica-Bold"],
  "inferred_pages": ["planejamento", "semanal", "mensal", "checklist", "notas"],
  "elements": [
    {"type": "rect", "x": 0, "y": 0, "w": 148, "h": 25, "text": "", "font_name": "", "font_size": 0, "color": "", "bg_color": "#FF5FA2", "border": false, "border_color": null, "border_width": 0, "bold": false, "italic": false, "align": "left", "line_height": 0, "opacity": 1.0},
    {"type": "text", "x": 10, "y": 4, "w": 50, "h": 8, "text": "TERCA", "font_name": "Helvetica-Bold", "font_size": 9, "color": "#FFFFFF", "bg_color": "", "border": false, "border_color": null, "border_width": 0, "bold": true, "italic": false, "align": "left", "line_height": 12, "opacity": 1.0},
    {"type": "text", "x": 10, "y": 12, "w": 30, "h": 10, "text": "15", "font_name": "Helvetica-Bold", "font_size": 24, "color": "#FFFFFF", "bg_color": "", "border": false, "border_color": null, "border_width": 0, "bold": true, "italic": false, "align": "left", "line_height": 28, "opacity": 1.0},
    {"type": "text", "x": 40, "y": 14, "w": 40, "h": 6, "text": "julho 2026", "font_name": "Helvetica", "font_size": 8, "color": "#FFFFFF", "bg_color": "", "border": false, "border_color": null, "border_width": 0, "bold": false, "italic": false, "align": "left", "line_height": 10, "opacity": 1.0},
    {"type": "line", "x": 0, "y": 25, "w": 148, "h": 0, "text": "", "font_name": "", "font_size": 0, "color": "#FF5FA2", "bg_color": "", "border": false, "border_color": null, "border_width": 1.5, "bold": false, "italic": false, "align": "left", "line_height": 0, "opacity": 1.0},
    {"type": "text", "x": 8, "y": 28, "w": 30, "h": 6, "text": "PRIORIDADES", "font_name": "Helvetica-Bold", "font_size": 6, "color": "#FF5FA2", "bg_color": "", "border": false, "border_color": null, "border_width": 0, "bold": true, "italic": false, "align": "left", "line_height": 8, "opacity": 1.0},
    {"type": "rect", "x": 8, "y": 35, "w": 62, "h": 8, "text": "", "font_name": "", "font_size": 0, "color": "", "bg_color": "#FFF0F5", "border": true, "border_color": "#FFD6E8", "border_width": 0.3, "bold": false, "italic": false, "align": "left", "line_height": 0, "opacity": 1.0},
    {"type": "circle", "x": 10, "y": 37, "w": 3, "h": 3, "text": "", "font_name": "", "font_size": 0, "color": "#FF5FA2", "bg_color": "", "border": false, "border_color": null, "border_width": 0, "bold": false, "italic": false, "align": "left", "line_height": 0, "opacity": 1.0},
    {"type": "text", "x": 15, "y": 37, "w": 52, "h": 4, "text": "Revisar material do curso", "font_name": "Helvetica", "font_size": 5, "color": "#555555", "bg_color": "", "border": false, "border_color": null, "border_width": 0, "bold": false, "italic": false, "align": "left", "line_height": 6, "opacity": 1.0}
  ]
}

EXAMPLE OF30+ ELEMENTS for a typical planner page (your output must have this many or more):

TOP SECTION (y=0 to 30mm) — Header bar:
1. Large colored rect covering full width (background bar)
2. Day name text ("TERCA", "QUARTA", etc.)
3. Day number (large font, "15", "16", etc.)
4. Month/year text ("julho 2026")
5. Decorative line below header

LEFT COLUMN (x=8 to 74mm, y=30 to 200mm):
6. Section title "PRIORIDADES" 
7. Colored background rect for priority area
8. Checkbox circle for task 1
9. Text for task 1
10. Checkbox circle for task 2
11. Text for task 2
12. Checkbox circle for task 3
13. Text for task 3
14. Divider line between sections
15. Section title "ANOTACOES"
16. Background rect for notes area
17. Horizontal ruled line 1
18. Horizontal ruled line 2
19. Horizontal ruled line 3
20. Horizontal ruled line 4
21. Horizontal ruled line 5
22. Horizontal ruled line 6
23. Horizontal ruled line 7

RIGHT COLUMN (x=74 to 140mm, y=30 to 200mm):
24. Section title "AGENDAMENTOS"
25. Time label "08:00"
26. Horizontal line for 08:00
27. Time label "09:00"
28. Horizontal line for 09:00
29. Time label "10:00"
30. Horizontal line for 10:00
31. Time label "11:00"
32. Horizontal line for 11:00
33. Time label "12:00"
34. Horizontal line for 12:00
35. Time label "13:00"
36. Horizontal line for 13:00
37. Time label "14:00"
38. Horizontal line for 14:00
39. Time label "15:00"
40. Horizontal line for 15:00
41. Time label "16:00"
42. Horizontal line for 16:00
43. Time label "17:00"
44. Horizontal line for 17:00

BOTTOM:
45. Decorative element (heart/flower/star)
46. Page number or small text

WHAT TO DETECT (be extremely thorough):

HEADER AREA (y=0 to 30mm):
- Full-width colored rectangle (the header bar)
- Day name text (bold, large)
- Day number (very large, bold)
- Month and year text
- Any decorative elements in header
- Thin line below header

SECTIONS (y=30 to 200mm):
- Each section title (PRIORIDADES, ANOTACOES, AGENDAMENTOS, etc.)
- Background rectangles behind each section
- Every checkbox (small circle or square) — YES, each individual one
- Every task text next to each checkbox
- Every horizontal ruled line in notes area
- Every time slot label (08:00, 09:00, etc.)
- Every horizontal line next to time slots
- Vertical dividers between columns
- Any colored accent strips or borders

DECORATIVE ELEMENTS:
- Hearts, flowers, stars, dots, icons
- Corner decorations
- Background patterns
- Colored dots or shapes
- Small illustrations

COORDINATE ACCURACY:
- Measure from the ACTUAL edges of each element in the image
- A5 page is 148mm wide × 210mm tall
- If header bar is top 12% of page: y=0, h=25mm
- If left column starts 5% from left: x=8mm
- If a line is at 60% down the page: y=126mm

CRITICAL: Return MINIMUM 25 elements. Most planner pages have 30-50. Count your elements before returning. If you have fewer than 20, STOP and look for more elements you missed."""

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
                radius=_float(e.get("radius"), 0),
                shape=e.get("shape", ""),
                cols=int(e.get("cols", 0) or 0),
                rows=int(e.get("rows", 0) or 0),
            ))

        return analysis

    @property
    def cache(self) -> AnalysisCache:
        return self._cache

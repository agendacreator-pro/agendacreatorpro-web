import json
import logging
from typing import Optional, Dict, Any, Callable, List
from .models import (
    AnalysisResult, PageAnalysis, DetectedElement,
    LayoutColor, PageType,
)
from .blueprint import Blueprint, EditableObject, Section
from .cache import AnalysisCache
from .providers import get_provider

logger = logging.getLogger(__name__)

ANALYSIS_PROMPT = """You are an expert layout architect analyzing a planner/agenda page.

Do NOT treat this as a photograph to copy pixel-by-pixel.
Treat this as a LAYOUT DOCUMENT to reverse-engineer structurally.

Perform this 8-stage analysis:

ETAPA 1 — STRUCTURAL GEOMETRY
Detect: margins, columns, lines, boxes, grids, content areas, alignments, spacing, hierarchy.
The page is A5 = 148mm wide × 210mm tall. (0,0) = top-left.

ETAPA 2 — ELEMENT CLASSIFICATION
Every visual element must be classified as one of:
TEXT, LINE, RECTANGLE, ROUNDED_RECTANGLE, CIRCLE, ICON, DECORATION,
HEADER, FOOTER, TABLE, CHECKBOX, BULLET, SECTION

Each element has: x, y, w, h (in mm), color, border_width, layer, align

ETAPA 3 — EDITABLE OBJECTS
Every element becomes an independent editable object.
Never draw the page as a single image. Every object is independent.

ETAPA 4 — OCR (Semantic Extraction)
Extract the SEMANTIC MEANING of text, not literal text:
- "Segunda-feira" → DAY_NAME
- "Janeiro" → MONTH_NAME
- "15" → DAY_NUMBER
- "PRIORIDADES" → SECTION_TITLE
- "Revisar material" → TASK_TEXT
- "08:00" → TIME_SLOT
- "ANOTACOES" → SECTION_TITLE
- "Notas" → NOTES_LABEL

ETAPA 5 — STYLE ANALYSIS
Detect: color family, visual weight, border thickness, border radius,
style type (minimalist/floral/modern/childish/elegant/executive/kawaii)

ETAPA 6 — PAGE TYPE INFERENCE
Classify as: 1dpp, 2dpp, semanal, mensal, calendario, checklist, planejamento, metas, dados_pessoais, notas

ETAPA 7 — BLUEPRINT GENERATION
Generate a Blueprint JSON that captures the COMPLETE structural layout.
This Blueprint will be used to generate all pages of this type.

ETAPA 8 — INFERRED PAGES
List which other page types should be generated from this Blueprint style.

Return ONLY valid JSON (no markdown):
{
  "page_type": "1dpp",
  "page_type_label": "Um por Pagina",
  "confidence": 0.9,
  "description": "Describe the visual style and layout structure",
  "grid": {
    "columns": 2,
    "rows": 1,
    "gutter": 4,
    "column_widths": [66, 66],
    "row_heights": []
  },
  "margins": {"top": 8, "bottom": 8, "left": 8, "right": 8},
  "typography": {
    "header_font": "Helvetica-Bold",
    "body_font": "Helvetica",
    "header_size": 14,
    "day_number_size": 28,
    "section_title_size": 7,
    "body_size": 6,
    "small_size": 5
  },
  "decorations": ["heart", "bee", "flower"],
  "palette": {
    "background": "#FFFFFF",
    "accent": "#FF5FA2",
    "primary": "#2D2D2D",
    "text": "#555555",
    "border": "#E0E0E0",
    "highlight": "#FFF0F5",
    "secondary": "#F5F5F5"
  },
  "sections": [
    {
      "id": "header",
      "section_type": "HEADER",
      "title": "",
      "x": 0, "y": 0, "w": 148, "h": 28,
      "bg_color": "_accent_",
      "border": false,
      "children": [
        {"id": "day_name", "obj_type": "TEXT", "semantic": "DAY_NAME", "value": "TERCA",
         "x": 10, "y": 3, "w": 50, "h": 8, "font_name": "Helvetica-Bold", "font_size": 10,
         "color": "_white_", "bold": true, "align": "left"},
        {"id": "day_number", "obj_type": "TEXT", "semantic": "DAY_NUMBER", "value": "15",
         "x": 10, "y": 11, "w": 25, "h": 14, "font_name": "Helvetica-Bold", "font_size": 28,
         "color": "_white_", "bold": true, "align": "left"},
        {"id": "month_year", "obj_type": "TEXT", "semantic": "MONTH_NAME", "value": "julho 2026",
         "x": 38, "y": 14, "w": 50, "h": 7, "font_name": "Helvetica", "font_size": 9,
         "color": "_white_", "align": "left"}
      ]
    },
    {
      "id": "priorities",
      "section_type": "SECTION",
      "title": "PRIORIDADES",
      "x": 8, "y": 31, "w": 62, "h": 40,
      "children": []
    }
  ],
  "editable_objects": [
    {"id": "day_name", "obj_type": "TEXT", "semantic": "DAY_NAME", "value": "TERCA",
     "x": 10, "y": 3, "w": 50, "h": 8, "font_name": "Helvetica-Bold", "font_size": 10,
     "color": "_white_", "bold": true, "align": "left"},
    {"id": "day_number", "obj_type": "TEXT", "semantic": "DAY_NUMBER", "value": "15",
     "x": 10, "y": 11, "w": 25, "h": 14, "font_name": "Helvetica-Bold", "font_size": 28,
     "color": "_white_", "bold": true, "align": "left"},
    {"id": "month_year", "obj_type": "TEXT", "semantic": "MONTH_NAME", "value": "julho 2026",
     "x": 38, "y": 14, "w": 50, "h": 7, "font_name": "Helvetica", "font_size": 9,
     "color": "_white_", "align": "left"},
    {"id": "header_bg", "obj_type": "RECTANGLE", "x": 0, "y": 0, "w": 148, "h": 28,
     "bg_color": "_accent_"},
    {"id": "accent_line", "obj_type": "LINE", "x": 0, "y": 28, "w": 148, "h": 0,
     "color": "_accent_", "border_width": 1.5},
    {"id": "section_priorities", "obj_type": "SECTION_TITLE", "semantic": "SECTION_TITLE",
     "value": "PRIORIDADES", "x": 8, "y": 31, "w": 35, "h": 6,
     "font_name": "Helvetica-Bold", "font_size": 7, "color": "_accent_", "bold": true},
    {"id": "priority_bg", "obj_type": "ROUNDED_RECTANGLE", "x": 8, "y": 38, "w": 62, "h": 10,
     "bg_color": "_highlight_", "border": true, "border_color": "_accent_", "border_width": 0.3, "radius": 2},
    {"id": "checkbox_1", "obj_type": "CHECKBOX", "x": 10, "y": 40.5, "w": 3.5, "h": 3.5,
     "color": "_accent_"},
    {"id": "task_1", "obj_type": "TEXT", "semantic": "TASK_TEXT", "value": "Revisar material",
     "x": 15, "y": 40, "w": 52, "h": 5, "font_name": "Helvetica", "font_size": 6,
     "color": "_text_"},
    {"id": "checkbox_2", "obj_type": "CHECKBOX", "x": 10, "y": 52.5, "w": 3.5, "h": 3.5,
     "color": "_accent_"},
    {"id": "task_2", "obj_type": "TEXT", "semantic": "TASK_TEXT", "value": "Enviar trabalho",
     "x": 15, "y": 52, "w": 52, "h": 5, "font_name": "Helvetica", "font_size": 6,
     "color": "_text_"},
    {"id": "checkbox_3", "obj_type": "CHECKBOX", "x": 10, "y": 64.5, "w": 3.5, "h": 3.5,
     "color": "_accent_"},
    {"id": "task_3", "obj_type": "TEXT", "semantic": "TASK_TEXT", "value": "Preparar apresentacao",
     "x": 15, "y": 64, "w": 52, "h": 5, "font_name": "Helvetica", "font_size": 6,
     "color": "_text_"},
    {"id": "divider_1", "obj_type": "LINE", "x": 8, "y": 76, "w": 62, "h": 0,
     "color": "_border_", "border_width": 0.5},
    {"id": "section_notes", "obj_type": "SECTION_TITLE", "semantic": "SECTION_TITLE",
     "value": "ANOTACOES", "x": 8, "y": 79, "w": 35, "h": 6,
     "font_name": "Helvetica-Bold", "font_size": 7, "color": "_accent_", "bold": true},
    {"id": "notes_bg", "obj_type": "ROUNDED_RECTANGLE", "x": 8, "y": 87, "w": 62, "h": 115,
     "bg_color": "_white_", "border": true, "border_color": "_border_", "border_width": 0.3},
    {"id": "ruled_1", "obj_type": "LINE", "x": 10, "y": 95, "w": 58, "h": 0,
     "color": "_border_", "border_width": 0.2},
    {"id": "ruled_2", "obj_type": "LINE", "x": 10, "y": 103, "w": 58, "h": 0,
     "color": "_border_", "border_width": 0.2},
    {"id": "ruled_3", "obj_type": "LINE", "x": 10, "y": 111, "w": 58, "h": 0,
     "color": "_border_", "border_width": 0.2},
    {"id": "ruled_4", "obj_type": "LINE", "x": 10, "y": 119, "w": 58, "h": 0,
     "color": "_border_", "border_width": 0.2},
    {"id": "ruled_5", "obj_type": "LINE", "x": 10, "y": 127, "w": 58, "h": 0,
     "color": "_border_", "border_width": 0.2},
    {"id": "ruled_6", "obj_type": "LINE", "x": 10, "y": 135, "w": 58, "h": 0,
     "color": "_border_", "border_width": 0.2},
    {"id": "ruled_7", "obj_type": "LINE", "x": 10, "y": 143, "w": 58, "h": 0,
     "color": "_border_", "border_width": 0.2},
    {"id": "ruled_8", "obj_type": "LINE", "x": 10, "y": 151, "w": 58, "h": 0,
     "color": "_border_", "border_width": 0.2},
    {"id": "ruled_9", "obj_type": "LINE", "x": 10, "y": 159, "w": 58, "h": 0,
     "color": "_border_", "border_width": 0.2},
    {"id": "ruled_10", "obj_type": "LINE", "x": 10, "y": 167, "w": 58, "h": 0,
     "color": "_border_", "border_width": 0.2},
    {"id": "ruled_11", "obj_type": "LINE", "x": 10, "y": 175, "w": 58, "h": 0,
     "color": "_border_", "border_width": 0.2},
    {"id": "ruled_12", "obj_type": "LINE", "x": 10, "y": 183, "w": 58, "h": 0,
     "color": "_border_", "border_width": 0.2},
    {"id": "ruled_13", "obj_type": "LINE", "x": 10, "y": 191, "w": 58, "h": 0,
     "color": "_border_", "border_width": 0.2},
    {"id": "vdivider", "obj_type": "LINE", "x": 74, "y": 31, "w": 0, "h": 172,
     "color": "_border_", "border_width": 0.5},
    {"id": "section_schedule", "obj_type": "SECTION_TITLE", "semantic": "SECTION_TITLE",
     "value": "AGENDAMENTOS", "x": 78, "y": 31, "w": 35, "h": 6,
     "font_name": "Helvetica-Bold", "font_size": 7, "color": "_accent_", "bold": true},
    {"id": "time_08", "obj_type": "TEXT", "semantic": "TIME_SLOT", "value": "08:00",
     "x": 78, "y": 40, "w": 12, "h": 5, "font_name": "Helvetica", "font_size": 5,
     "color": "_text_"},
    {"id": "line_08", "obj_type": "LINE", "x": 92, "y": 44, "w": 48, "h": 0,
     "color": "_border_", "border_width": 0.2},
    {"id": "time_09", "obj_type": "TEXT", "semantic": "TIME_SLOT", "value": "09:00",
     "x": 78, "y": 48, "w": 12, "h": 5, "font_name": "Helvetica", "font_size": 5,
     "color": "_text_"},
    {"id": "line_09", "obj_type": "LINE", "x": 92, "y": 52, "w": 48, "h": 0,
     "color": "_border_", "border_width": 0.2},
    {"id": "time_10", "obj_type": "TEXT", "semantic": "TIME_SLOT", "value": "10:00",
     "x": 78, "y": 56, "w": 12, "h": 5, "font_name": "Helvetica", "font_size": 5,
     "color": "_text_"},
    {"id": "line_10", "obj_type": "LINE", "x": 92, "y": 60, "w": 48, "h": 0,
     "color": "_border_", "border_width": 0.2},
    {"id": "time_11", "obj_type": "TEXT", "semantic": "TIME_SLOT", "value": "11:00",
     "x": 78, "y": 64, "w": 12, "h": 5, "font_name": "Helvetica", "font_size": 5,
     "color": "_text_"},
    {"id": "line_11", "obj_type": "LINE", "x": 92, "y": 68, "w": 48, "h": 0,
     "color": "_border_", "border_width": 0.2},
    {"id": "time_12", "obj_type": "TEXT", "semantic": "TIME_SLOT", "value": "12:00",
     "x": 78, "y": 72, "w": 12, "h": 5, "font_name": "Helvetica", "font_size": 5,
     "color": "_text_"},
    {"id": "line_12", "obj_type": "LINE", "x": 92, "y": 76, "w": 48, "h": 0,
     "color": "_border_", "border_width": 0.2},
    {"id": "time_13", "obj_type": "TEXT", "semantic": "TIME_SLOT", "value": "13:00",
     "x": 78, "y": 80, "w": 12, "h": 5, "font_name": "Helvetica", "font_size": 5,
     "color": "_text_"},
    {"id": "line_13", "obj_type": "LINE", "x": 92, "y": 84, "w": 48, "h": 0,
     "color": "_border_", "border_width": 0.2},
    {"id": "time_14", "obj_type": "TEXT", "semantic": "TIME_SLOT", "value": "14:00",
     "x": 78, "y": 88, "w": 12, "h": 5, "font_name": "Helvetica", "font_size": 5,
     "color": "_text_"},
    {"id": "line_14", "obj_type": "LINE", "x": 92, "y": 92, "w": 48, "h": 0,
     "color": "_border_", "border_width": 0.2},
    {"id": "time_15", "obj_type": "TEXT", "semantic": "TIME_SLOT", "value": "15:00",
     "x": 78, "y": 96, "w": 12, "h": 5, "font_name": "Helvetica", "font_size": 5,
     "color": "_text_"},
    {"id": "line_15", "obj_type": "LINE", "x": 92, "y": 100, "w": 48, "h": 0,
     "color": "_border_", "border_width": 0.2},
    {"id": "time_16", "obj_type": "TEXT", "semantic": "TIME_SLOT", "value": "16:00",
     "x": 78, "y": 104, "w": 12, "h": 5, "font_name": "Helvetica", "font_size": 5,
     "color": "_text_"},
    {"id": "line_16", "obj_type": "LINE", "x": 92, "y": 108, "w": 48, "h": 0,
     "color": "_border_", "border_width": 0.2},
    {"id": "time_17", "obj_type": "TEXT", "semantic": "TIME_SLOT", "value": "17:00",
     "x": 78, "y": 112, "w": 12, "h": 5, "font_name": "Helvetica", "font_size": 5,
     "color": "_text_"},
    {"id": "line_17", "obj_type": "LINE", "x": 92, "y": 116, "w": 48, "h": 0,
     "color": "_border_", "border_width": 0.2},
    {"id": "time_18", "obj_type": "TEXT", "semantic": "TIME_SLOT", "value": "18:00",
     "x": 78, "y": 120, "w": 12, "h": 5, "font_name": "Helvetica", "font_size": 5,
     "color": "_text_"},
    {"id": "line_18", "obj_type": "LINE", "x": 92, "y": 124, "w": 48, "h": 0,
     "color": "_border_", "border_width": 0.2},
    {"id": "bottom_notes_bg", "obj_type": "ROUNDED_RECTANGLE", "x": 78, "y": 134, "w": 60, "h": 68,
     "bg_color": "_secondary_", "border": true, "border_color": "_border_", "border_width": 0.3},
    {"id": "ruled_b1", "obj_type": "LINE", "x": 80, "y": 142, "w": 56, "h": 0,
     "color": "_border_", "border_width": 0.2},
    {"id": "ruled_b2", "obj_type": "LINE", "x": 80, "y": 150, "w": 56, "h": 0,
     "color": "_border_", "border_width": 0.2},
    {"id": "ruled_b3", "obj_type": "LINE", "x": 80, "y": 158, "w": 56, "h": 0,
     "color": "_border_", "border_width": 0.2},
    {"id": "ruled_b4", "obj_type": "LINE", "x": 80, "y": 166, "w": 56, "h": 0,
     "color": "_border_", "border_width": 0.2},
    {"id": "ruled_b5", "obj_type": "LINE", "x": 80, "y": 174, "w": 56, "h": 0,
     "color": "_border_", "border_width": 0.2},
    {"id": "ruled_b6", "obj_type": "LINE", "x": 80, "y": 182, "w": 56, "h": 0,
     "color": "_border_", "border_width": 0.2},
    {"id": "ruled_b7", "obj_type": "LINE", "x": 80, "y": 190, "w": 56, "h": 0,
     "color": "_border_", "border_width": 0.2},
    {"id": "page_number", "obj_type": "TEXT", "semantic": "PAGE_NUMBER", "value": "1 / 365",
     "x": 60, "y": 203, "w": 28, "h": 5, "font_name": "Helvetica", "font_size": 5,
     "color": "_text_", "align": "center"}
  ],
  "inferred_pages": ["planejamento", "semanal", "notas"]
}

CRITICAL RULES:
1. Every editable_object MUST have ALL position fields (x, y, w, h) with accurate mm values
2. Color references use "_accent_", "_primary_", "_text_", "_white_", "_border_", "_highlight_", "_secondary_"
3. semantic field tells the generator what kind of data this object holds
4. The Blueprint must cover the ENTIRE page (y from 0 to ~200mm)
5. Include ALL ruled lines, ALL time slots, ALL checkboxes as individual objects
6. decorative_objects list what decorative elements exist in the image
7. sections describe the logical grouping of objects
8. inferred_pages lists what other page types to generate (max 4)
9. Every section child must be a full object with all fields, not just a reference
10. Include BOTTOM elements (footer, page number, decorative items at bottom)"""


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
            on_progress({"stage": "ocr", "progress": 30, "message": "Running 8-stage structural analysis..."})

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
            on_progress({"stage": "elements", "progress": 60, "message": "Classifying elements..."})

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
            on_progress({"stage": "colors", "progress": 80, "message": "Extracting palette..."})

        if on_progress:
            on_progress({"stage": "structure", "progress": 90, "message": "Building Blueprint..."})

        result.success = True
        self._cache.put(image_bytes, result)

        if on_progress:
            on_progress({"stage": "complete", "progress": 100, "message": "Blueprint generated"})

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
        analysis.title = raw.get("title", raw.get("description", ""))
        analysis.description = raw.get("description", "")
        analysis.margins = raw.get("margins", {"top": 10, "bottom": 10, "left": 8, "right": 8})
        analysis.inferred_pages = raw.get("inferred_pages", [])
        analysis.fonts_detected = raw.get("typography", {}).get("header_font", "Helvetica"), raw.get("typography", {}).get("body_font", "Helvetica")
        analysis.fonts_detected = list(analysis.fonts_detected)

        for c in raw.get("palette", raw.get("colors", [])).items() if isinstance(raw.get("palette", raw.get("colors", {})), dict) else []:
            analysis.colors.append(LayoutColor(
                name=c[0],
                hex=c[1],
                role=c[0],
            ))

        if isinstance(raw.get("colors"), list):
            for c in raw["colors"]:
                already = any(col.hex == c.get("hex", "") for col in analysis.colors)
                if not already:
                    analysis.colors.append(LayoutColor(
                        name=c.get("name", "accent"),
                        hex=c.get("hex", "#000000"),
                        role=c.get("role", "accent"),
                    ))

        blueprint_data = raw
        blueprint_data["editable_objects"] = raw.get("editable_objects", [])
        blueprint_data["sections"] = raw.get("sections", [])
        blueprint_data["decorations"] = raw.get("decorations", raw.get("decorative_elements", []))
        if "typography" not in blueprint_data:
            blueprint_data["typography"] = {}
        if "grid" not in blueprint_data:
            blueprint_data["grid"] = {}
        if "margins" not in blueprint_data:
            blueprint_data["margins"] = {}
        if "palette" not in blueprint_data and "colors" in blueprint_data:
            if isinstance(raw["colors"], list):
                pal = {}
                for c in raw["colors"]:
                    pal[c.get("role", "accent")] = c.get("hex", "#000000")
                blueprint_data["palette"] = pal

        analysis._blueprint_raw = blueprint_data

        for e in raw.get("editable_objects", raw.get("elements", [])):
            analysis.elements.append(DetectedElement(
                type=e.get("obj_type", e.get("type", "rect")).lower().replace("rounded_rectangle", "rect").replace("rectangle", "rect").replace("section_title", "text").replace("checkbox", "circle").replace("icon", "decorative").replace("image", "decorative").replace("bullet", "circle").replace("header", "rect").replace("footer", "rect").replace("table", "grid"),
                x=_float(e.get("x")),
                y=_float(e.get("y")),
                w=_float(e.get("w")),
                h=_float(e.get("h")),
                text=e.get("value", e.get("text", "")),
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

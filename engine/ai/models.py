from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from enum import Enum


class PageType(str, Enum):
    ONE_PER_PAGE = "1dpp"
    TWO_PER_PAGE = "2dpp"
    WEEKLY = "semanal"
    MONTHLY = "mensal"
    CALENDAR = "calendario"
    PLANNING = "planejamento"
    GOALS = "metas"
    CHECKLIST = "checklist"
    PERSONAL_DATA = "dados_pessoais"
    NOTES = "notas"
    DIVIDER = "divisoria"
    UNKNOWN = "desconhecido"


@dataclass
class LayoutColor:
    name: str
    hex: str
    role: str = "accent"


@dataclass
class DetectedElement:
    type: str = "rect"
    x: float = 0
    y: float = 0
    w: float = 0
    h: float = 0
    text: str = ""
    font_name: str = ""
    font_size: float = 10
    color: str = "#000000"
    bg_color: Optional[str] = None
    border: bool = False
    border_color: Optional[str] = None
    border_width: float = 0.5
    rotation: float = 0
    opacity: float = 1.0
    line_height: float = 14
    align: str = "left"
    bold: bool = False
    italic: bool = False
    radius: float = 0
    shape: str = ""
    cols: int = 0
    rows: int = 0

    def to_dict(self) -> dict:
        d = {k: v for k, v in self.__dict__.items() if v is not None and v != ""}
        if self.cols:
            d["cols"] = self.cols
        if self.rows:
            d["rows"] = self.rows
        return d


@dataclass
class PageAnalysis:
    page_type: PageType = PageType.UNKNOWN
    page_type_label: str = "Desconhecido"
    confidence: float = 0.0
    margins: Dict[str, float] = field(default_factory=lambda: {"top": 10, "bottom": 10, "left": 8, "right": 8})
    elements: List[DetectedElement] = field(default_factory=list)
    colors: List[LayoutColor] = field(default_factory=list)
    fonts_detected: List[str] = field(default_factory=list)
    title: str = ""
    description: str = ""
    inferred_pages: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "page_type": self.page_type.value,
            "page_type_label": self.page_type_label,
            "confidence": self.confidence,
            "margins": self.margins,
            "elements": [e.to_dict() for e in self.elements],
            "colors": [c.__dict__ for c in self.colors],
            "fonts_detected": self.fonts_detected,
            "title": self.title,
            "description": self.description,
            "inferred_pages": self.inferred_pages,
        }


@dataclass
class AnalysisResult:
    success: bool = False
    image_hash: str = ""
    page_analysis: Optional[PageAnalysis] = None
    raw_response: Dict[str, Any] = field(default_factory=dict)
    error: str = ""
    provider: str = ""
    model: str = ""
    cached: bool = False

    def to_dict(self) -> dict:
        d = {
            "success": self.success,
            "image_hash": self.image_hash,
            "error": self.error,
            "provider": self.provider,
            "model": self.model,
            "cached": self.cached,
        }
        if self.page_analysis:
            d["page_analysis"] = self.page_analysis.to_dict()
        return d

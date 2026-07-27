"""
Blueprint data model.
A Blueprint is a structural description of a page layout.
It contains ALL information needed to generate any page of the same type.
"""
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any


@dataclass
class EditableObject:
    id: str = ""
    obj_type: str = "TEXT"
    semantic: str = ""
    value: str = ""
    x: float = 0
    y: float = 0
    w: float = 0
    h: float = 0
    font_name: str = "Helvetica"
    font_size: float = 6
    color: str = "#000000"
    bg_color: str = ""
    bold: bool = False
    italic: bool = False
    align: str = "left"
    border: bool = False
    border_color: str = ""
    border_width: float = 0.5
    radius: float = 0
    shape: str = ""
    line_height: float = 0
    layer: int = 0

    def to_dict(self) -> dict:
        d = {}
        for k, v in self.__dict__.items():
            if v is not None and v != "" and v != 0 and v is not False and v != "Helvetica" and v != "#000000":
                d[k] = v
        return d

    @classmethod
    def from_dict(cls, d: dict) -> "EditableObject":
        return cls(**{k: v for k, v in d.items() if k in cls.__dataclass_fields__})


@dataclass
class Section:
    id: str = ""
    section_type: str = "SECTION"
    title: str = ""
    x: float = 0
    y: float = 0
    w: float = 0
    h: float = 0
    bg_color: str = ""
    border: bool = False
    border_color: str = ""
    border_width: float = 0.5
    children: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict:
        d = {}
        for k, v in self.__dict__.items():
            if v is not None and v != "" and v != 0 and v is not False and v != []:
                d[k] = v
        return d


@dataclass
class BlueprintGrid:
    columns: int = 1
    rows: int = 1
    gutter: float = 4
    column_widths: List[float] = field(default_factory=list)
    row_heights: List[float] = field(default_factory=list)

    def to_dict(self) -> dict:
        d = {"columns": self.columns, "rows": self.rows, "gutter": self.gutter}
        if self.column_widths:
            d["column_widths"] = self.column_widths
        if self.row_heights:
            d["row_heights"] = self.row_heights
        return d


@dataclass
class BlueprintMargins:
    top: float = 8
    bottom: float = 8
    left: float = 8
    right: float = 8

    def to_dict(self) -> dict:
        return {"top": self.top, "bottom": self.bottom, "left": self.left, "right": self.right}


@dataclass
class BlueprintTypography:
    header_font: str = "Helvetica-Bold"
    body_font: str = "Helvetica"
    header_size: float = 14
    day_number_size: float = 28
    section_title_size: float = 7
    body_size: float = 6
    small_size: float = 5

    def to_dict(self) -> dict:
        return {
            "header_font": self.header_font,
            "body_font": self.body_font,
            "header_size": self.header_size,
            "day_number_size": self.day_number_size,
            "section_title_size": self.section_title_size,
            "body_size": self.body_size,
            "small_size": self.small_size,
        }


@dataclass
class BlueprintPalette:
    background: str = "#FFFFFF"
    accent: str = "#4A90D9"
    primary: str = "#2D2D2D"
    text: str = "#555555"
    border: str = "#E0E0E0"
    highlight: str = "#F0F6FF"
    secondary: str = "#F5F5F5"

    def to_dict(self) -> dict:
        return {
            "background": self.background,
            "accent": self.accent,
            "primary": self.primary,
            "text": self.text,
            "border": self.border,
            "highlight": self.highlight,
            "secondary": self.secondary,
        }

    def get(self, role: str, fallback: str = "#000000") -> str:
        return getattr(self, role, fallback)


@dataclass
class Blueprint:
    page_type: str = "1dpp"
    page_type_label: str = "Um por Pagina"
    confidence: float = 0.0
    description: str = ""
    grid: BlueprintGrid = field(default_factory=BlueprintGrid)
    margins: BlueprintMargins = field(default_factory=BlueprintMargins)
    typography: BlueprintTypography = field(default_factory=BlueprintTypography)
    decorations: List[str] = field(default_factory=list)
    palette: BlueprintPalette = field(default_factory=BlueprintPalette)
    sections: List[Section] = field(default_factory=list)
    editable_objects: List[EditableObject] = field(default_factory=list)
    inferred_pages: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "page_type": self.page_type,
            "page_type_label": self.page_type_label,
            "confidence": self.confidence,
            "description": self.description,
            "grid": self.grid.to_dict(),
            "margins": self.margins.to_dict(),
            "typography": self.typography.to_dict(),
            "decorations": self.decorations,
            "palette": self.palette.to_dict(),
            "sections": [s.to_dict() for s in self.sections],
            "editable_objects": [o.to_dict() for o in self.editable_objects],
            "inferred_pages": self.inferred_pages,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "Blueprint":
        bp = cls()
        bp.page_type = d.get("page_type", "1dpp")
        bp.page_type_label = d.get("page_type_label", "")
        bp.confidence = float(d.get("confidence", 0))
        bp.description = d.get("description", "")
        bp.decorations = d.get("decorations", [])
        bp.inferred_pages = d.get("inferred_pages", [])

        if "grid" in d:
            g = d["grid"]
            bp.grid = BlueprintGrid(
                columns=g.get("columns", 1),
                rows=g.get("rows", 1),
                gutter=g.get("gutter", 4),
                column_widths=g.get("column_widths", []),
                row_heights=g.get("row_heights", []),
            )
        if "margins" in d:
            m = d["margins"]
            bp.margins = BlueprintMargins(
                top=m.get("top", 8), bottom=m.get("bottom", 8),
                left=m.get("left", 8), right=m.get("right", 8),
            )
        if "typography" in d:
            t = d["typography"]
            bp.typography = BlueprintTypography(
                header_font=t.get("header_font", "Helvetica-Bold"),
                body_font=t.get("body_font", "Helvetica"),
                header_size=t.get("header_size", 14),
                day_number_size=t.get("day_number_size", 28),
                section_title_size=t.get("section_title_size", 7),
                body_size=t.get("body_size", 6),
                small_size=t.get("small_size", 5),
            )
        if "palette" in d:
            p = d["palette"]
            bp.palette = BlueprintPalette(
                background=p.get("background", "#FFFFFF"),
                accent=p.get("accent", "#4A90D9"),
                primary=p.get("primary", "#2D2D2D"),
                text=p.get("text", "#555555"),
                border=p.get("border", "#E0E0E0"),
                highlight=p.get("highlight", "#F0F6FF"),
                secondary=p.get("secondary", "#F5F5F5"),
            )
        for s in d.get("sections", []):
            bp.sections.append(Section(
                id=s.get("id", ""),
                section_type=s.get("section_type", "SECTION"),
                title=s.get("title", ""),
                x=s.get("x", 0), y=s.get("y", 0),
                w=s.get("w", 0), h=s.get("h", 0),
                bg_color=s.get("bg_color", ""),
                border=s.get("border", False),
                border_color=s.get("border_color", ""),
                border_width=s.get("border_width", 0.5),
                children=s.get("children", []),
            ))
        for o in d.get("editable_objects", []):
            bp.editable_objects.append(EditableObject.from_dict(o))
        return bp

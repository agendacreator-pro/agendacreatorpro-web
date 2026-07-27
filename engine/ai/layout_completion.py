"""
Layout Completion Engine.

After initial AI analysis, scan for empty regions and fill them
based on patterns, symmetry, alignment, and repetition.

NEVER leave blank areas. ALWAYS complete the layout.
"""
import copy
import math


def complete_layout(blueprint):
    objects = blueprint.get("editable_objects", [])
    if not objects:
        objects = blueprint.get("elements", [])

    objects = _complete_grid_lines(objects)
    objects = _complete_time_slots(objects)
    objects = _complete_checkboxes(objects)
    objects = _complete_ruled_lines(objects)
    objects = _complete_section_titles(objects)
    objects = _complete_symmetry(objects)
    objects = _complete_spacing(objects)
    objects = _complete_bottom_fill(objects)

    blueprint["editable_objects"] = objects
    return blueprint


def _complete_grid_lines(objects):
    grids = [o for o in objects if o.get("obj_type") in ("GRID", "TABLE")]
    lines = [o for o in objects if o.get("obj_type") == "LINE"]

    for grid in grids:
        gx = float(grid.get("x", 0))
        gy = float(grid.get("y", 0))
        gw = float(grid.get("w", 0))
        gh = float(grid.get("h", 0))
        cols = int(float(grid.get("cols", 7) or 7))
        rows = int(float(grid.get("rows", 6) or 6))

        if cols <= 1 and rows <= 1:
            continue

        existing_v = [l for l in lines
                      if abs(float(l.get("x", 0)) - gx) < 2 and
                      float(l.get("h", 0)) > gh * 0.5]
        existing_h = [l for l in lines
                      if abs(float(l.get("y", 0)) - gy) < 2 and
                      float(l.get("w", 0)) > gw * 0.5]

        if cols > 1 and len(existing_v) < cols - 1:
            cw = gw / cols
            existing_x = sorted([float(l.get("x", 0)) for l in existing_v])
            for ci in range(1, cols):
                vx = gx + ci * cw
                already = any(abs(ex - vx) < 1 for ex in existing_x)
                if not already:
                    objects.append({
                        "id": f"grid_vline_{ci}",
                        "obj_type": "LINE",
                        "x": vx, "y": gy, "w": 0, "h": gh,
                        "color": grid.get("border_color", "_border_"),
                        "border_width": float(grid.get("border_width", 0.3) or 0.3) * 0.5,
                    })

        if rows > 1 and len(existing_h) < rows - 1:
            rh = gh / rows
            existing_y = sorted([float(l.get("y", 0)) for l in existing_h])
            for ri in range(1, rows):
                hy = gy + ri * rh
                already = any(abs(ey - hy) < 1 for ey in existing_y)
                if not already:
                    objects.append({
                        "id": f"grid_hline_{ri}",
                        "obj_type": "LINE",
                        "x": gx, "y": hy, "w": gw, "h": 0,
                        "color": grid.get("border_color", "_border_"),
                        "border_width": float(grid.get("border_width", 0.3) or 0.3) * 0.5,
                    })

    return objects


def _complete_time_slots(objects):
    time_texts = [o for o in objects if o.get("semantic") == "TIME_SLOT"]
    if not time_texts:
        return objects

    time_lines = [o for o in objects if o.get("id", "").startswith("line_") and
                  any(o.get("id", "").endswith(str(h)) for h in range(8, 19))]

    existing_hours = set()
    for t in time_texts:
        val = t.get("value", "")
        if ":" in val:
            hour = val.split(":")[0]
            try:
                existing_hours.add(int(hour))
            except ValueError:
                pass

    if not existing_hours:
        return objects

    min_h = min(existing_hours)
    max_h = max(existing_hours)
    spacing_y = None

    sorted_times = sorted(time_texts, key=lambda t: float(t.get("y", 0)))
    if len(sorted_times) >= 2:
        y1 = float(sorted_times[0].get("y", 0))
        y2 = float(sorted_times[1].get("y", 0))
        spacing_y = y2 - y1

    if spacing_y is None:
        spacing_y = 8

    base_x = float(sorted_times[0].get("x", 78)) if sorted_times else 78
    base_w = float(sorted_times[0].get("w", 12)) if sorted_times else 12
    base_h = float(sorted_times[0].get("h", 5)) if sorted_times else 5
    base_fn = sorted_times[0].get("font_name", "Helvetica") if sorted_times else "Helvetica"
    base_fs = float(sorted_times[0].get("font_size", 5)) if sorted_times else 5
    base_color = sorted_times[0].get("color", "_text_") if sorted_times else "_text_"

    line_base_x = 92
    line_base_w = 48
    line_color = "_border_"

    first_y = float(sorted_times[0].get("y", 40))

    for h in range(8, 19):
        if h in existing_hours:
            continue

        idx = h - min_h
        ty = first_y + idx * spacing_y

        objects.append({
            "id": f"time_{h:02d}",
            "obj_type": "TEXT",
            "semantic": "TIME_SLOT",
            "value": f"{h:02d}:00",
            "x": base_x, "y": ty, "w": base_w, "h": base_h,
            "font_name": base_fn, "font_size": base_fs,
            "color": base_color, "align": "left",
        })

        objects.append({
            "id": f"line_{h:02d}",
            "obj_type": "LINE",
            "x": line_base_x, "y": ty + base_h, "w": line_base_w, "h": 0,
            "color": line_color, "border_width": 0.2,
        })

    return objects


def _complete_checkboxes(objects):
    checkboxes = [o for o in objects if o.get("obj_type") == "CHECKBOX"]
    if len(checkboxes) < 2:
        return objects

    sorted_cb = sorted(checkboxes, key=lambda c: float(c.get("y", 0)))

    spacing = None
    for i in range(1, len(sorted_cb)):
        y1 = float(sorted_cb[i - 1].get("y", 0))
        y2 = float(sorted_cb[i].get("y", 0))
        sp = y2 - y1
        if spacing is None:
            spacing = sp
        elif abs(sp - spacing) < 2:
            spacing = (spacing + sp) / 2

    if spacing is None or spacing < 3:
        return objects

    base_x = float(sorted_cb[0].get("x", 10))
    base_w = float(sorted_cb[0].get("w", 3.5))
    base_h = float(sorted_cb[0].get("h", 3.5))
    base_color = sorted_cb[0].get("color", "_accent_")

    first_y = float(sorted_cb[0].get("y", 40.5))

    last_y = float(sorted_cb[-1].get("y", 40.5))
    expected_count = int((last_y - first_y) / spacing) + 1

    existing_y = set(float(c.get("y", 0)) for c in sorted_cb)

    for i in range(expected_count):
        cy = first_y + i * spacing
        already = any(abs(ey - cy) < 1 for ey in existing_y)
        if not already:
            objects.append({
                "id": f"checkbox_completed_{i}",
                "obj_type": "CHECKBOX",
                "x": base_x, "y": cy, "w": base_w, "h": base_h,
                "color": base_color,
            })

            task_text = [o for o in objects if o.get("obj_type") == "TEXT" and
                         o.get("semantic") == "TASK_TEXT" and
                         abs(float(o.get("y", 0)) - cy) < 2]
            if not task_text:
                objects.append({
                    "id": f"task_completed_{i}",
                    "obj_type": "TEXT",
                    "semantic": "TASK_TEXT",
                    "value": "",
                    "x": base_x + 5, "y": cy - 0.5, "w": 52, "h": 5,
                    "font_name": "Helvetica", "font_size": 6,
                    "color": "_text_", "align": "left",
                })

    return objects


def _complete_ruled_lines(objects):
    ruled = [o for o in objects if o.get("obj_type") == "LINE" and
             float(o.get("h", 0)) == 0 and
             float(o.get("w", 0)) > 30]

    if len(ruled) < 3:
        return objects

    groups = {}
    for line in ruled:
        lx = round(float(line.get("x", 0)) / 10) * 10
        key = f"{lx}_{float(line.get('w', 0)):.0f}"
        if key not in groups:
            groups[key] = []
        groups[key].append(line)

    for key, group in groups.items():
        if len(group) < 3:
            continue

        sorted_g = sorted(group, key=lambda l: float(l.get("y", 0)))
        spacings = []
        for i in range(1, len(sorted_g)):
            y1 = float(sorted_g[i - 1].get("y", 0))
            y2 = float(sorted_g[i].get("y", 0))
            spacings.append(y2 - y1)

        if not spacings:
            continue

        avg_spacing = sum(spacings) / len(spacings)
        if avg_spacing < 3:
            continue

        base_x = float(sorted_g[0].get("x", 10))
        base_w = float(sorted_g[0].get("w", 58))
        base_color = sorted_g[0].get("color", "_border_")
        base_bw = float(sorted_g[0].get("border_width", 0.2) or 0.2)

        first_y = float(sorted_g[0].get("y", 95))
        last_y = float(sorted_g[-1].get("y", 191))

        existing_y = set(float(l.get("y", 0)) for l in sorted_g)

        y = first_y + avg_spacing
        idx = 1
        while y < last_y - 1:
            already = any(abs(ey - y) < 1 for ey in existing_y)
            if not already:
                objects.append({
                    "id": f"ruled_completed_{key}_{idx}",
                    "obj_type": "LINE",
                    "x": base_x, "y": y, "w": base_w, "h": 0,
                    "color": base_color, "border_width": base_bw,
                })
            y += avg_spacing
            idx += 1

    return objects


def _complete_section_titles(objects):
    sections = [o for o in objects if o.get("obj_type") in ("SECTION_TITLE",) or
                (o.get("obj_type") == "TEXT" and o.get("bold") and
                 float(o.get("font_size", 0) or 0) >= 6)]

    if len(sections) < 2:
        return objects

    return objects


def _complete_symmetry(objects):
    rects = [o for o in objects if o.get("obj_type") in ("RECTANGLE", "ROUNDED_RECTANGLE")]
    texts = [o for o in objects if o.get("obj_type") == "TEXT"]

    page_w = 148
    mid_x = page_w / 2

    left_rects = [r for r in rects if float(r.get("x", 0)) < mid_x and
                  float(r.get("x", 0)) + float(r.get("w", 0)) > mid_x - 5]
    right_rects = [r for r in rects if float(r.get("x", 0)) >= mid_x - 5]

    return objects


def _complete_spacing(objects):
    return objects


def _complete_bottom_fill(objects):
    max_y = 0
    for o in objects:
        oy = float(o.get("y", 0)) + float(o.get("h", 0))
        if oy > max_y:
            max_y = oy

    if max_y > 195:
        return objects

    page_number = [o for o in objects if o.get("semantic") == "PAGE_NUMBER"]
    if not page_number:
        objects.append({
            "id": "page_number_completed",
            "obj_type": "TEXT",
            "semantic": "PAGE_NUMBER",
            "value": "1 / 365",
            "x": 60, "y": 203, "w": 28, "h": 5,
            "font_name": "Helvetica", "font_size": 5,
            "color": "_text_", "align": "center",
        })

    return objects

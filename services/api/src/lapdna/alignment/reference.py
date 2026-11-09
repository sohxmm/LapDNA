"""Frozen reference geometry and ordered, approximate source corner annotations."""

from math import hypot

from lapdna.alignment.native import AlignmentError, elapsed_at, linear, support, utc_seconds


def geometry_at(prepared: dict, positions: list[dict], grid: list[float]) -> dict:
    samples = []
    for row in positions:
        try:
            t = utc_seconds(row["date"])
            x, y = float(row["x"]), float(row["y"])
        except (KeyError, TypeError, ValueError):
            continue
        if prepared["start"] - 1 <= t <= prepared["end"] + 1:
            samples.append((t, x, y))
    samples.sort()
    if len(samples) < 3:
        raise AlignmentError("reference position stream is missing")
    times = [row[0] for row in samples]
    x, y = [row[1] for row in samples], [row[2] for row in samples]
    output_x, output_y = [], []
    for distance in grid:
        t = prepared["start"] + elapsed_at(prepared, distance) / 1000
        px, py = linear(times, x, t, max_gap=.75), linear(times, y, t, max_gap=.75)
        output_x.append(px if py is not None else None)
        output_y.append(py if px is not None else None)
    if sum(value is not None for value in output_x) < len(grid) * .99:
        raise AlignmentError("reference position coverage is incomplete")
    # OpenF1 does not document a surveyed metric position scale. Preserve its
    # coordinate frame; distance on the analytical axis comes from speed.
    return {"x": output_x, "y": output_y, "coordinate_unit": "source_units",
            "coordinate_note": "OpenF1 location coordinates retained in their source frame. The map is approximate; the distance axis is integrated speed, not map coordinates."}


def project_markers(raw_markers: dict, grid: list[float], geometry: dict, reference: dict) -> list[dict]:
    markers, previous = [], -1
    for raw in sorted(raw_markers.get("corners", []), key=lambda item: (item["number"], item.get("letter", ""))):
        position = raw["trackPosition"]
        candidates = [(hypot(x - position["x"], y - position["y"]), i)
                      for i, (x, y) in enumerate(zip(geometry["x"], geometry["y"]))
                      if i > previous and x is not None and y is not None]
        if not candidates:
            raise AlignmentError("source corner order cannot be projected")
        error, index = min(candidates)
        if error > 1000:
            raise AlignmentError("source marker and position frames do not agree")
        previous = index
        distance = grid[index]
        # Classification uses a native reference window, never the dense grid.
        windows = [support(reference, distance - 40 + shift, distance + 40 + shift)
                   for shift in (-10, 0, 10)]
        classes = [speed_class(item["minimum"]) if item["count"] >= 3 and item["span_ms"] <= 500.0001
                   else "unknown" for item in windows]
        classification = classes[1] if len(set(classes)) == 1 else "unknown"
        markers.append({"marker_id": f"T{raw['number']}{raw.get('letter', '')}",
                        "number": raw["number"], "label": f"T{raw['number']}{raw.get('letter', '')}",
                        "distance_m": distance, "segment_id": "pending",
                        "reference_speed_kph": windows[1]["minimum"],
                        "speed_class": classification, "projection_error_source_units": error})
    if not 1 <= len(markers) <= 60:
        raise AlignmentError("source turn annotation inventory is empty or exceeds the reviewed bound")
    return markers


def speed_class(speed):
    return "unknown" if speed is None else "low" if speed < 150 else "medium" if speed < 250 else "high"


def monza_regions(markers: list[dict], length: float) -> list[dict]:
    """Versioned editorial windows derived from actual projected marker positions.

    T1–T2, T4–T5 and T8–T10 are inseparable chicane complexes. Bounds are
    deliberately shared for both laps, include approaches/exits, and leave
    complementary straights. This profile must be inspected with its reference.
    """
    groups = [([1, 2], "Rettifilo · T1–T2", 190, 140),
              ([3], "Curva Grande · T3", 125, 180),
              ([4, 5], "Roggia · T4–T5", 185, 140),
              ([6], "Lesmo 1 · T6", 125, 115),
              ([7], "Lesmo 2 · T7", 130, 140),
              ([8, 9, 10], "Ascari · T8–T10", 190, 150),
              ([11], "Parabolica · T11", 195, 180)]
    by_number = {marker["number"]: marker for marker in markers}
    corners = []
    for numbers, label, approach, exit_distance in groups:
        members = [by_number[number] for number in numbers]
        start = max(0., members[0]["distance_m"] - approach)
        end = min(length, members[-1]["distance_m"] + exit_distance)
        classes = {marker["speed_class"] for marker in members}
        classification = "unknown" if "unknown" in classes else "mixed" if len(classes) > 1 else next(iter(classes))
        identifier = "corner_" + "_".join(str(number) for number in numbers)
        for marker in members:
            marker["segment_id"] = identifier
        corners.append({"segment_id": identifier, "kind": "complex" if len(numbers) > 1 else "corner",
                        "label": label, "speed_class": classification, "start_m": start, "end_m": end})
    regions, previous = [], 0.
    for corner in corners:
        if corner["start_m"] < previous:
            raise AlignmentError("Monza corner windows overlap; profile review required")
        if corner["start_m"] > previous:
            regions.append({"segment_id": f"straight_{len(regions)}", "kind": "straight", "label":
                            "Start straight" if not regions else f"Straight to {corner['label'].split(' · ')[0]}",
                            "speed_class": None, "start_m": previous, "end_m": corner["start_m"]})
        regions.append(corner)
        previous = corner["end_m"]
    if previous < length:
        regions.append({"segment_id": "finish_straight", "kind": "straight", "label": "Finish straight",
                        "speed_class": None, "start_m": previous, "end_m": length})
    return regions


def marker_regions(markers: list[dict], length: float) -> list[dict]:
    """Approximate annotation-centred zones, not measured corner boundaries.

    Freeze ±120 m windows on the reference. Merge overlapping windows into
    complexes so neither time nor class support is counted twice. Their
    complement forms straights. A mixed/unsupported complex stays explicit.
    No speed threshold is used to invent braking or pedal data.
    """
    groups = []
    for marker in markers:
        start, end = max(0., marker["distance_m"] - 120), min(length, marker["distance_m"] + 120)
        if groups and start <= groups[-1][1]:
            groups[-1][1] = end
            groups[-1][2].append(marker)
        else:
            groups.append([start, end, [marker]])
    regions, previous = [], 0.
    for start, end, members in groups:
        identifier = "zone_" + "_".join(marker["marker_id"] for marker in members)
        classes = {marker["speed_class"] for marker in members}
        classification = "unknown" if "unknown" in classes else "mixed" if len(classes) > 1 else next(iter(classes))
        if start > previous:
            regions.append({"segment_id": f"straight_{len(regions)}", "kind": "straight",
                            "label": "Straight to " + members[0]["label"], "speed_class": None,
                            "start_m": previous, "end_m": start})
        for marker in members:
            marker["segment_id"] = identifier
        label = members[0]["label"] if len(members) == 1 else members[0]["label"] + "–" + members[-1]["label"]
        regions.append({"segment_id": identifier, "kind": "corner" if len(members) == 1 else "complex",
                        "label": label + " vicinity", "speed_class": classification, "start_m": start, "end_m": end})
        previous = end
    if previous < length:
        regions.append({"segment_id": "finish_straight", "kind": "straight", "label": "Finish straight",
                        "speed_class": None, "start_m": previous, "end_m": length})
    return regions


def canonical_grid(length: float, markers: list[dict], regions: list[dict], sectors: list[float]) -> list[float]:
    values = {0., length, *sectors}
    values.update(float(value) for value in range(0, int(length) + 1, 5))
    values.update(marker["distance_m"] for marker in markers)
    for region in regions:
        values.update((region["start_m"], region["end_m"]))
    return sorted(values)

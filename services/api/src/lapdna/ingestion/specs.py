"""Explicit source identities for offline imports; never guessed from driver names."""

from pathlib import Path
import json
import re


def load_specs(path: Path) -> list[dict]:
    value = json.loads(path.read_text(encoding="utf-8"))
    specs = value["sessions"]
    keys = set()
    for spec in specs:
        key = (spec["year"], spec["round"], spec["session_type"])
        if key in keys or not 2023 <= spec["year"] <= 2026 or spec["session_type"] != "Q":
            raise ValueError("duplicate, unsupported year or unreviewed session format")
        keys.add(key)
        if not re.fullmatch(r"[a-f0-9]{40}", spec["archive_commit"]):
            raise ValueError("archive imports require an immutable commit")
        if not re.fullmatch(r"[a-z0-9_]+", spec["circuit_id"]):
            raise ValueError("invalid circuit identity")
        if not 1 <= spec["turn_count"] <= 40:
            raise ValueError("invalid turn annotation count")
    return specs


def archive_root(spec: dict) -> str:
    from urllib.parse import quote
    return f"https://raw.githubusercontent.com/TracingInsights/{spec['year']}/{spec['archive_commit']}/" + quote(spec["archive_event"], safe="") + "/Qualifying/"

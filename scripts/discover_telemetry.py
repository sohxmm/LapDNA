"""Resolve pinned import candidates; this metadata-only step never enables telemetry."""

import argparse
from hashlib import sha256
import json
from pathlib import Path
import sys
from urllib.parse import quote
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError
import time

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "services/api/src"))
from lapdna.ingestion.openf1 import atomic_json, utc_now

PINS = {2023: "737c84d3ae14b9883a671ca248d015b69cf1cb58",
        2024: "d1543a71370d9b617b627319f8ad80b2f85dfd5e",
        2025: "dfb3ea3f50b69857fe8e40cabe5e899743c59f6a",
        2026: "69450be0e8c27f9aa996ce9e5170693816c4869c"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--years", type=int, nargs="+", default=list(PINS))
    parser.add_argument("--output", type=Path, default=Path("config/telemetry-sessions.json"))
    parser.add_argument("--cache-dir", type=Path, default=Path("work/telemetry-discovery"))
    args = parser.parse_args()

    def fetch(url):
        key = sha256(url.encode()).hexdigest()
        path = args.cache_dir / f"{key}.json"
        if path.exists():
            record = json.loads(path.read_text(encoding="utf-8"))
            if record["url"] == url and sha256(record["body"].encode()).hexdigest() == record["sha256"]:
                return json.loads(record["body"])
        time.sleep(2.05 if "api.openf1.org" in url else .3)
        with urlopen(Request(url, headers={"User-Agent": "LapDNA historical session identity discovery"}), timeout=30) as response:
            raw = response.read(2 * 1024 * 1024 + 1)
        if len(raw) > 2 * 1024 * 1024:
            raise ValueError("discovery metadata exceeded bound")
        body = raw.decode("utf-8")
        atomic_json(path, {"url": url, "sha256": sha256(raw).hexdigest(), "retrieved_at": utc_now(), "body": body})
        return json.loads(body)

    specs, unavailable = [], []
    for year in args.years:
        if year not in PINS:
            parser.error("Only pinned native composite archive years 2023–2026 are supported here; 2018–2022 require the authenticated FastF1 adapter")
        calendar = json.loads(Path(f"services/api/src/lapdna/calendar_snapshots/{year}.json").read_text(encoding="utf-8"))
        sessions = fetch(f"https://api.openf1.org/v1/sessions?year={year}&session_name=Qualifying")
        by_key = {row["session_key"]: row for row in sessions}
        for race in calendar["races"]:
            event = race["name"]
            try:
                url = f"https://raw.githubusercontent.com/TracingInsights/{year}/{PINS[year]}/" + quote(event, safe="") + "/Qualifying/session_info.json"
                info = fetch(url)["session_info"]
                native = by_key[info["Key"]]
                if native["meeting_key"] != info["Meeting"]["Key"] or native["year"] != year or native.get("is_cancelled") is not False:
                    raise ValueError("archive/native meeting identity mismatch or source cancellation is unknown")
                markers = fetch(f"https://api.multiviewer.app/api/v1/circuits/{native['circuit_key']}/{year}")
                numbers = sorted({item["number"] for item in markers["corners"]})
                if not numbers or numbers != list(range(1, max(numbers) + 1)):
                    raise ValueError("source turn annotation inventory is incomplete")
                spec = {key: native[key] for key in ("year", "session_key", "meeting_key", "circuit_key", "circuit_short_name")}
                spec.update(round=race["round"], session_type="Q", circuit_id=race["circuit_id"], event_name=event,
                            qualifying_date=native["date_start"][:10], archive_event=event, archive_commit=PINS[year],
                            archive_session_path=info["Path"], turn_count=max(numbers),
                            profile="monza-v1" if race["circuit_id"] == "monza" else "marker-windows-v1")
                specs.append(spec)
                print(f"Candidate {year} R{race['round']:02}: {event}", flush=True)
            except (HTTPError, URLError, TimeoutError, KeyError, ValueError) as exc:
                unavailable.append({"year": year, "round": race["round"], "event_name": event, "reason": str(exc)[:300]})
                print(f"No candidate {year} R{race['round']:02}: {exc}", flush=True)
    atomic_json(args.output, {"schema_version": "1.0.0", "scope": "Import candidates only; session/channel availability is established by actual native import and publication gates", "archive_pins": {str(year): PINS[year] for year in args.years}, "sessions": specs, "unresolved": unavailable})
    print(f"Resolved {len(specs)} candidates; {len(unavailable)} unresolved. No telemetry was published.")


if __name__ == "__main__":
    main()

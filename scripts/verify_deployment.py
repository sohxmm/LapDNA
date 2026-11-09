"""Check real hosted session identity, comparisons, reversals and exact links."""

import argparse
from collections import Counter
from datetime import datetime, timezone
import json
from pathlib import Path
from time import perf_counter
from urllib.request import Request, urlopen


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", default="https://lapdna.vercel.app")
    parser.add_argument("--output", type=Path, default=Path("work/deployment-checks.json"))
    parser.add_argument("--expected-publication", type=Path)
    args = parser.parse_args()
    base = args.base_url.rstrip("/")
    def call(path, body=None):
        request = Request(base + "/api/v1/" + path,
            data=json.dumps(body).encode() if body else None,
            headers={"Content-Type":"application/json", "Accept":"application/json"})
        start = perf_counter()
        with urlopen(request, timeout=30) as response:
            raw = response.read(8 * 1024 * 1024 + 1)
        if len(raw) > 8 * 1024 * 1024:
            raise ValueError("Hosted response exceeds check bound")
        return json.loads(raw), round((perf_counter() - start) * 1000, 1)
    health, _ = call("health")
    inventory, _ = call("sessions")
    assert inventory["schema_version"] == "1.4.0"
    if args.expected_publication:
        expected = json.loads(args.expected_publication.read_text(encoding="utf-8"))
        assert {row["session"]["session_id"] for row in inventory["sessions"]} == set(expected["sessions"]), "Hosted catalogue differs from the audited frozen release"
    checks = []
    cases = [("2024-16-monza-Q","NOR","RUS","Q3","telemetry"),
             ("2018-14-monza-Q","RAI","VET","Q3","telemetry"),
             ("2019-11-hockenheimring-Q","HAM","VER","Q3",None),
             ("2019-6-monaco-Q","HAM","BOT","Q3",None),
             ("2024-6-miami-SQ","VER","LEC","SQ3","telemetry"),
             ("2026-19-rodriguez-Q","HAM","LEC","Q3","sector_only")]
    for session, driver_a, driver_b, phase, tier in cases:
        index, _ = call(f"sessions/{session}/laps")
        selected = []
        for driver in (driver_a,driver_b):
            laps = [lap for lap in index["laps"] if lap["driver_code"] == driver and lap["phase"] == phase and lap["capability"] != "unavailable"]
            selected.append(min(laps, key=lambda lap:(lap["lap_time_ms"],lap["lap_number"])))
        a,b = selected
        request = {"session_id":session,"lap_a_id":a["lap_id"],"lap_b_id":b["lap_id"],"detail_level":"auto"}
        result, cold = call("compare", request)
        artifact = result["artifact"]
        if tier: assert artifact["detail_level"] == tier
        aa,bb = (artifact["lap_b"],artifact["lap_a"]) if result["swapped"] else (artifact["lap_a"],artifact["lap_b"])
        assert aa["lap_id"] == a["lap_id"] and bb["lap_id"] == b["lap_id"]
        assert aa["team_colour"] == a["team_colour"] and bb["team_colour"] == b["team_colour"]
        assert aa["lap_time_ms"] == a["lap_time_ms"] and bb["sector_times_ms"] == b["sector_times_ms"]
        reverse, warm = call("compare",{**request,"lap_a_id":b["lap_id"],"lap_b_id":a["lap_id"]})
        assert reverse["artifact"] == artifact and reverse["swapped"] != result["swapped"]
        exact, _ = call("comparisons/" + artifact["comparison_id"])
        assert exact == artifact
        if artifact["detail_level"] == "sector_only":
            assert not any(key in artifact for key in ("distance_m","channels_a","geometry","corners"))
        if session == "2026-19-rodriguez-Q":
            assert b["lap_time_ms"] - a["lap_time_ms"] == 119
        checks.append({"session_id":session,"comparison_id":artifact["comparison_id"],"detail_level":artifact["detail_level"],
                       "source_snapshot_sha256":index["source_snapshot_sha256"],"cold_request_ms":cold,"reverse_request_ms":warm})
        print(f"Verified {session}: {artifact['detail_level']}, first request {cold} ms", flush=True)
    australia, _ = call("sessions/2024-3-albert_park-Q/laps")
    assert len(australia["drivers"]) == 19 and not any(driver["driver_code"] == "SAR" for driver in australia["drivers"])
    output = {"checked_at":datetime.now(timezone.utc).isoformat(),"base_url":base,"health":health,
              "sessions":len(inventory["sessions"]),"sessions_by_year":dict(Counter(str(row["session"]["year"]) for row in inventory["sessions"])),
              "checks":checks,"withdrawn_driver_roster_check":"Australia 2024: 19 actual source drivers; no invented SAR entry"}
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(output,indent=2),encoding="utf-8")
    print(json.dumps({key:value for key,value in output.items() if key != "checks"}),flush=True)


if __name__ == "__main__":
    main()

import importlib.util
import json
from pathlib import Path

spec = importlib.util.spec_from_file_location("native_import_operator",Path(__file__).resolve().parents[3] / "scripts/import_fastf1.py")
operator = importlib.util.module_from_spec(spec)
spec.loader.exec_module(operator)


def test_targeted_retry_preserves_other_rounds_and_remembers_prior_success(tmp_path):
    path=tmp_path / "report.json"
    first={"year":2019,"round":1,"status":"published","telemetry_laps":100}
    second={"year":2019,"round":2,"status":"published","telemetry_laps":80}
    operator.record_attempt(path,first)
    operator.record_attempt(path,second)
    operator.record_attempt(path,{"year":2019,"round":1,"session_type":"Q","status":"unavailable","code":"rate_limited"})
    rows=json.loads(path.read_text())["results"]
    assert len(rows)==2 and rows[1]==second
    assert rows[0]["last_success"]==first and rows[0]["code"]=="rate_limited"
    operator.record_attempt(path,{**first,"telemetry_laps":101})
    rows=json.loads(path.read_text())["results"]
    assert rows[0]["telemetry_laps"]==101 and "last_success" not in rows[0]

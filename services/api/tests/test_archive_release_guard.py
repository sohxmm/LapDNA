import importlib.util
from pathlib import Path

import pytest

spec=importlib.util.spec_from_file_location("archive_release",Path(__file__).resolve().parents[3] / "scripts/complete_archive.py")
release=importlib.util.module_from_spec(spec)
spec.loader.exec_module(release)


def test_background_release_stops_if_reviewed_source_changes(monkeypatch):
    monkeypatch.setattr(release,"head",lambda:"reviewed")
    monkeypatch.setattr(release.subprocess,"check_output",lambda *a,**k:"")
    release.require_unchanged("reviewed")
    with pytest.raises(ValueError,match="Source changed"):
        release.require_unchanged("other")
    monkeypatch.setattr(release.subprocess,"check_output",lambda *a,**k:" M apps/web/src/App.tsx")
    with pytest.raises(ValueError,match="clean checkpoint"):
        release.require_unchanged("reviewed")


def test_partial_release_uses_audited_success_and_counts_unattempted_candidates():
    expected={(2022,1,"Q"):{"year":2022,"round":1,"session_type":"Q","event_name":"Bahrain"},
              (2022,2,"Q"):{"year":2022,"round":2,"session_type":"Q","event_name":"Saudi Arabia"}}
    coverage={"sessions":[{"year":2022,"round":1,"session_id":"2022-1-bahrain-Q"}]}
    attempts={"results":{"2022-1-Q":{"status":"unavailable","code":"old_failure"}}}
    missing=release.remaining_candidates(expected,coverage,attempts)
    assert len(missing)==1 and missing[0]["round"]==2 and missing[0]["code"]=="not_attempted"

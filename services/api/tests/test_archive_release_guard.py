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

"""A long source rate limit must stop safely instead of retrying prematurely."""
import importlib.util
from pathlib import Path
from urllib.error import HTTPError

import pytest

spec = importlib.util.spec_from_file_location("classification_fetch", Path(__file__).resolve().parents[3] / "scripts/import_classifications.py")
fetch = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fetch)


def test_long_retry_after_preserves_progress_and_stops_without_hammering_source(tmp_path, monkeypatch):
    calls, sleeps = [], []
    def limited(*args, **kwargs):
        calls.append(1)
        raise HTTPError("https://example.invalid/results", 429, "Rate limit", {"Retry-After": "3600"}, None)
    monkeypatch.setattr(fetch, "urlopen", limited)
    monkeypatch.setattr(fetch.time, "sleep", sleeps.append)
    importer = fetch.Fetcher(tmp_path)
    with pytest.raises(RuntimeError, match="Retry-After"):
        importer.get("one.json", "https://example.invalid/results")
    assert calls == [1] and sleeps == []

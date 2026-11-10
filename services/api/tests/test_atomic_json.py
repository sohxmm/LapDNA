import json
from pathlib import Path

import pytest

from lapdna.ingestion.openf1 import atomic_json


def test_transient_replace_lock_preserves_previous_receipt_until_success(tmp_path, monkeypatch):
    target = tmp_path / "receipt.json"
    target.write_text('{"revision":1}')
    original = Path.replace
    attempts = []

    def replace(source, destination):
        attempts.append(source)
        assert source.parent == target.parent
        assert json.loads(source.read_text()) == {"revision": 2}
        if len(attempts) < 3:
            assert json.loads(target.read_text()) == {"revision": 1}
            raise PermissionError("destination temporarily locked")
        return original(source, destination)

    monkeypatch.setattr(Path, "replace", replace)
    monkeypatch.setattr("lapdna.ingestion.openf1.time.sleep", lambda _: None)
    atomic_json(target, {"revision": 2})
    assert len(attempts) == 3
    assert json.loads(target.read_text()) == {"revision": 2}
    assert list(tmp_path.glob("*.tmp")) == []


def test_permanent_replace_failure_is_bounded_and_keeps_previous_receipt(tmp_path, monkeypatch):
    target = tmp_path / "receipt.json"
    target.write_text('{"revision":1}')
    attempts = []

    def fail(*args):
        attempts.append(1)
        raise PermissionError("locked")

    monkeypatch.setattr(Path, "replace", fail)
    monkeypatch.setattr("lapdna.ingestion.openf1.time.sleep", lambda _: None)
    with pytest.raises(PermissionError):
        atomic_json(target, {"revision": 2})
    assert len(attempts) == 7
    assert json.loads(target.read_text()) == {"revision": 1}
    assert list(tmp_path.glob("*.tmp")) == []


def test_invalid_numeric_json_never_replaces_existing_receipt(tmp_path):
    target = tmp_path / "receipt.json"
    target.write_text('{"revision":1}')
    with pytest.raises(ValueError):
        atomic_json(target, {"value": float("nan")})
    assert json.loads(target.read_text()) == {"revision": 1}
    assert list(tmp_path.glob("*.tmp")) == []

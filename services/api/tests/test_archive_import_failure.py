import importlib.util
import json
from pathlib import Path
import sys

spec=importlib.util.spec_from_file_location("archive_import",Path(__file__).resolve().parents[3] / "scripts/import_archive.py")
archive=importlib.util.module_from_spec(spec)
spec.loader.exec_module(archive)


def test_unexpected_parser_error_is_not_reported_as_a_completed_source_pass(tmp_path,monkeypatch):
    report=tmp_path / "attempts.json"
    monkeypatch.setattr(sys,"argv",["import_archive.py","--years","2022","--report",str(report)])
    def failed(*args,**kwargs): raise RuntimeError("private exception detail")
    monkeypatch.setattr(archive,"import_fastf1_session",failed)
    assert archive.main()==3
    output=report.read_text()
    assert "private exception detail" not in output
    assert json.loads(output)["results"]["2022-1-Q"]["code"]=="unexpected_import_error"

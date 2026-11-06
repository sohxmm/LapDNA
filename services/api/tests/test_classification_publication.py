"""Calendar identity and complete-archive gates for the publication command."""
import importlib.util
import json
from pathlib import Path

import pytest

spec = importlib.util.spec_from_file_location("classification_publication", Path(__file__).resolve().parents[3] / "scripts/publish_classifications.py")
publication = importlib.util.module_from_spec(spec)
spec.loader.exec_module(publication)


def test_sprint_matches_the_actual_country_and_weekend_not_session_index():
    session = {"session_key": 999, "year": 2024, "country_name": "United States", "date_start": "2024-05-03T20:00:00+00:00"}
    race = {"season": "2024", "round": "6", "date": "2024-05-05", "Circuit": {"Location": {"country": "USA"}}}
    another = {**race, "round": "19", "date": "2024-10-20"}
    assert publication.match_sprint_event(session, [another, race])["round"] == "6"


def test_ambiguous_or_wrong_country_calendar_match_fails_instead_of_guessing():
    session = {"session_key": 999, "year": 2024, "country_name": "United States", "date_start": "2024-05-03T20:00:00+00:00"}
    race = {"season": "2024", "round": "6", "date": "2024-05-05", "Circuit": {"Location": {"country": "USA"}}}
    with pytest.raises(ValueError, match="uniquely"):
        publication.match_sprint_event(session, [race, {**race, "round": "7"}])
    with pytest.raises(ValueError, match="uniquely"):
        publication.match_sprint_event({**session, "country_name": "Canada"}, [race])


def test_partial_source_archive_is_rejected_before_any_publication(tmp_path):
    (tmp_path / "jolpica-qualifying.json").write_text(json.dumps({"actual_records": 0, "payload": {"MRData": {
        "total": "1", "RaceTable": {"Races": []}}}}), encoding="utf-8")
    destination = tmp_path / "published"
    with pytest.raises(ValueError, match="incomplete"):
        publication.build_publication(tmp_path, destination)
    assert not destination.exists()

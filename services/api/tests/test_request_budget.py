from pathlib import Path

import pytest

from lapdna.ingestion.budget import RequestBudget
from lapdna.ingestion.openf1 import ImportFailure


def test_request_window_survives_new_operator_instance_and_expires(tmp_path):
    now = [100.]
    first = RequestBudget(tmp_path, limit=2, window=10., clock=lambda:now[0])
    first.initialize([99.])
    first.record()
    second = RequestBudget(tmp_path, limit=2, window=10., clock=lambda:now[0])
    assert second.status() == (2, 9.)
    with pytest.raises(ImportFailure) as error:
        second.record()
    assert error.value.code == "rate_limited"
    now[0] = 110.
    second.record()
    assert first.status() == (1, 0.)

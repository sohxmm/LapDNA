"""Persistent operator request budget, including independent local import jobs.

The pinned library's own rate limits remain enabled. This stricter ledger
prevents restarting an operator process from resetting the project's window.
Only UTC attempt timestamps are stored, never URLs, tokens or account details.
"""

import json
from pathlib import Path
import time

from lapdna.analysis.publication import activation_lock
from .openf1 import ImportFailure, atomic_json


class RequestBudget:
    def __init__(self, directory: Path, *, limit=450, window=3600., clock=time.time):
        self.directory, self.limit, self.window, self.clock = directory, limit, window, clock

    def initialize(self, timestamps=()):
        with activation_lock(self.directory):
            path = self.directory / "attempts.json"
            if not path.exists():
                now = self.clock()
                atomic_json(path, {"attempts": sorted(value for value in timestamps if now - self.window < value <= now), "limit": self.limit, "window_seconds": self.window})

    def status(self):
        path = self.directory / "attempts.json"
        with activation_lock(self.directory):
            values = json.loads(path.read_text(encoding="utf-8"))["attempts"] if path.exists() else []
            now = self.clock()
            recent = sorted(value for value in values if value > now - self.window)
            wait = max(0., recent[-self.limit] + self.window - now) if len(recent) >= self.limit else 0.
            return len(recent), wait

    def record(self):
        with activation_lock(self.directory):
            path = self.directory / "attempts.json"
            values = json.loads(path.read_text(encoding="utf-8"))["attempts"] if path.exists() else []
            now = self.clock()
            recent = sorted(value for value in values if value > now - self.window)
            if len(recent) >= self.limit:
                raise ImportFailure("rate_limited", "The shared historical import window is full; cached progress is retained until the source window resets")
            recent.append(now)
            atomic_json(path, {"attempts": recent, "limit": self.limit, "window_seconds": self.window})


def install_fastf1_budget(root=Path("work/fastf1")):
    """Count actual non-cached sends; preserve the original library limiter."""
    from fastf1.req import _SessionWithRateLimiting
    current = _SessionWithRateLimiting.send
    if getattr(current, "_lapdna_budget", None) is not None:
        return current._lapdna_budget
    budget = RequestBudget(root / "request-budget")
    if not (budget.directory / "attempts.json").exists():
        # These are this project's own locally generated HTTP caches. Read
        # only response creation times; no request/header data is exported.
        from requests_cache import CachedSession
        timestamps = []
        for path in root.glob("*/library/*.sqlite"):
            with CachedSession(cache_name=str(path.with_suffix(""))) as session:
                for response in session.cache.responses.values():
                    if response is not None and response.created_at is not None:
                        timestamps.append(response.created_at.timestamp())
        budget.initialize(timestamps)

    def send(self, request, **kwargs):
        budget.record()
        return current(self, request, **kwargs)
    send._lapdna_budget = budget
    _SessionWithRateLimiting.send = send
    return budget

"""Artificial transport responses verify the artifact boundary without network."""

from hashlib import sha256
from io import BytesIO
import json
from urllib.error import URLError

import pytest

from lapdna.analysis.remote import read_normalized
from lapdna.store import InvalidArtifact


class Opener:
    def __init__(self, raw): self.raw, self.calls = raw, 0
    def open(self, request, timeout):
        self.calls += 1
        assert request.full_url.startswith("https://example.public.blob.vercel-storage.com/telemetry/")
        assert len(request.full_url.rsplit("/",1)[1]) == 72
        assert timeout == 15
        return BytesIO(self.raw)


def origin(directory, base="https://example.public.blob.vercel-storage.com/telemetry"):
    (directory / "remote.json").write_text(json.dumps({"base_url":base}))


def test_pinned_artifact_is_cached_and_corrupt_cache_is_repaired(tmp_path):
    origin(tmp_path)
    raw = b"artificial-compressed-artifact"
    digest = sha256(raw).hexdigest()
    opener = Opener(raw)
    cache = tmp_path / "cache"
    for _ in range(2):
        assert read_normalized(tmp_path, "normalized/test.json.gz", digest, cache_dir=cache, opener=opener) == raw
    assert opener.calls == 1
    (cache / f"{digest}.gz").write_bytes(b"corrupt")
    assert read_normalized(tmp_path, "normalized/test.json.gz", digest, cache_dir=cache, opener=opener) == raw
    assert opener.calls == 2


@pytest.mark.parametrize("base", ["http://example.public.blob.vercel-storage.com/telemetry", "https://evil.invalid/telemetry", "https://example.public.blob.vercel-storage.com/telemetry?redirect=1"])
def test_untrusted_origin_rejects_without_transport(tmp_path, base):
    origin(tmp_path, base)
    with pytest.raises(InvalidArtifact):
        read_normalized(tmp_path, "normalized/test.json.gz", "0" * 64, opener=Opener(b""))


def test_wrong_digest_never_populates_cache(tmp_path):
    origin(tmp_path)
    with pytest.raises(InvalidArtifact, match="digest"):
        read_normalized(tmp_path, "normalized/test.json.gz", "0" * 64, cache_dir=tmp_path / "cache", opener=Opener(b"wrong"))
    assert not list((tmp_path / "cache").glob("*.gz"))


def test_transport_failure_is_a_clear_unavailable_result(tmp_path):
    origin(tmp_path)
    class Unavailable:
        def open(self, *args, **kwargs): raise URLError("network unavailable")
    with pytest.raises(InvalidArtifact, match="temporarily unavailable"):
        read_normalized(tmp_path, "normalized/test.json.gz", "0" * 64, cache_dir=tmp_path / "cache", opener=Unavailable())

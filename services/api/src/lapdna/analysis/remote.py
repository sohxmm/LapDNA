"""Read immutable, hash-pinned normalized publications from the release store.

Only this project's public Vercel Blob origin is allowed. This downloads an
already normalized artifact, never upstream telemetry or account credentials.
"""

from hashlib import sha256
import json
from pathlib import Path
import re
from tempfile import gettempdir
from urllib.error import HTTPError
from urllib.parse import urlsplit
from urllib.request import build_opener, HTTPRedirectHandler, Request

from lapdna.store import InvalidArtifact, MAX_ARTIFACT_BYTES


class SameOriginRedirect(HTTPRedirectHandler):
    def redirect_request(self, request, fp, code, msg, headers, newurl):
        if urlsplit(newurl).scheme != "https" or urlsplit(newurl).netloc != urlsplit(request.full_url).netloc:
            raise HTTPError(request.full_url, code, "Artifact redirect left the release origin", headers, fp)
        return super().redirect_request(request, fp, code, msg, headers, newurl)


def read_normalized(directory: Path, relative: str, expected: str, *, cache_dir=None, opener=None):
    path = directory / relative
    if not re.fullmatch(r"normalized/[A-Za-z0-9_-]+\.json\.gz", relative) or not re.fullmatch(r"[a-f0-9]{64}", expected):
        raise InvalidArtifact("invalid normalized artifact reference")
    if path.exists():
        if path.stat().st_size > MAX_ARTIFACT_BYTES:
            raise InvalidArtifact("compressed publication exceeds size limit")
        return path.read_bytes()
    config = directory / "remote.json"
    if not config.exists():
        raise FileNotFoundError(path)
    if config.stat().st_size > 4096:
        raise InvalidArtifact("release origin configuration exceeds bound")
    base = json.loads(config.read_text(encoding="utf-8"))["base_url"]
    if not re.fullmatch(r"https://[a-z0-9]+\.public\.blob\.vercel-storage\.com/telemetry", base):
        raise InvalidArtifact("untrusted release artifact origin")
    cache = Path(cache_dir or Path(gettempdir()) / "lapdna-normalized-v1")
    cache.mkdir(parents=True, exist_ok=True)
    cached = cache / f"{expected}.gz"
    if cached.is_file() and cached.stat().st_size <= MAX_ARTIFACT_BYTES:
        raw = cached.read_bytes()
        if sha256(raw).hexdigest() == expected:
            cached.touch()
            return raw
    request = Request(base + "/" + expected + ".json.gz", headers={"User-Agent":"LapDNA normalized release reader", "Accept-Encoding":"identity"})
    try:
        with (opener or build_opener(SameOriginRedirect())).open(request, timeout=15) as response:
            raw = response.read(MAX_ARTIFACT_BYTES + 1)
    except OSError as exc:
        raise InvalidArtifact("verified release artifact is temporarily unavailable") from exc
    if len(raw) > MAX_ARTIFACT_BYTES or sha256(raw).hexdigest() != expected:
        raise InvalidArtifact("remote publication digest or size mismatch")
    # The process's publication lock serializes reads. Other processes may
    # share a temp directory, so use a unique temporary pathname and atomic write.
    from uuid import uuid4
    temporary = cache / f"{expected}-{uuid4().hex}.tmp"
    temporary.write_bytes(raw)
    temporary.replace(cached)
    # At most eight compressed artifacts remain in this disposable cache.
    for old in sorted(cache.glob("*.gz"), key=lambda p:p.stat().st_mtime, reverse=True)[8:]:
        try:
            old.unlink()
        except FileNotFoundError:
            pass
    return raw

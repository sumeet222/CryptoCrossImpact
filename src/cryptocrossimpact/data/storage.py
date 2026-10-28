"""Bounded public HTTP, fingerprints, atomic writes, incremental disk guard."""
import hashlib
import json
import shutil
import time
import warnings
from datetime import datetime, timezone
from pathlib import Path
from zipfile import ZipFile

import pandas as pd
import requests


def utcnow():
    return datetime.now(timezone.utc).isoformat()


def sha256(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def write_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(json.dumps(value, indent=2, allow_nan=False) + "\n")
    temp.replace(path)


def write_parquet(path, frame):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(".parquet.tmp")
    try:
        frame.to_parquet(temp, index=False, compression="zstd")
        loaded = pd.read_parquet(temp)
        pd.testing.assert_frame_equal(frame.reset_index(drop=True), loaded, check_exact=True)
        temp.replace(path)
    finally:
        temp.unlink(missing_ok=True)


class SourceError(RuntimeError):
    def __init__(self, status, message):
        self.status = status
        super().__init__(message)


class PublicSource:
    def __init__(self, root, config):
        self.root, self.config = Path(root), config
        self.session = requests.Session()
        self.session.headers["User-Agent"] = "CryptoCrossImpact/Stage1 noncommercial academic research"
        self.peak_bytes = 0

    def guard(self, reserve=0):
        # Include the existing environment's new dependencies and all project data.
        usage = sum(p.stat().st_size for p in self.root.rglob("*") if p.is_file() and not p.is_symlink())
        self.peak_bytes = max(self.peak_bytes, usage)
        incremental = max(0, usage - self.config["resources"]["initial_bytes"])
        limits = self.config["resources"]
        if incremental + reserve >= limits["stop_bytes"]:
            raise SourceError("STORAGE_HOLD", "Would exceed 30 GB incremental storage; approval required")
        if incremental + reserve >= limits["warn_bytes"]:
            warnings.warn("Approaching 25 GB incremental storage", stacklevel=2)
        if shutil.disk_usage(self.root).free < reserve + 1_000_000_000:
            raise SourceError("STORAGE_HOLD", "Insufficient free disk including 1 GB safety reserve")
        return usage

    def request(self, method, url, **kwargs):
        attempts = self.config["http"]["attempts"]
        for attempt in range(attempts):
            try:
                response = self.session.request(method, url,
                    timeout=self.config["http"]["timeout_seconds"], **kwargs)
                if response.status_code in (401, 403, 451):
                    response.close()
                    raise SourceError("ACCESS_BLOCKED", f"HTTP {response.status_code}: {url}")
                if response.status_code == 404:
                    response.close()
                    raise SourceError("MISSING_SOURCE", f"HTTP 404: {url}")
                if response.status_code == 429:
                    response.close()
                    # Do not work around provider rate limits or retry aggressively.
                    raise SourceError("RATE_LIMITED", f"HTTP 429: {url}; resume later")
                if response.status_code >= 500:
                    response.close()
                    if attempt + 1 < attempts:
                        time.sleep(2 ** attempt)
                        continue
                response.raise_for_status()
                return response
            except requests.RequestException as error:
                if attempt + 1 == attempts:
                    raise SourceError("NETWORK_ERROR", f"{type(error).__name__}: {url}") from error
                time.sleep(2 ** attempt)
        raise SourceError("HTTP_ERROR", url)

    def checksum(self, url):
        try:
            with self.request("GET", url + ".CHECKSUM") as response:
                tokens = response.text.strip().split()
                if len(tokens) != 2 or len(tokens[0]) != 64 or tokens[1].lstrip("*") != url.rsplit("/", 1)[-1]:
                    raise SourceError("CHECKSUM_ERROR", "Malformed checksum or wrong archive name")
                int(tokens[0], 16)
                return tokens[0].lower(), response.text
        except SourceError as error:
            if error.status == "MISSING_SOURCE":
                return None, None
            raise

    def archive(self, url, known=None):
        """Recheck published hash on resume. Preserve changed sources for review."""
        expected, checksum_text = self.checksum(url)
        if known and known.get("vendor_sha256") != expected:
            raise SourceError("UPSTREAM_CHANGED", f"Published checksum changed: {url}")
        path = self.root / "data/raw" / url.rsplit("/", 1)[-1]
        created = not path.exists()
        headers = {}
        if created:
            path.parent.mkdir(parents=True, exist_ok=True)
            temp = path.with_suffix(".zip.part")
            try:
                with self.request("GET", url, stream=True) as response:
                    size = int(response.headers.get("Content-Length", 0))
                    if size > self.config["resources"]["max_archive_bytes"]:
                        raise SourceError("SIZE_HOLD", f"Archive unexpectedly large: {size} bytes")
                    self.guard(size + 50_000_000)
                    headers = {k: response.headers[k] for k in ("ETag", "Last-Modified", "Content-Length") if k in response.headers}
                    total = 0
                    with temp.open("wb") as output:
                        for block in response.iter_content(1024 * 1024):
                            total += len(block)
                            if total > self.config["resources"]["max_archive_bytes"]:
                                raise SourceError("SIZE_HOLD", "Streaming size limit exceeded")
                            output.write(block)
                if size and total != size:
                    raise SourceError("CORRUPT", "Truncated download")
                if expected and sha256(temp) != expected:
                    raise SourceError("CHECKSUM_ERROR", "SHA-256 mismatch")
                with ZipFile(temp) as archive:
                    uncompressed = sum(x.file_size for x in archive.infolist())
                    if uncompressed > self.config["resources"]["max_uncompressed_bytes"]:
                        raise SourceError("SIZE_HOLD", "ZIP expansion exceeds streaming resource ceiling")
                    if archive.testzip() is not None:
                        raise SourceError("CORRUPT", "ZIP CRC mismatch")
                temp.replace(path)
            finally:
                temp.unlink(missing_ok=True)
        fingerprint = sha256(path)
        if expected and fingerprint != expected:
            raise SourceError("CHECKSUM_ERROR", f"Cached ZIP differs from vendor: {path.name}")
        if known and fingerprint != known["sha256"]:
            raise SourceError("UPSTREAM_CHANGED", f"Source content changed: {path.name}")
        if not created and (not known or not known.get("http_metadata")):
            with self.request("HEAD", url) as response:
                headers = {k: response.headers[k] for k in ("ETag", "Last-Modified", "Content-Length") if k in response.headers}
        with ZipFile(path) as archive:
            uncompressed = sum(x.file_size for x in archive.infolist())
            if uncompressed > self.config["resources"]["max_uncompressed_bytes"]:
                raise SourceError("SIZE_HOLD", "ZIP expansion limit")
            if archive.testzip() is not None:
                raise SourceError("CORRUPT", "ZIP CRC mismatch")
        if checksum_text:
            path.with_suffix(".zip.CHECKSUM").write_text(checksum_text)
        self.guard()  # capture retained + current ZIP before an optional audit removes it
        return path, dict(url=url, retrieved_at_utc=utcnow(), sha256=fingerprint,
                          vendor_sha256=expected, checksum_status="PASS" if expected else "UNAVAILABLE",
                          bytes=path.stat().st_size, uncompressed_bytes=uncompressed,
                          http_metadata=headers, local_archive=str(path.relative_to(self.root)),
                          created_this_call=created)

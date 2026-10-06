"""Windows-user-bound, authenticated recovery envelope for test archives only."""

import ctypes
from ctypes import wintypes
import hashlib
import json
import os
from pathlib import Path
import struct
import tempfile

MAGIC = b"MYGYM-RECOVERY-1\n"
MAX_BYTES = 64 * 1024 * 1024


class ArchiveError(ValueError):
    pass


class Blob(ctypes.Structure):
    _fields_ = [("size", wintypes.DWORD), ("data", ctypes.POINTER(ctypes.c_ubyte))]


def _dpapi(data, decrypt=False):
    if os.name != "nt":
        raise ArchiveError("This rehearsal requires Windows user protection.")
    crypt = ctypes.WinDLL("crypt32", use_last_error=True)
    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel.LocalFree.argtypes = [ctypes.c_void_p]
    kernel.LocalFree.restype = ctypes.c_void_p
    buffer = ctypes.create_string_buffer(data)
    source = Blob(len(data), ctypes.cast(buffer, ctypes.POINTER(ctypes.c_ubyte)))
    result = Blob()
    function = crypt.CryptUnprotectData if decrypt else crypt.CryptProtectData
    function.argtypes = [
        ctypes.POINTER(Blob),
        ctypes.c_void_p,
        ctypes.c_void_p,
        ctypes.c_void_p,
        ctypes.c_void_p,
        wintypes.DWORD,
        ctypes.POINTER(Blob),
    ]
    function.restype = wintypes.BOOL
    # UI forbidden; never LOCAL_MACHINE (which would allow every Windows user).
    if not function(
        ctypes.byref(source), None, None, None, None, 1, ctypes.byref(result)
    ):
        raise ArchiveError(
            "Archive protection failed: wrong Windows identity or damaged file."
        )
    try:
        return ctypes.string_at(result.data, result.size)
    finally:
        kernel.LocalFree(result.data)


def _validate(metadata, dump):
    if metadata.get("format") != 1 or metadata.get("postgres_major") != 17:
        raise ArchiveError("Unsupported envelope or PostgreSQL version.")
    if (
        metadata.get("source") != "mygym_test"
        or metadata.get("scope") != "fixture-rehearsal"
    ):
        raise ArchiveError("Only the isolated test database is admitted.")
    if not dump.startswith(b"PGDMP") or len(dump) > MAX_BYTES:
        raise ArchiveError("Expected a bounded PostgreSQL custom archive.")
    if metadata.get("digest") != hashlib.sha256(dump).hexdigest():
        raise ArchiveError("Archive integrity check failed.")


def seal_archive(path, dump, *, source, postgres_major):
    metadata = {
        "format": 1,
        "postgres_major": postgres_major,
        "source": source,
        "scope": "fixture-rehearsal",
        "digest": hashlib.sha256(dump).hexdigest(),
    }
    _validate(metadata, dump)
    header = json.dumps(metadata, separators=(",", ":")).encode("utf-8")
    encrypted = _dpapi(struct.pack("!I", len(header)) + header + dump)
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(
            dir=path.parent, prefix=".recovery-", delete=False
        ) as handle:
            temporary = Path(handle.name)
            handle.write(MAGIC + encrypted)
            handle.flush()
            os.fsync(handle.fileno())
        # Atomic publication fails if destination exists; only ciphertext touches disk.
        os.link(temporary, path)
    except OSError:
        raise ArchiveError(
            "Cannot publish archive; destination must be new on a local NTFS volume."
        ) from None
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def open_archive(path):
    try:
        with Path(path).open("rb") as handle:
            envelope = handle.read(MAX_BYTES + 8193)
        if len(envelope) > MAX_BYTES + 8192 or not envelope.startswith(MAGIC):
            raise ArchiveError("Unsupported or oversized recovery envelope.")
        payload = _dpapi(envelope[len(MAGIC) :], decrypt=True)
        if len(payload) < 4:
            raise ArchiveError("Truncated recovery envelope.")
        header_size = struct.unpack("!I", payload[:4])[0]
        if not 0 < header_size <= 4096:
            raise ArchiveError("Invalid recovery metadata.")
        metadata = json.loads(payload[4 : 4 + header_size])
        if not isinstance(metadata, dict):
            raise ArchiveError("Invalid recovery metadata.")
        dump = payload[4 + header_size :]
        _validate(metadata, dump)
        return dump
    except (OSError, ValueError, struct.error):
        raise ArchiveError(
            "Cannot open recovery archive: protection, version or integrity failure."
        ) from None

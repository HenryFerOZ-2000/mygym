"""Download a pinned official PostgreSQL Windows archive and extract its runtime."""

import hashlib
from pathlib import Path
import urllib.request
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[1]
ARCHIVE = ROOT / ".local/postgresql.zip"
DESTINATION = (ROOT / ".local/pg17").resolve()
URL = "https://get.enterprisedb.com/postgresql/postgresql-17.11-4-windows-x64-binaries.zip"
SHA256 = "b9424ee7bc60b52450ff910a3630225df32e633f3cb29c1d126d9299d59aea28"


def main():
    ARCHIVE.parent.mkdir(exist_ok=True)
    if not ARCHIVE.exists():
        temporary = ARCHIVE.with_suffix(".download")
        print("Downloading PostgreSQL 17.11 from EDB (about 380 MB)...")
        urllib.request.urlretrieve(URL, temporary)
        temporary.replace(ARCHIVE)
    with ARCHIVE.open("rb") as source:
        actual = hashlib.file_digest(source, "sha256").hexdigest()
    if actual != SHA256:
        raise SystemExit("PostgreSQL archive checksum mismatch; nothing extracted.")
    if (DESTINATION / "pgsql/share/postgres.bki").exists():
        print("Pinned PostgreSQL runtime already present.")
        return
    with ZipFile(ARCHIVE) as archive:
        for item in archive.infolist():
            if item.filename.startswith(("pgsql/bin/", "pgsql/lib/", "pgsql/share/")):
                if (
                    not (DESTINATION / item.filename)
                    .resolve()
                    .is_relative_to(DESTINATION)
                ):
                    raise SystemExit("Unsafe archive path.")
                archive.extract(item, DESTINATION)
    print("PostgreSQL runtime extracted. No global PATH or service changes.")


if __name__ == "__main__":
    main()

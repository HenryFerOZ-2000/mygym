from pathlib import Path
import sys

import pytest
from django.db import connection, transaction
from django.contrib.sessions.models import Session
from django.utils import timezone

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from recovery.archive import ArchiveError, open_archive, seal_archive
from recovery.guards import RecoveryError, assert_backup_role, assert_empty_destination
from recovery.guards import dump_arguments, restore_arguments, validate_source


def test_windows_protection_roundtrip_and_confidentiality(tmp_path):
    data = b"PGDMP" + b"fictional-private-fixture" * 20
    path = tmp_path / "fixture.mygym-recovery"
    seal_archive(path, data, source="mygym_test", postgres_major=17)
    assert b"fictional-private-fixture" not in path.read_bytes()
    assert b"mygym_test" not in path.read_bytes()
    assert open_archive(path) == data


def test_damaged_archive_is_rejected(tmp_path):
    path = tmp_path / "fixture.mygym-recovery"
    seal_archive(path, b"PGDMPfictional", source="mygym_test", postgres_major=17)
    damaged = bytearray(path.read_bytes())
    damaged[-12] ^= 128
    path.write_bytes(damaged)
    with pytest.raises(ArchiveError):
        open_archive(path)


def test_never_replace_an_existing_archive(tmp_path):
    path = tmp_path / "fixture.mygym-recovery"
    path.write_bytes(b"original")
    with pytest.raises(ArchiveError):
        seal_archive(path, b"PGDMPfixture", source="mygym_test", postgres_major=17)
    assert path.read_bytes() == b"original"
    assert list(tmp_path.iterdir()) == [path]


@pytest.mark.parametrize(
    "source", ["mygym_dev", "postgres", "mygym_e2e", "mygym_test;DROP"]
)
def test_rehearsal_rejects_non_test_source(source):
    with pytest.raises(RecoveryError):
        validate_source(source)


@pytest.mark.parametrize("major", [16, 18])
def test_rejects_incompatible_postgres_before_writing(tmp_path, major):
    with pytest.raises(ArchiveError):
        seal_archive(
            tmp_path / "new.mygym-recovery",
            b"PGDMPfixture",
            source="mygym_test",
            postgres_major=major,
        )
    assert not list(tmp_path.iterdir())


def test_rejects_unknown_envelope_and_non_archive(tmp_path):
    path = tmp_path / "fixture.mygym-recovery"
    path.write_bytes(b"MYGYM-RECOVERY-99\nfixture")
    with pytest.raises(ArchiveError):
        open_archive(path)
    with pytest.raises(ArchiveError):
        seal_archive(path, b"plain SQL", source="mygym_test", postgres_major=17)


@pytest.mark.parametrize(
    "role",
    [
        ("mygym_runtime", False, False, False, False),
        ("mygym_migrator", False, False, False, False),
        ("mygym_admin", True, True, True, True),
        ("fixture_reader", False, False, False, False),
        ("fixture_backup", False, True, True, False),
    ],
)
def test_rejects_inadequate_backup_identity(role):
    with pytest.raises(RecoveryError):
        assert_backup_role(role)


def test_commands_preserve_source_sessions_and_restore_atomically():
    assert_backup_role(("fixture_backup", False, True, False, False))
    dump = dump_arguments("pg_dump.exe", "mygym_test")
    restore = restore_arguments("pg_restore.exe", "mygym_restore_test_12345678")
    assert "--exclude-table-data=public.django_session" in dump
    assert "--single-transaction" in restore and "--exit-on-error" in restore
    assert not {
        "--clean",
        "--create",
        "--disable-triggers",
        "--enable-row-security",
    }.intersection(restore)
    assert not {"--clean", "--create", "--enable-row-security"}.intersection(dump)


@pytest.mark.django_db
def test_existing_test_database_is_not_a_restore_target():
    with pytest.raises(RecoveryError):
        assert_empty_destination(connection, "mygym_test")


@pytest.mark.django_db
def test_runtime_cannot_export_whole_database():
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT current_user,rolsuper,rolbypassrls,rolcreatedb,rolcreaterole FROM pg_roles WHERE rolname=current_user"
        )
        role = cursor.fetchone()
    with pytest.raises(RecoveryError):
        assert_backup_role(role)


@pytest.mark.django_db
def test_session_invalidation_and_integrity_roll_back_together(workspaces):
    from recovery.guards import invalidate_restored_sessions
    from modules.clients.models import ClientRecord
    from tenancy.context import workspace_context
    from tenancy.checks import assert_runtime_role

    assert_runtime_role()
    Session.objects.create(
        session_key="fictional-recovery-session",
        session_data="fixture",
        expire_date=timezone.now(),
    )
    with workspace_context(workspaces[0].id):
        record = ClientRecord.objects.create(
            workspace=workspaces[0], full_name="Recovery fixture"
        )
    with pytest.raises(RecoveryError), transaction.atomic():
        invalidate_restored_sessions(connection)
        raise RecoveryError("Fixture integrity failure")
    assert Session.objects.filter(session_key="fictional-recovery-session").exists()
    with transaction.atomic():
        invalidate_restored_sessions(connection)
    assert not Session.objects.exists()
    assert ClientRecord.objects.count() == 0
    with workspace_context(workspaces[1].id):
        assert not ClientRecord.objects.filter(pk=record.pk).exists()
    with workspace_context(workspaces[0].id):
        assert ClientRecord.objects.filter(pk=record.pk).exists()

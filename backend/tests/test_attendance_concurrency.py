from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from uuid import uuid4


def test_committed_concurrent_visits_and_void(django_db_blocker):
    from django.contrib.auth import get_user_model
    from django.db import connections
    from rest_framework.exceptions import ValidationError
    from modules.workspaces.models import (
        Workspace,
        WorkspaceAccess,
        WorkspaceCapability,
    )
    from modules.workspaces.policies import WorkspaceContext
    from modules.clients.services import create_client
    from modules.gym.attendance import record_attendance, void_attendance
    from modules.gym.models import Attendance, AttendanceVoid
    from modules.gym.dates import today
    from tenancy.context import workspace_context

    with django_db_blocker.unblock():
        actor = get_user_model().objects.create_user(
            username="attendance-race-" + uuid4().hex
        )
        space = Workspace.objects.create(
            name="Concurrencia asistencia ficticia " + uuid4().hex
        )
        WorkspaceAccess.objects.create(workspace=space, user=actor, role="OWNER")
        WorkspaceCapability.objects.create(workspace=space, code="gym.attendance")
        context = WorkspaceContext(space, actor)
        try:
            with workspace_context(space.id):
                client = create_client(
                    context, {"full_name": "Visita ficticia concurrente"}
                )
            payload = {
                "request_id": uuid4(),
                "expected_date": today(space),
                "expected_count": 0,
                "confirm_repeat": False,
                "exception": True,
                "reason": "Prueba de concurrencia",
            }

            def race(fn, target, payloads):
                barrier = Barrier(2)

                def run(data):
                    try:
                        with workspace_context(space.id):
                            barrier.wait(timeout=10)
                            return str(fn(context, target, data).id)
                    except ValidationError:
                        return "rejected"
                    finally:
                        connections.close_all()

                with ThreadPoolExecutor(max_workers=2) as pool:
                    return list(pool.map(run, payloads))

            ids = race(record_attendance, client.id, [payload, payload])
            assert ids[0] == ids[1] and ids[0] != "rejected"
            repeat = {**payload, "expected_count": 1, "confirm_repeat": True}
            outcomes = race(
                record_attendance,
                client.id,
                [{**repeat, "request_id": uuid4()}, {**repeat, "request_id": uuid4()}],
            )
            assert outcomes.count("rejected") == 1
            voids = race(
                void_attendance,
                ids[0],
                [
                    {"request_id": uuid4(), "reason": "Error ficticio"},
                    {"request_id": uuid4(), "reason": "Error ficticio"},
                ],
            )
            assert voids.count("rejected") == 1
            with workspace_context(space.id):
                assert Attendance.objects.filter(client=client).count() == 2
                assert AttendanceVoid.objects.count() == 1
        finally:
            space.is_active = False
            space.save(update_fields=["is_active"])
            actor.is_active = False
            actor.save(update_fields=["is_active"])

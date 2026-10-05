from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from decimal import Decimal
from uuid import uuid4


def test_committed_concurrent_enrollment_payment_and_refund(django_db_blocker):
    from django.contrib.auth import get_user_model
    from django.db import connections
    from modules.workspaces.models import Workspace
    from modules.workspaces.policies import WorkspaceContext
    from modules.clients.services import create_client
    from modules.gym.services import create_plan
    from modules.gym.memberships import preview, enroll
    from modules.gym.dates import today
    from modules.gym.models import Membership
    from modules.receivables.models import Charge, Payment, Refund
    from modules.receivables.services import record_payment, refund_payment, balance
    from tenancy.context import workspace_context
    from rest_framework.exceptions import ValidationError

    # Real commits are necessary to exercise row locks. Append-only fictional
    # history is retained in an inactive, isolated test workspace after the test.
    with django_db_blocker.unblock():
        actor = get_user_model().objects.create_user(
            username="concurrency-" + uuid4().hex
        )
        space = Workspace.objects.create(name="Prueba concurrente " + uuid4().hex)
        context = WorkspaceContext(workspace=space, actor=actor)
        try:
            with workspace_context(space.id):
                client = create_client(context, {"full_name": "Concurrencia ficticia"})
                plan = create_plan(
                    context,
                    {
                        "name": "Prueba",
                        "amount": Decimal("20.00"),
                        "currency": "USD",
                        "unit": "DAYS",
                        "quantity": 30,
                    },
                )
                data = {
                    "plan_id": plan.id,
                    "start_date": today(space) + timedelta(days=1),
                }
                result = preview(context, client.id, data)
                enrollment = {
                    **data,
                    "expected_version": 1,
                    "expected_start": result["start_date"],
                    "expected_end": result["end_date"],
                    "request_id": uuid4(),
                }

            def run(fn, *args):
                try:
                    with workspace_context(space.id):
                        return str(fn(context, client.id, *args).id)
                except ValidationError:
                    return "rejected"
                finally:
                    connections.close_all()

            with ThreadPoolExecutor(max_workers=2) as pool:
                ids = list(pool.map(lambda _: run(enroll, enrollment), range(2)))
                assert ids[0] == ids[1] and ids[0] != "rejected"
            with workspace_context(space.id):
                assert Membership.objects.filter(client=client).count() == 1
                charge = Charge.objects.get(client=client)
                payment_data = {
                    "request_id": uuid4(),
                    "amount": Decimal("20.00"),
                    "currency": "USD",
                    "method": "CASH",
                    "allocations": [
                        {"charge_id": charge.id, "amount": Decimal("20.00")}
                    ],
                }
            with ThreadPoolExecutor(max_workers=2) as pool:
                outcomes = list(
                    pool.map(
                        lambda key: run(
                            record_payment, {**payment_data, "request_id": key}
                        ),
                        [uuid4(), uuid4()],
                    )
                )
                assert outcomes.count("rejected") == 1
            with workspace_context(space.id):
                payment = Payment.objects.get(client=client)
                assert balance(charge) == 0
                refund_data = {
                    "request_id": uuid4(),
                    "reason": "Prueba ficticia",
                    "allocations": [
                        {"charge_id": charge.id, "amount": Decimal("20.00")}
                    ],
                }
            with ThreadPoolExecutor(max_workers=2) as pool:
                outcomes = list(
                    pool.map(
                        lambda key: run(
                            refund_payment,
                            payment.id,
                            {**refund_data, "request_id": key},
                        ),
                        [uuid4(), uuid4()],
                    )
                )
                assert outcomes.count("rejected") == 1
            with workspace_context(space.id):
                assert Refund.objects.filter(payment=payment).count() == 1
                assert balance(charge) == Decimal("20.00")
                other_client = create_client(
                    context, {"full_name": "Otro cliente ficticio"}
                )
                from modules.receivables.services import create_charge

                other_charge = create_charge(
                    context,
                    other_client,
                    uuid4(),
                    Decimal("20.00"),
                    "USD",
                    "Prueba de colisión",
                )

            from threading import Barrier

            barrier = Barrier(2)
            shared_key = uuid4()

            def collide(pair):
                customer, obligation = pair
                try:
                    with workspace_context(space.id):
                        barrier.wait(timeout=5)
                        payload = {
                            **payment_data,
                            "request_id": shared_key,
                            "allocations": [
                                {"charge_id": obligation.id, "amount": Decimal("20.00")}
                            ],
                        }
                        return str(record_payment(context, customer.id, payload).id)
                except ValidationError:
                    return "rejected"
                finally:
                    connections.close_all()

            with ThreadPoolExecutor(max_workers=2) as pool:
                outcomes = list(
                    pool.map(collide, [(client, charge), (other_client, other_charge)])
                )
                assert outcomes.count("rejected") == 1
        finally:
            space.is_active = False
            space.save(update_fields=["is_active"])
            actor.is_active = False
            actor.save(update_fields=["is_active"])

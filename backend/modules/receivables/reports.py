from django.db import connection
from modules.shared.reporting import period_bounds


def financial_report(context, start, end):
    """One statement: event totals and current debt share a PostgreSQL snapshot."""
    lower, upper = period_bounds(start, end, context.workspace.timezone)
    with connection.cursor() as cursor:
        cursor.execute(
            """
            WITH movements AS (
                SELECT currency, amount AS payments, 0::numeric AS refunds,
                       0::numeric AS debt FROM receivables_payment
                WHERE workspace_id = %(workspace)s AND created_at >= %(lower)s AND created_at < %(upper)s
                UNION ALL
                SELECT p.currency, 0, r.amount, 0 FROM receivables_refund r
                JOIN receivables_payment p ON p.id = r.payment_id
                WHERE r.workspace_id = %(workspace)s AND p.workspace_id = %(workspace)s
                  AND r.created_at >= %(lower)s AND r.created_at < %(upper)s
                UNION ALL
                SELECT currency, 0, 0, amount FROM receivables_charge WHERE workspace_id = %(workspace)s
                UNION ALL
                SELECT c.currency, 0, 0, -a.amount FROM receivables_allocation a
                JOIN receivables_charge c ON c.id = a.charge_id
                WHERE a.workspace_id = %(workspace)s AND c.workspace_id = %(workspace)s
                UNION ALL
                SELECT c.currency, 0, 0, r.amount FROM receivables_refundallocation r
                JOIN receivables_allocation a ON a.id = r.allocation_id
                JOIN receivables_charge c ON c.id = a.charge_id
                WHERE r.workspace_id = %(workspace)s AND a.workspace_id = %(workspace)s AND c.workspace_id = %(workspace)s
            ), totals AS (
                SELECT currency, sum(payments) payments, sum(refunds) refunds,
                       sum(payments-refunds) net, sum(debt) outstanding_now
                FROM movements GROUP BY currency
            )
            SELECT statement_timestamp(), currency, payments, refunds, net, outstanding_now
            FROM (SELECT 1) anchor LEFT JOIN totals ON true ORDER BY currency
        """,
            {"workspace": context.workspace.id, "lower": lower, "upper": upper},
        )
        rows = cursor.fetchall()
    return {
        "from_date": start,
        "to_date": end,
        "timezone": context.workspace.timezone,
        "as_of": rows[0][0],
        "currencies": [
            dict(
                currency=row[1],
                **{
                    key: format(value, ".2f")
                    for key, value in zip(
                        ("payments", "refunds", "net", "outstanding_now"), row[2:]
                    )
                },
            )
            for row in rows
            if row[1] is not None
        ],
    }

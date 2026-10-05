from datetime import timedelta
from django.db import connection
from .dates import today


def attendance_report(context, start, end):
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT statement_timestamp(),
                count(*) FILTER (WHERE v.id IS NULL),
                count(DISTINCT a.client_id) FILTER (WHERE v.id IS NULL),
                count(*) FILTER (WHERE v.id IS NULL AND a.decision = 'EXCEPTION'),
                count(*) FILTER (WHERE v.id IS NOT NULL)
            FROM gym_attendance a LEFT JOIN gym_attendancevoid v
              ON v.attendance_id = a.id AND v.workspace_id = a.workspace_id
            WHERE a.workspace_id = %s AND a.local_date BETWEEN %s AND %s
        """,
            [context.workspace.id, start, end],
        )
        instant, entries, clients, exceptions, voided = cursor.fetchone()
    return {
        "from_date": start,
        "to_date": end,
        "as_of": instant,
        "entries": entries,
        "clients": clients,
        "exceptions": exceptions,
        "voided": voided,
    }


def expiry_report(context, query):
    day = today(context.workspace)
    number, size = query["page"], query["page_size"]
    with connection.cursor() as cursor:
        cursor.execute(
            """
            WITH RECURSIVE periods AS (
                SELECT id, client_id, start_date,
                    least(end_date, coalesce(cancelled_on, end_date)) finish
                FROM gym_membership WHERE workspace_id = %(workspace)s
                  AND least(end_date, coalesce(cancelled_on, end_date)) > start_date
            ), current_period AS (
                SELECT * FROM periods WHERE start_date <= %(day)s AND finish > %(day)s
            ), coverage AS (
                SELECT client_id, finish FROM current_period
                UNION
                SELECT c.client_id, p.finish FROM coverage c
                JOIN periods p ON p.client_id = c.client_id AND p.start_date = c.finish
            ), clients AS (
                SELECT c.id AS client_id, c.full_name,
                    CASE WHEN NOT c.is_active THEN 'CLIENT_INACTIVE'
                        WHEN EXISTS (SELECT 1 FROM current_period p JOIN gym_freeze f ON f.membership_id = p.id
                            WHERE p.client_id = c.id AND f.workspace_id = %(workspace)s
                              AND f.start_date <= %(day)s AND f.end_date > %(day)s) THEN 'FROZEN'
                        WHEN EXISTS (SELECT 1 FROM current_period p WHERE p.client_id = c.id) THEN 'ACTIVE'
                        WHEN EXISTS (SELECT 1 FROM periods p WHERE p.client_id = c.id AND p.finish <= %(day)s) THEN 'EXPIRED'
                        WHEN EXISTS (SELECT 1 FROM periods p WHERE p.client_id = c.id AND p.start_date > %(day)s) THEN 'FUTURE'
                        ELSE 'NO_MEMBERSHIP' END AS status,
                    (SELECT max(finish) FROM coverage x WHERE x.client_id = c.id) AS coverage_end,
                    (SELECT max(finish) FROM periods p WHERE p.client_id = c.id AND p.finish <= %(day)s) AS previous_end,
                    (SELECT min(start_date) FROM periods p WHERE p.client_id = c.id AND p.start_date > %(day)s) AS next_start
                FROM clients_clientrecord c WHERE c.workspace_id = %(workspace)s AND c.full_name ILIKE %(search)s
            ), filtered AS (
                SELECT *, coverage_end - 1 AS last_day,
                    coverage_end - 1 - %(day)s::date AS calendar_days_remaining
                FROM clients WHERE status = %(status)s OR
                  (%(status)s = 'EXPIRING' AND status = 'ACTIVE' AND coverage_end - 1 <= %(horizon)s)
            ), result_page AS (
                SELECT * FROM filtered ORDER BY coalesce(coverage_end, next_start, previous_end), full_name, client_id
                LIMIT %(size)s OFFSET %(offset)s
            )
            SELECT statement_timestamp(), (SELECT count(*) FROM filtered),
                coalesce((SELECT jsonb_agg(to_jsonb(r) ORDER BY coalesce(coverage_end, next_start, previous_end), full_name, client_id) FROM result_page r), '[]'::jsonb)
        """,
            {
                "workspace": context.workspace.id,
                "day": day,
                "search": "%"
                + query["q"]
                .replace("\\", "\\\\")
                .replace("%", "\\%")
                .replace("_", "\\_")
                + "%",
                "status": query["status"],
                "horizon": day + timedelta(days=query["horizon"]),
                "size": size,
                "offset": (number - 1) * size,
            },
        )
        instant, count, results = cursor.fetchone()
    # psycopg's Django cursor returns JSONB as text for raw SQL.
    if isinstance(results, str):
        import json

        results = json.loads(results)
    return {
        "as_of": instant,
        "reference_date": day,
        "timezone": context.workspace.timezone,
        "count": count,
        "next": number + 1 if count > number * size else None,
        "previous": number - 1 if number > 1 else None,
        "results": results,
    }

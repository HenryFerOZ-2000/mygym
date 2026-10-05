from django.db import migrations

TABLES = ["gym_attendance", "gym_attendancevoid"]


class Migration(migrations.Migration):
    dependencies = [("gym", "0005_attendance_attendancevoid_and_more")]
    operations = [migrations.RunSQL(
        f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY; ALTER TABLE {table} FORCE ROW LEVEL SECURITY; "
        f"CREATE POLICY workspace_isolation ON {table} USING (workspace_id::text = nullif(current_setting('app.workspace_id', true), '')) WITH CHECK (workspace_id::text = nullif(current_setting('app.workspace_id', true), ''));",
        f"DROP POLICY workspace_isolation ON {table}; ALTER TABLE {table} NO FORCE ROW LEVEL SECURITY; ALTER TABLE {table} DISABLE ROW LEVEL SECURITY;"
    ) for table in TABLES]

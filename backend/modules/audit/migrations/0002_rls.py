from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [("audit", "0001_initial")]
    operations = [
        migrations.RunSQL(
            """
        ALTER TABLE audit_auditevent ENABLE ROW LEVEL SECURITY;
        ALTER TABLE audit_auditevent FORCE ROW LEVEL SECURITY;
        CREATE POLICY workspace_isolation ON audit_auditevent
          USING (workspace_id::text = nullif(current_setting('app.workspace_id', true), ''))
          WITH CHECK (workspace_id::text = nullif(current_setting('app.workspace_id', true), ''));
        """,
            """
        DROP POLICY workspace_isolation ON audit_auditevent;
        ALTER TABLE audit_auditevent NO FORCE ROW LEVEL SECURITY;
        ALTER TABLE audit_auditevent DISABLE ROW LEVEL SECURITY;
        """,
        )
    ]

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [("clients", "0001_initial")]
    operations = [
        migrations.RunSQL(
            """
        ALTER TABLE clients_clientrecord ENABLE ROW LEVEL SECURITY;
        ALTER TABLE clients_clientrecord FORCE ROW LEVEL SECURITY;
        CREATE POLICY workspace_isolation ON clients_clientrecord
          USING (workspace_id::text = nullif(current_setting('app.workspace_id', true), ''))
          WITH CHECK (workspace_id::text = nullif(current_setting('app.workspace_id', true), ''));
        """,
            """
        DROP POLICY workspace_isolation ON clients_clientrecord;
        ALTER TABLE clients_clientrecord NO FORCE ROW LEVEL SECURITY;
        ALTER TABLE clients_clientrecord DISABLE ROW LEVEL SECURITY;
        """,
        )
    ]

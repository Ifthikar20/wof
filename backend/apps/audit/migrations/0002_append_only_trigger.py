"""
Database-level tamper protection (PostgreSQL only).

Even if application code were compromised, UPDATE/DELETE on the audit log and on story
revisions raise an exception. Combined with the production role grants in
infra/postgres/roles.sql (the app role has only INSERT/SELECT on these tables) this
makes history append-only at the database layer.
"""

from django.db import migrations

FORWARD = """
CREATE OR REPLACE FUNCTION wof_forbid_mutation() RETURNS trigger AS $$
BEGIN
  RAISE EXCEPTION 'table %% is append-only', TG_TABLE_NAME USING ERRCODE = 'insufficient_privilege';
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER audit_auditlog_append_only
  BEFORE UPDATE OR DELETE ON audit_auditlog
  FOR EACH ROW EXECUTE FUNCTION wof_forbid_mutation();

CREATE TRIGGER stories_storyrevision_append_only
  BEFORE UPDATE OR DELETE ON stories_storyrevision
  FOR EACH ROW EXECUTE FUNCTION wof_forbid_mutation();
"""

REVERSE = """
DROP TRIGGER IF EXISTS audit_auditlog_append_only ON audit_auditlog;
DROP TRIGGER IF EXISTS stories_storyrevision_append_only ON stories_storyrevision;
DROP FUNCTION IF EXISTS wof_forbid_mutation();
"""


def forward(apps, schema_editor):
    if schema_editor.connection.vendor == "postgresql":
        schema_editor.execute(FORWARD)


def reverse(apps, schema_editor):
    if schema_editor.connection.vendor == "postgresql":
        schema_editor.execute(REVERSE)


class Migration(migrations.Migration):
    dependencies = [
        ("audit", "0001_initial"),
        ("stories", "0001_initial"),
    ]

    operations = [migrations.RunPython(forward, reverse)]

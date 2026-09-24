-- Production role model (run by the DBA / Terraform, not by the app).
--
--   wof_owner    owns the schema; used ONLY by the migration job in CI/CD.
--   wof_app      what the running web/worker processes use. DML only, no DDL.
--   wof_readonly analytics / support read replica access.
--
-- Append-only tables (audit log, story revisions) get INSERT/SELECT only, on top of the
-- trigger installed by migration audit.0002. Nobody but wof_owner can drop the trigger.

CREATE ROLE wof_owner NOLOGIN;
CREATE ROLE wof_app LOGIN;           -- password / IAM auth managed by the secrets manager
CREATE ROLE wof_readonly LOGIN;

GRANT CONNECT ON DATABASE wof TO wof_app, wof_readonly;
GRANT USAGE ON SCHEMA public TO wof_app, wof_readonly;

GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO wof_app;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO wof_app;

REVOKE UPDATE, DELETE, TRUNCATE ON audit_auditlog, stories_storyrevision FROM wof_app;
GRANT SELECT, INSERT ON audit_auditlog, stories_storyrevision TO wof_app;

GRANT SELECT ON ALL TABLES IN SCHEMA public TO wof_readonly;
-- Readonly must not see secrets-at-rest columns even encrypted.
REVOKE SELECT ON accounts_user, verification_verificationrequest FROM wof_readonly;

ALTER DEFAULT PRIVILEGES FOR ROLE wof_owner IN SCHEMA public
  GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO wof_app;
ALTER DEFAULT PRIVILEGES FOR ROLE wof_owner IN SCHEMA public
  GRANT SELECT ON TABLES TO wof_readonly;

-- Local bootstrap: creates the least-privileged application role used by Django.
-- The container's POSTGRES_USER (superuser "postgres") owns the database and runs this once.
DO $$
BEGIN
  IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'wof_app') THEN
    CREATE ROLE wof_app LOGIN PASSWORD 'wof_app_local_password';
  END IF;
END $$;
ALTER DATABASE wof OWNER TO wof_app;

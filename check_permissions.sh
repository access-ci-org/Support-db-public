#!/bin/bash

# Load environment variables
set -a 
source .env
set +a

DB_NAME=ara_db

# SQL commands to list users and their permissions
SQL_COMMANDS=$(cat <<EOF
-- List all users
SELECT usename AS role_name,
  CASE 
     WHEN usesuper AND usecreatedb THEN 
	   CAST('superuser, create database' AS pg_catalog.text)
     WHEN usesuper THEN 
	    CAST('superuser' AS pg_catalog.text)
     WHEN usecreatedb THEN 
	    CAST('create database' AS pg_catalog.text)
     ELSE 
	    CAST('' AS pg_catalog.text)
  END role_attributes
FROM pg_catalog.pg_user
ORDER BY role_name;

-- List database-specific permissions
SELECT grantee, table_catalog, table_schema, table_name, privilege_type
FROM information_schema.table_privileges
WHERE table_catalog = '$DB_NAME'
ORDER BY grantee, table_name;

-- List schema permissions
SELECT nspname AS schema, 
       rolname AS grantee, 
       string_agg(privilege_type, ', ') AS privileges
FROM (
  SELECT nspname, rolname, privilege_type
  FROM pg_namespace
  CROSS JOIN pg_roles
  LEFT JOIN (
    SELECT nspname, rolname, privilege_type
    FROM aclexplode((SELECT nspacl FROM pg_namespace WHERE nspname = 'public')) AS acl
    JOIN pg_roles ON acl.grantee = pg_roles.oid
    JOIN pg_namespace ON acl.grantor = pg_namespace.oid
  ) AS privileges USING (nspname, rolname)
) AS foo
GROUP BY nspname, rolname
ORDER BY nspname, rolname;
EOF
)

# Execute SQL commands
echo "Executing SQL commands to show users and permissions..."
echo "$SQL_COMMANDS" | PGPASSWORD=$DB_ADMIN_PASS psql -U $DB_ADMIN_USER -d $DB_NAME
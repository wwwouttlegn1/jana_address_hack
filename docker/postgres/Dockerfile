FROM postgres:16-alpine

COPY scripts/create_reference_tables.sql /docker-entrypoint-initdb.d/01-reference-schema.sql
COPY docker/postgres/02-import-reference.sh /docker-entrypoint-initdb.d/02-import-reference.sh
COPY data/reference/*.csv /opt/jana-reference/

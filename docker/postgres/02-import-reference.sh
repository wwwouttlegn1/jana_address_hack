#!/bin/sh
set -eu

tables="regions districts settlements places streets living_areas admin_areas aliases"

for table in $tables; do
    echo "Importing jana_reference.$table"
    columns="$(head -n 1 "/opt/jana-reference/$table.csv" | tr -d '\r')"
    psql \
        --username "$POSTGRES_USER" \
        --dbname "$POSTGRES_DB" \
        --set ON_ERROR_STOP=1 \
        --command "\\copy jana_reference.$table ($columns) FROM '/opt/jana-reference/$table.csv' WITH (FORMAT csv, HEADER true, NULL '')"
done

psql \
    --username "$POSTGRES_USER" \
    --dbname "$POSTGRES_DB" \
    --set ON_ERROR_STOP=1 \
    --command "ANALYZE jana_reference.regions; ANALYZE jana_reference.districts; ANALYZE jana_reference.settlements; ANALYZE jana_reference.places; ANALYZE jana_reference.streets; ANALYZE jana_reference.living_areas; ANALYZE jana_reference.admin_areas; ANALYZE jana_reference.aliases;"

echo "JANA ADDRESS reference import completed"

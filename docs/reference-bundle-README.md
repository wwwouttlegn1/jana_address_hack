# Jana Address — Kazakhstan OSM reference bundle (v2)

**Purpose:** ready-to-import offline reference CSV files for the Jana Address FastAPI/PostgreSQL backend, prepared from the user's `kazakhstan-261016.osm.pbf` OpenStreetMap extract dated **2026-10-16**.

> This is an **OSM-derived address reference**, **not** Kazakhstan's official complete KATO catalogue. It has no KATO IDs and must not be presented as an official exhaustive list of addresses. The uploaded T-18-19-P statistical spreadsheet is not used as a KATO source, because it does not provide a complete machine-readable settlement classifier.

## Contents and checked sizes

| File | Rows | Description |
|---|---:|---|
| `data/reference/regions.csv` | 20 | OSM administrative level 4: 17 regions and 3 cities of republican significance |
| `data/reference/districts.csv` | 310 | Observed districts and city administrations linked to a region (from admin boundaries / contained features) |
| `data/reference/settlements.csv` | 8,351 | Deduplicated OSM city/town/village/hamlet/isolated dwelling/farm features |
| `data/reference/places.csv` | 15,017 | Place features, with original OSM IDs and geographical context |
| `data/reference/streets.csv` | 95,511 | **Road segments/features, not unique street names.** Includes full name, stripped core name, type, province and validated city when available |
| `data/reference/living_areas.csv` | 8,960 | Named neighbourhoods, residential landuse polygons and other area-type features |
| `data/reference/aliases.csv` | 80,955 | Russian, Kazakh and other alternative OSM names with normalized search keys |
| `data/reference/admin_areas.csv` | 1,152 | OSM named admin relations used as geographic context; missing/open geometries flagged |
| `data/reference/quality_report.json` | — | Extraction, filtering, missing links and limitations |

### Key points for the backend developer

- Join a record to its OSM identity via `(osm_type, osm_id)`. Street segments can repeat the same street name; this is normal. Do **not** assume `streets.csv` has one row per street.
- `name` is the primary OSM name; `name_ru` / `name_kk` preserve OSM language variants. `street_name_core` strips **explicit** street-type words (e.g. `Абай даңғылы` → `Абай`), `normalized_core` is lowercase/Unicode-normalized for lookup. Street type code is `street`, `avenue`, `lane`, etc. Empty street type means **not explicitly known**, not automatically `street`.
- `city` is **not** guessed from the nearest settlement. A populated `city` is derived from `addr:city` / `is_in:city` OSM tag, validated OSM administrative polygon with a matching settlement name, or one of the three verified republican-city level-4 polygons. Refer to `location_method`.
- `nearest_settlement` and `nearest_settlement_km` are **hints only**; never treat them as validated city without additional conditions. Streets lacking confidently verified city must retain `NULL`/empty city. Particularly useful when parser input already explicitly specifies city or province.
- `province` refers to the matched Kazakhstan region/city administrative polygon (sometimes explicit OSM tag); `district` is an OSM admin level 6 name and can represent a municipal administration. `admin8` might be a village council, and **must not automatically be written as city**.
- Some OSM `landuse=residential` areas may represent village polygons instead of named microdistricts. Use `area_type` and `place` semantics to filter.
- CSV files are UTF-8 with comma delimiters and quoted text where necessary. Empty fields are imported into PostgreSQL as `NULL`.
- The 8,351 settlements are **deduplicated by name + region + district + type** with point features preferred. Preserve `places.csv` when individual OSM identities matter. Homonymous settlements within the same district might need manual review.
- The output excludes features not linked to a validated Kazakhstan level-4 administrative area; this avoids obvious Russian/Kyrgyz/Chinese/Uzbek border contamination but can lose a small number of valid border objects.

## Install PostgreSQL tables (without changing existing app tables)

Files import into their **own schema**: `jana_reference` (tables `regions`, `districts`, `settlements`, `places`, `streets`, `living_areas`, `admin_areas`, `aliases`). No application table is overwritten.

From the repo root on Windows, after installing `pip install "psycopg[binary]"`:

```powershell
$env:DATABASE_URL = "postgresql://jana_user:YOUR_PASSWORD@localhost:5432/jana_address"
python scripts/import_to_postgres.py
```

For a backend running **inside Docker Compose**, `localhost` is not PostgreSQL: use the Compose service name (often `db`) as the hostname. This is only an example URL; check the actual credentials and host in your team's `.env` and `compose.yml`.

This one command executes `create_reference_tables.sql` and imports all eight CSV files in a single transaction. If the schema already contains old imported data, rerun with:

```powershell
python scripts/import_to_postgres.py --replace
```

`--replace` truncates **only eight `jana_reference.*` tables** inside one transaction. Back up manually curated additions first. No `DROP DATABASE`, no wiping user/assignment data. Never commit real DB passwords to GitHub.

**Important:** the SQL/PostgreSQL importer was syntax-checked, but was not connected to your teammate's PostgreSQL here; run it against your local instance and check results. If the other developer already has a differently named reference table/schema, agree on the interface before importing. Do not merge it with existing tables blindly.

For manually inspecting the DDL and example queries: `scripts/create_reference_tables.sql`, `scripts/sample_queries.sql`.

## Repeat the export from the original `.osm.pbf`

Requires Python 3.10+ and Shapely 2.x (the included PBF reader needs no `osmium` package):

```powershell
pip install shapely
python scripts/build_reference_v2.py data/raw/kazakhstan-261016.osm.pbf data/reference
python scripts/finalize_reference.py data/reference
python scripts/validate_reference.py data/reference
```

The source `.osm.pbf` file is **not bundled** in the ZIP; place it in `data/raw/` if a repeat export is needed. Add `data/raw/` to the **existing** project `.gitignore` before copying source files; never overwrite your team’s existing `.gitignore`. Do not place the original 215 MB PBF in Git unless the team has decided on LFS and checked licensing/size limits. Note: `finalize_reference.py` filters existing CSVs, so for another source version, regenerate raw files first.

## Example integration

A normalized input street `Абай` and explicit city `Алматы`:

```sql
SELECT name, name_ru, name_kk, street_name_core,
       street_type, city, province, location_method
FROM jana_reference.streets
WHERE normalized_core = 'абай' AND city = 'Алматы'
LIMIT 20;
```

For RU/KZ variant search, use `aliases.normalized_alias_core` joined to the target `(object_kind, osm_type, osm_id)`; additional parser-side inflection/fuzzy matching may be needed (e.g. `Абай` vs. `Абая`). See `scripts/sample_queries.sql`.

## Completeness and licensing

- The OSM PBF gives rich volunteered geographic information, not authoritative KATO numeric hierarchy, not guaranteed house/building numbers, and not all residential roads have verified city labels. OSM mappings change over time. Data is suitable as a reference **candidate system** for the parser, not proof an address exists.
- Dataset licence: **OpenStreetMap contributors, Open Database License (ODbL) 1.0**. Attribution: `© OpenStreetMap contributors` — https://www.openstreetmap.org/copyright . Any sharing of derived databases must follow ODbL obligations; discuss with the team if the service distributes derivatives.
- `admin_areas.csv` contains area names, geometry validity flags and representative coordinate, **not full polygon geometry**. Spatial linking was performed during extraction using complete enough OSM ways, not in PostgreSQL.
- Overall correctness against the hackathon's hidden address samples is **not measured** by this export. Measure accuracy in the actual parser with labeled test addresses before claiming improvements.

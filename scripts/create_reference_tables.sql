-- Jana Address: separate, non-destructive schema for OSM reference data.
-- Execute: psql "$DATABASE_URL" -f scripts/create_reference_tables.sql
CREATE SCHEMA IF NOT EXISTS jana_reference;

CREATE TABLE IF NOT EXISTS jana_reference.places (
    osm_type TEXT NOT NULL,
    osm_id BIGINT NOT NULL,
    name TEXT NOT NULL,
    name_ru TEXT,
    name_kk TEXT,
    place_type TEXT,
    lat DOUBLE PRECISION,
    lon DOUBLE PRECISION,
    province TEXT,
    district TEXT,
    admin8 TEXT,
    city TEXT,
    location_method TEXT NOT NULL,
    nearest_settlement TEXT,
    nearest_settlement_km DOUBLE PRECISION,
    source TEXT NOT NULL,
    PRIMARY KEY (osm_type,osm_id)
);

CREATE TABLE IF NOT EXISTS jana_reference.streets (
    osm_type TEXT NOT NULL,
    osm_id BIGINT NOT NULL,
    name TEXT NOT NULL,
    name_ru TEXT,
    name_kk TEXT,
    street_type TEXT,
    street_name_core TEXT,
    normalized_core TEXT,
    highway TEXT,
    lat DOUBLE PRECISION,
    lon DOUBLE PRECISION,
    province TEXT,
    district TEXT,
    admin8 TEXT,
    city TEXT,
    location_method TEXT NOT NULL,
    nearest_settlement TEXT,
    nearest_settlement_km DOUBLE PRECISION,
    source TEXT NOT NULL,
    PRIMARY KEY(osm_type,osm_id)
);

CREATE TABLE IF NOT EXISTS jana_reference.living_areas (
    osm_type TEXT NOT NULL,
    osm_id BIGINT NOT NULL,
    name TEXT NOT NULL,
    name_ru TEXT,
    name_kk TEXT,
    area_type TEXT,
    lat DOUBLE PRECISION,
    lon DOUBLE PRECISION,
    province TEXT,
    district TEXT,
    admin8 TEXT,
    city TEXT,
    location_method TEXT NOT NULL,
    nearest_settlement TEXT,
    nearest_settlement_km DOUBLE PRECISION,
    source TEXT NOT NULL,
    PRIMARY KEY(osm_type,osm_id)
);

CREATE TABLE IF NOT EXISTS jana_reference.admin_areas (
    osm_relation_id BIGINT PRIMARY KEY,
    name TEXT NOT NULL,
    name_ru TEXT,
    name_kk TEXT,
    admin_level INTEGER NOT NULL,
    place TEXT,
    geometry_status TEXT NOT NULL,
    center_lat DOUBLE PRECISION,
    center_lon DOUBLE PRECISION,
    way_members INTEGER,
    source TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS jana_reference.regions (
    osm_relation_id BIGINT PRIMARY KEY,
    name TEXT NOT NULL,
    name_ru TEXT,
    name_kk TEXT,
    region_type TEXT NOT NULL,
    center_lat DOUBLE PRECISION,
    center_lon DOUBLE PRECISION,
    source TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS jana_reference.districts (
    province TEXT NOT NULL,
    name TEXT NOT NULL,
    name_ru TEXT,
    name_kk TEXT,
    osm_relation_id BIGINT,
    observed_objects INTEGER,
    relation_match TEXT,
    source TEXT NOT NULL,
    PRIMARY KEY (province,name)
);

CREATE TABLE IF NOT EXISTS jana_reference.settlements (
    osm_type TEXT NOT NULL,
    osm_id BIGINT NOT NULL,
    name TEXT NOT NULL,
    name_ru TEXT,
    name_kk TEXT,
    settlement_type TEXT NOT NULL,
    province TEXT,
    district TEXT,
    admin8 TEXT,
    lat DOUBLE PRECISION,
    lon DOUBLE PRECISION,
    source TEXT NOT NULL,
    PRIMARY KEY (osm_type,osm_id)
);

CREATE TABLE IF NOT EXISTS jana_reference.aliases (
    object_kind TEXT NOT NULL,
    osm_type TEXT NOT NULL,
    osm_id BIGINT NOT NULL,
    alias TEXT NOT NULL,
    lang_or_tag TEXT NOT NULL,
    normalized_alias TEXT NOT NULL,
    normalized_alias_core TEXT NOT NULL
);

-- Index creation is separate so the loader can import data before building them.
CREATE INDEX IF NOT EXISTS jr_streets_name_ci ON jana_reference.streets (lower(name));
CREATE INDEX IF NOT EXISTS jr_streets_name_ru_ci ON jana_reference.streets (lower(name_ru));
CREATE INDEX IF NOT EXISTS jr_streets_name_kk_ci ON jana_reference.streets (lower(name_kk));
CREATE INDEX IF NOT EXISTS jr_streets_city_name ON jana_reference.streets (city,lower(name));
CREATE INDEX IF NOT EXISTS jr_places_name_ci ON jana_reference.places (lower(name));
CREATE INDEX IF NOT EXISTS jr_places_type ON jana_reference.places (place_type);
CREATE INDEX IF NOT EXISTS jr_areas_name_ci ON jana_reference.living_areas (lower(name));
CREATE INDEX IF NOT EXISTS jr_aliases_lookup ON jana_reference.aliases (normalized_alias);
CREATE INDEX IF NOT EXISTS jr_aliases_target ON jana_reference.aliases (object_kind,osm_type,osm_id);
CREATE INDEX IF NOT EXISTS jr_districts_name_ci ON jana_reference.districts (lower(name));
CREATE INDEX IF NOT EXISTS jr_settlements_name_ci ON jana_reference.settlements (lower(name));
CREATE INDEX IF NOT EXISTS jr_settlements_context ON jana_reference.settlements (province,district);
CREATE INDEX IF NOT EXISTS jr_streets_normalized_core ON jana_reference.streets (normalized_core);
CREATE INDEX IF NOT EXISTS jr_aliases_normalized_core ON jana_reference.aliases (normalized_alias_core);

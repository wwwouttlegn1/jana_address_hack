-- Example lookup patterns for the Jana Address parser after import.
-- Roads may be split into many OSM segments; group by name/province/city when needed.
-- 'city' is empty when not confidently known; do not treat nearest_settlement as verified city.

-- 1) Search for the core form of a road name inside a known city.
SELECT osm_id,name,name_ru,name_kk,street_type,street_name_core,
       city,province,district,location_method
FROM jana_reference.streets
WHERE normalized_core = 'абай'
  AND city = 'Алматы'
ORDER BY name
LIMIT 20;

-- 2) Alias search for Russian/Kazakh named OSM road variants.
SELECT s.osm_type,s.osm_id,s.name,a.alias,a.lang_or_tag,
       s.city,s.province,s.location_method
FROM jana_reference.aliases a
JOIN jana_reference.streets s
  ON a.object_kind='streets' AND a.osm_type=s.osm_type AND a.osm_id=s.osm_id
WHERE a.normalized_alias_core = 'абая'
  AND s.province = 'Алматы'
LIMIT 20;

-- 3) Exact locality by province and district.
SELECT name, name_ru, name_kk, settlement_type, province, district,lat,lon
FROM jana_reference.settlements
WHERE province = 'Қарағанды облысы'
  AND (lower(name)=lower('Караганда') OR lower(name_ru)=lower('Караганда'))
LIMIT 20;

-- 4) Overview of coverage by confident city matching approach.
SELECT location_method,COUNT(*) FROM jana_reference.streets
GROUP BY location_method ORDER BY COUNT(*) DESC;

#!/usr/bin/env python3
"""Keep only objects with verified Kazakhstan level-4 region, and build flat lookup tables.
Uses raw OSM-derived output of build_reference_v2.py, no external data.
"""
import collections
import copy
import csv
import json
import os
import re
import sys
import unicodedata
from build_reference_v2 import TYPE_PATTERNS
from pathlib import Path

SETTLEMENT={'city','town','village','hamlet','isolated_dwelling','farm'}
CAPITALS={'Алматы','Астана','Шымкент'}
BASE=('places','streets','living_areas')

def norm(x):
    x=unicodedata.normalize('NFKC',x).casefold().replace('ё','е')
    return ' '.join(re.findall(r'[\w]+',x,flags=re.UNICODE))

def core_street_name(name):
    """Remove only explicit street-type words, never guess an absent street type."""
    text=name.strip()
    for _,pat in TYPE_PATTERNS:
        candidate=re.sub(pat,' ',text).strip(' ,.-\t')
        if candidate and candidate!=text:
            return ' '.join(candidate.split())
    return text

def readcsv(path):
    with path.open(newline='',encoding='utf-8') as f:return list(csv.DictReader(f))

def writecsv(path,rows,fields):
    path.parent.mkdir(parents=True,exist_ok=True)
    temp=path.with_suffix('.tmp')
    with temp.open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=fields,extrasaction='ignore');w.writeheader();w.writerows(rows)
    os.replace(temp,path)

def run():
    path=Path(sys.argv[1]) if len(sys.argv)>1 else Path(__file__).resolve().parents[1]/'data'/'reference'
    report=json.loads((path/'quality_report.json').read_text('utf-8'))
    alladmins=readcsv(path/'admin_areas.csv')
    regions0=[r for r in alladmins if r['admin_level']=='4' and r['geometry_status']=='valid_polygon' and (
        r['name'].endswith('облысы') or r['name'] in CAPITALS)]
    regions0.sort(key=lambda r:r['name'])
    valid_regions={r['name'] for r in regions0}
    if len(valid_regions)!=20:raise RuntimeError(f'Expected 20 verified OSM Kazakhstan regions, got {len(valid_regions)}: {sorted(valid_regions)}')
    region_cols=['osm_relation_id','name','name_ru','name_kk','region_type','center_lat','center_lon','source']
    writecsv(path/'regions.csv',[{'osm_relation_id':r['osm_relation_id'],'name':r['name'],'name_ru':r['name_ru'],
       'name_kk':r['name_kk'],'region_type':'republican_city' if r['name'] in CAPITALS else 'region',
       'center_lat':r['center_lat'],'center_lon':r['center_lon'],'source':'OpenStreetMap'} for r in regions0],region_cols)
    before={};after={};tables={};keys=set();method_counts=collections.Counter();city_counts=collections.Counter()
    for kind in BASE:
        source=readcsv(path/(kind+'.csv'))
        before[kind]=len(source)
        filtered=[]
        for r in source:
            if r['province'] not in valid_regions:continue
            if r['province'] in CAPITALS and not r['city']:
                r['city']=r['province'];r['location_method']='republican_city_admin4'
            if kind=='streets':
                r['street_name_core']=core_street_name(r['name'])
                r['normalized_core']=norm(r['street_name_core'])
            filtered.append(r)
            keys.add((kind,r['osm_type'],r['osm_id']))
            method_counts[r['location_method']]+=1
            if r['city']:city_counts[kind]+=1
        after[kind]=len(filtered)
        writecsv(path/(kind+'.csv'),filtered, list(source[0].keys()) + (['street_name_core','normalized_core'] if kind=='streets' and 'street_name_core' not in source[0] else []))
        tables[kind]=filtered
    alias_rows=readcsv(path/'aliases.csv');before['aliases']=len(alias_rows)
    alias_rows=[r for r in alias_rows if (r['object_kind'],r['osm_type'],r['osm_id']) in keys]
    for r in alias_rows:
        r['normalized_alias_core']=norm(core_street_name(r['alias'])) if r['object_kind']=='streets' else r['normalized_alias']
    after['aliases']=len(alias_rows)
    writecsv(path/'aliases.csv',alias_rows,['object_kind','osm_type','osm_id','alias','lang_or_tag','normalized_alias','normalized_alias_core'])
    observed=collections.Counter()
    for kind in BASE:
        for r in tables[kind]:
            if r['district']:observed[(r['province'],r['district'])]+=1
    by_name=collections.defaultdict(list)
    for a in alladmins:
        if a['admin_level']=='6' and a['geometry_status']=='valid_polygon':by_name[a['name']].append(a)
    district_cols=['province','name','name_ru','name_kk','osm_relation_id','observed_objects','relation_match','source']
    districts=[]
    for (region,name),n in sorted(observed.items()):
        matches=by_name.get(name,[])
        # A relation id is only safe if the name unambiguously identifies one region-wide feature.
        row={'province':region,'name':name,'name_ru':'','name_kk':'',
             'osm_relation_id':'','observed_objects':n,'relation_match':'ambiguous_or_missing','source':'OpenStreetMap'}
        if len(matches)==1:
            row.update({'name_ru':matches[0]['name_ru'],'name_kk':matches[0]['name_kk'],
                        'osm_relation_id':matches[0]['osm_relation_id'],'relation_match':'osm_relation_name'})
        districts.append(row)
    writecsv(path/'districts.csv',districts,district_cols)
    settlement_cols=['osm_type','osm_id','name','name_ru','name_kk','settlement_type','province','district',
                     'admin8','lat','lon','source']
    settlement_rows=[];settlements_seen=set()
    # Prefer point geometry and locality nodes, then polygons if no same-name node exists.
    candidates=sorted([r for r in tables['places'] if r['place_type'] in SETTLEMENT],
                      key=lambda r:0 if r['osm_type']=='node' else 1)
    for r in candidates:
        # Deduplicate OSM node/way representations with same name and administrative context.
        key=(norm(r['name']),r['province'],r['district'],r['place_type'])
        if key in settlements_seen:continue
        settlements_seen.add(key)
        settlement_rows.append({'osm_type':r['osm_type'],'osm_id':r['osm_id'],
             'name':r['name'],'name_ru':r['name_ru'],'name_kk':r['name_kk'],
             'settlement_type':r['place_type'],'province':r['province'],
             'district':r['district'],'admin8':r['admin8'],
             'lat':r['lat'],'lon':r['lon'],'source':'OpenStreetMap'})
    settlement_rows.sort(key=lambda r:(r['province'],r['district'],r['name']))
    writecsv(path/'settlements.csv',settlement_rows,settlement_cols)
    # Keep only Kazakhstan administrative relations with names observed in the actual contained records.
    known_l8={r['admin8'] for kind in BASE for r in tables[kind] if r['admin8']}
    known_l6={r['district'] for kind in BASE for r in tables[kind] if r['district']}
    kept_admin=[r for r in alladmins if (r['admin_level']=='4' and r['name'] in valid_regions) or
        (r['admin_level']=='6' and r['name'] in known_l6) or
        (r['admin_level']=='8' and r['name'] in known_l8)]
    writecsv(path/'admin_areas.csv',kept_admin,list(alladmins[0].keys()))
    before['admin_areas']=len(alladmins)
    after.update({'admin_areas':len(kept_admin),'regions':len(regions0),
                  'districts':len(districts),'settlements':len(settlement_rows)})
    report['raw_extraction']=report.get('raw_extraction',copy.deepcopy(report['processing']))
    report['processing']['count']=after
    report['processing']['location_methods']=dict(method_counts)
    report['processing']['rows_with_verified_city']=dict(city_counts)
    report['processing']['filtered_out_border_or_unlinked']= {k:report['raw_extraction']['count'][k]-after[k] for k in before}
    report['processing']['admin4_verified_regions']=sorted(valid_regions)
    report['processing']['settlements_deduplication']='name+province+district+place_type, preferring OSM place nodes'
    report['processing']['regional_filter']='Only level-4 polygon-matched OSM provinces and 3 cities of republican significance.'
    report['limitations'].extend([
       'Excluded OSM objects without a matching Kazakhstan level-4 administrative polygon; this favors precision over recall near border/geometry gaps.',
       'City field for 3 cities of republican significance comes from verified admin-level-4 polygon containment.',
       'Settlement place name deduplication can merge true homonyms inside the same district; retain places.csv for raw per-OSM identities.',
       'Districts are derived from administrative names observed on geolocated OSM features; parent region is not a KATO-official code.',
       'The region source is OSM administrative polygons, not the official KATO classifier.'])
    (path/'quality_report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print('Finalized:',json.dumps(after,ensure_ascii=False))
    print('Dropped unlocated or foreign:',{k:report['raw_extraction']['count'][k]-after[k] for k in before})
    print('Verified city links:',dict(city_counts))

if __name__=='__main__':run()

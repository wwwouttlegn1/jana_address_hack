#!/usr/bin/env python3
"""Verify CSV consistency before sharing with the backend developer.
Usage: python scripts/validate_reference.py [data/reference]
"""
import collections,csv,json,sys
from pathlib import Path

root=Path(sys.argv[1]) if len(sys.argv)>1 else Path(__file__).resolve().parents[1]/'data'/'reference'
report=json.loads((root/'quality_report.json').read_text(encoding='utf-8'))
errors=[]
for table in ('regions','districts','settlements','places','streets','living_areas','aliases','admin_areas'):
    path=root/(table+'.csv')
    with path.open(newline='',encoding='utf-8') as handle:
        rd=csv.DictReader(handle)
        if not rd.fieldnames:errors.append(f'{table}: no header');continue
        cnt=0;seen=set();methods=collections.Counter()
        for row in rd:
            cnt+=1
            if table in ('places','streets','living_areas'):
                if not row['name'] or not row['osm_type'] or not row['osm_id']:
                    errors.append(f'{table}: missing required name/OSM key at CSV record {cnt}')
                key=(row['osm_type'],row['osm_id'])
                if key in seen:errors.append(f'{table}: repeated OSM feature {key}')
                seen.add(key)
                if row['lat'] or row['lon']:
                    try:
                        lat=float(row['lat']);lon=float(row['lon'])
                        if not (40<=lat<=56 and 46<=lon<=88):errors.append(f'{table}: invalid bbox at row {cnt}: {lat} {lon}')
                    except ValueError:errors.append(f'{table}: non numeric coordinates row {cnt}')
                if row['city'] and row['location_method'] not in ('explicit_osm_tag','polygon_and_settlement_name','republican_city_admin4'):
                    errors.append(f'{table}: unverified populated city at row {cnt}')
                methods[row['location_method']]+=1
        expected=report['processing']['count'][table]
        if cnt!=expected:errors.append(f'{table}: rows={cnt} expected={expected}')
        print(table,'rows=',cnt,'methods=',dict(methods) if methods else 'n/a')
print('PASS' if not errors else 'FAILED',len(errors),'errors')
if errors:print(*errors[:30],sep='\n');sys.exit(1)

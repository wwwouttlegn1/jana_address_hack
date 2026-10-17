#!/usr/bin/env python3
"""Build a reproducible offline Kazakhstan OSM reference bundle.
Usage: python scripts/build_reference_v2.py SOURCE.osm.pbf OUTPUT_DIRECTORY
Works with Python 3.10+ and shapely 2.x. Does not download anything.
Properties: named dense nodes included; admin boundaries used only if valid; street-city links
are derived from containing admin areas matched to named settlement points; no nearest-city
heuristic is silently written to the verified city field.
"""
import collections
import csv
import json
import math
import re
import struct
import sys
import time
import unicodedata
import zlib
from pathlib import Path

from shapely.geometry import LineString, Point, Polygon, MultiPolygon
from shapely.ops import polygonize
from shapely.strtree import STRtree

SOURCE = 'OpenStreetMap'
PLACE_TYPES = {'country','state','region','district','county','municipality','city','town','village','hamlet','isolated_dwelling','farm','suburb','quarter','neighbourhood','locality'}
SETTLEMENT_TYPES = {'city', 'town', 'village', 'hamlet', 'isolated_dwelling', 'farm'}
NEIGHBORHOOD_TYPES = {'suburb','quarter','neighbourhood','locality'}
HIGHWAY_TYPES = {'motorway','trunk','primary','secondary','tertiary','unclassified','residential','living_street','service','pedestrian','road','track','footway','steps','path','cycleway','motorway_link','trunk_link','primary_link','secondary_link','tertiary_link'}
ALIAS_FIELDS = {'name:ru':'ru','name:kk':'kk','name:kz':'kk','alt_name':'alt','old_name':'old','short_name':'short','official_name':'official','loc_name':'local','int_name':'international','name:en':'en'}
TYPE_PATTERNS = [
    ('avenue',r'(?iu)(?:^|\s)(?:проспект|пр\.?-?т\.?|даңғылы|даңғыл|даңғылының)(?:\s|$)'),
    ('street',r'(?iu)(?:^|\s)(?:улица|ул\.?|көше|көшесі)(?:\s|$)'),
    ('lane',r'(?iu)(?:^|\s)(?:переулок|пер\.?|тұйық|тұйығы)(?:\s|$)'),
    ('boulevard',r'(?iu)(?:^|\s)(?:бульвар|б-р|желекжол)(?:\s|$)'),
    ('highway',r'(?iu)(?:^|\s)(?:шоссе|тасжол)(?:\s|$)'),
    ('square',r'(?iu)(?:^|\s)(?:площадь|алаңы)(?:\s|$)'),
]
TIMER=time.monotonic()

def log(*args): print('[%6.1fs]'%(time.monotonic()-TIMER),*args,flush=True)

def read_varint(buf,i):
    val=0;shift=0
    while True:
        b=buf[i]; i+=1;val|=(b&127)<<shift
        if b<128:return val,i
        shift+=7

def pb_fields(buf):
    i=0;n=len(buf)
    while i<n:
        key,i=read_varint(buf,i); typ=key&7; fid=key>>3
        if typ==0: val,i=read_varint(buf,i)
        elif typ==2:
            ln,i=read_varint(buf,i);val=buf[i:i+ln];i+=ln
        elif typ==1:val=buf[i:i+8];i+=8
        elif typ==5:val=buf[i:i+4];i+=4
        else:raise ValueError(f'unsupported wire type {typ}')
        yield fid, val

def pb_packed(buf):
    i=0
    while i<len(buf):
        v,i=read_varint(buf,i);yield v

def zz(v):return(v>>1)^(-(v&1))

def gettags(keys,values,strings):
    if not keys or not values:return {}
    return {strings[k]:strings[v] for k,v in zip(pb_packed(keys),pb_packed(values))}

def blobs(path):
    with open(path,'rb') as f:
        while 1:
            hdr_size=f.read(4)
            if not hdr_size:break
            hlen=struct.unpack('>I',hdr_size)[0]
            header=dict(pb_fields(f.read(hlen)))
            typ=header.get(1,b'');size=header.get(3)
            if size is None:raise ValueError('bad PBF block')
            raw=f.read(size)
            if typ!=b'OSMData':continue
            b=dict(pb_fields(raw))
            if 1 in b:yield b[1]
            elif 3 in b:yield zlib.decompress(b[3])
            else:raise ValueError('PBF compression type unsupported')

def primitive_group(block):
    strings=[];groups=[];granularity=100;lat_offset=0;lon_offset=0
    for k,val in pb_fields(block):
        if k==1:strings=[x.decode('utf-8','replace') for n,x in pb_fields(val) if n==1]
        elif k==2:groups.append(val)
        elif k==17:granularity=val
        elif k==19:lat_offset=zz(val)
        elif k==20:lon_offset=zz(val)
    return strings,groups,(granularity,lat_offset,lon_offset)

def coords(nlat,nlon,geo):
    scale,lat_offset,lon_offset=geo
    return (lat_offset+scale*nlat)/1e9,(lon_offset+scale*nlon)/1e9

def valid_coord(lat,lon):return 40<=lat<=56 and 46<=lon<=88

def to_tags(obj,strings):
    attrs=dict(pb_fields(obj))
    return attrs,gettags(attrs.get(2),attrs.get(3),strings)

def osm_way_midref(attrs):
    refs=attrs.get(8)
    if not refs:return None
    nums=list(pb_packed(refs));idx=len(nums)//2;prev=0
    for i,v in enumerate(nums):
        prev+=zz(v)
        if i==idx:return prev
    return None

def object_name(t):return (t.get('name') or t.get('name:ru') or t.get('name:kk') or '').strip()

def feat(kind,osmtype,ident,t,midref=None,lat=None,lon=None):
    return {'kind':kind,'osm_type':osmtype,'osm_id':ident,'name':object_name(t),
            'name_ru':t.get('name:ru',''),'name_kk':t.get('name:kk','') or t.get('name:kz',''),
            'object_type':t.get('place') if kind!='streets' else t.get('highway',''),
            'landuse':t.get('landuse',''),'admin_level':t.get('admin_level',''),
            'lat':lat,'lon':lon,'midref':midref,'explicit_city':t.get('addr:city','') or t.get('is_in:city',''),
            'explicit_province':t.get('addr:region','') or t.get('is_in:state',''),
            'explicit_district':t.get('addr:district',''),
            'tags':{k:v for k,v in t.items() if k in ALIAS_FIELDS or k in {'name','place','highway','boundary','landuse'}}}

def classify(t):
    if not object_name(t):return []
    cats=[];place=t.get('place','');hw=t.get('highway','')
    if place in PLACE_TYPES:cats.append('places')
    if hw in HIGHWAY_TYPES:cats.append('streets')
    if place in NEIGHBORHOOD_TYPES or t.get('landuse')=='residential':cats.append('living_areas')
    return cats

def members_of_relation(attrs):
    # Relation fields: roles_sid=8, memids=9, types=10 (according to OSM PBF proto)
    roles=list(pb_packed(attrs.get(8,b'')))
    deltas=list(pb_packed(attrs.get(9,b'')))
    types=list(pb_packed(attrs.get(10,b'')))
    node=0
    for typ,role,delta in zip(types,roles,deltas):
        node+=zz(delta)
        yield typ,role,node

def scan_features(source):
    feats=[];admin={};roads_midrefs=set();stat=collections.Counter()
    for ix,blob in enumerate(blobs(source)):
        strings,groups,geo=primitive_group(blob)
        for group in groups:
            for typ,obj in pb_fields(group):
                if typ not in (3,4):continue
                attrs,t=to_tags(obj,strings)
                if typ==3:
                    kinds=classify(t)
                    if not kinds:continue
                    ident=attrs.get(1);ref=osm_way_midref(attrs)
                    if ref is not None:roads_midrefs.add(ref)
                    for kind in kinds:feats.append(feat(kind,'way',ident,t,midref=ref));stat[kind+'_ways']+=1
                else:
                    ident=attrs.get(1)
                    if t.get('boundary')=='administrative' and t.get('admin_level','') in {'4','6','8'} and object_name(t):
                        mids=[]
                        for typcode,role,memberid in members_of_relation(attrs):
                            if typcode==1: mids.append(memberid) # only ways
                        if mids:
                            admin[ident]={'osm_id':ident,'name':object_name(t),'name_ru':t.get('name:ru',''),
                                          'name_kk':t.get('name:kk',''),'admin_level':int(t['admin_level']),
                                          'place':t.get('place',''),'way_ids':mids,'n_members':len(mids)}
                            stat['admin_relations']+=1
                    for kind in classify(t):
                        feats.append(feat(kind,'relation',ident,t));stat[kind+'_relations']+=1
        if (ix+1)%1200==0:log('feature pass:',ix+1,'blocks',len(feats),'named way/relation features')
    return feats,admin,roads_midrefs,stat

def scan_boundary_ways(source,admin):
    ids=set()
    for a in admin.values():ids.update(a['way_ids'])
    ret={};nodes=set()
    for ix,blob in enumerate(blobs(source)):
        strings,groups,geo=primitive_group(blob)
        for group in groups:
            for typ,obj in pb_fields(group):
                if typ!=3:continue
                attrs=dict(pb_fields(obj));ident=attrs.get(1)
                if ident not in ids:continue
                parts=list(pb_packed(attrs.get(8,b'')))
                i=0;ids_in_way=[]
                for v in parts:i+=zz(v);ids_in_way.append(i)
                if len(ids_in_way)>=2:
                    ret[ident]=ids_in_way;nodes.update(ids_in_way)
        if (ix+1)%1400==0:log('boundary way pass:',ix+1,'blocks',len(ret),'ways')
    return ret,nodes

def scan_nodes(source,need_nodes):
    coords_by_id={};node_feats=[];stat=collections.Counter();counter=0
    for ix,blob in enumerate(blobs(source)):
        strings,groups,geo=primitive_group(blob)
        for group in groups:
            for typ,obj in pb_fields(group):
                if typ==1:
                    attrs,t=to_tags(obj,strings)
                    ident=attrs.get(1)
                    if ident in need_nodes or classify(t):
                        lat,lon=coords(zz(attrs.get(8,0)),zz(attrs.get(9,0)),geo)
                        if ident in need_nodes:coords_by_id[ident]=(lon,lat)
                        if valid_coord(lat,lon):
                            for kind in classify(t):node_feats.append(feat(kind,'node',ident,t,lat=lat,lon=lon));stat[kind+'_nodes']+=1
                elif typ==2:
                    attrs=dict(pb_fields(obj))
                    idbuf=attrs.get(1,b'');latbuf=attrs.get(8,b'');lonbuf=attrs.get(9,b'')
                    kvbuf=attrs.get(10,b'')
                    kviter=iter(pb_packed(kvbuf));ident=lat=lon=0
                    for did,dlat,dlon in zip(pb_packed(idbuf),pb_packed(latbuf),pb_packed(lonbuf)):
                        ident+=zz(did);lat+=zz(dlat);lon+=zz(dlon);counter+=1
                        keep=ident in need_nodes
                        if keep:
                            lat1,lon1=coords(lat,lon,geo)
                            coords_by_id[ident]=(lon1,lat1)
                        # Every dense node is terminated by zero in keys_vals. Most are untagged.
                        if not kvbuf:continue
                        pair=next(kviter)
                        if pair==0:continue
                        tags={}
                        while pair!=0:
                            val=next(kviter);key=strings[pair]
                            if key in {'name','name:ru','name:kk','name:kz','place','highway','landuse','addr:city','addr:region','addr:district','alt_name','old_name','short_name','official_name','loc_name','int_name','name:en'}:
                                tags[key]=strings[val]
                            pair=next(kviter)
                        kinds=classify(tags)
                        if kinds:
                            lat1,lon1=coords(lat,lon,geo)
                            if valid_coord(lat1,lon1):
                                for kind in kinds:node_feats.append(feat(kind,'node',ident,tags,lat=lat1,lon=lon1));stat[kind+'_dense_nodes']+=1
        if (ix+1)%1200==0:log('node pass:',ix+1,'blocks; selected coords',len(coords_by_id),'named nodes',len(node_feats),'dense seen',counter)
    return node_feats,coords_by_id,stat,counter

def join_rings(lines):
    # Polygonize individual member ways. Isolated/open ways won't yield fake polygons.
    try:
        shapes=list(polygonize([LineString(p) for p in lines if len(p)>=2]))
        shapes=[s for s in shapes if s.is_valid and s.area>1e-10]
        if not shapes:return None
        # Nested polygons can include holes; ignore very small isolated overlaps.
        from shapely.ops import unary_union
        geometry=unary_union(shapes)
        if geometry.is_valid and not geometry.is_empty:return geometry
    except Exception:return None
    return None

def build_boundaries(admin,way_nodes,coordmap):
    out=[];shapes=[];stat=collections.Counter()
    for a in admin.values():
        lines=[];missing=0
        for wid in a['way_ids']:
            refs=way_nodes.get(wid)
            if not refs:missing+=1;continue
            pts=[coordmap.get(ref) for ref in refs]
            if any(p is None for p in pts):missing+=1;continue
            lines.append(pts)
        geom=join_rings(lines) if len(lines)>=1 and missing==0 else None
        # Do not claim a complete polygon when member ways are absent or open.
        a['geometry_status']='valid_polygon' if geom is not None else 'incomplete_or_open'
        a['centroid_lon']=round(geom.representative_point().x,7) if geom is not None else ''
        a['centroid_lat']=round(geom.representative_point().y,7) if geom is not None else ''
        stat[a['geometry_status']]+=1
        if geom is not None and geom.intersects(Polygon([(46,40),(88,40),(88,56),(46,56)])):
            shapes.append(geom);out.append(a)
    tree=STRtree(shapes) if shapes else None
    log('built administrative geometry:',dict(stat),'in bbox',len(out))
    return out,shapes,tree,stat

def normalize(s):
    s=unicodedata.normalize('NFKC',s).casefold().replace('ё','е')
    s=' '.join(re.findall(r'[\w]+',s,flags=re.UNICODE))
    return s

def street_type(name):
    for label,pat in TYPE_PATTERNS:
        if re.search(pat,name):return label
    return ''

def nearest_city_feature(pt,locations,citytree):
    if not citytree:return None,None
    # Use degree metric only to find candidates; compute exact haversine for display.
    x,y=pt.x,pt.y
    idx=citytree.nearest(pt)
    loc=locations[int(idx)]
    d=dist_km(y,x,loc['lat'],loc['lon'])
    return loc,d

def dist_km(lat1,lon1,lat2,lon2):
    a=math.radians(lat2-lat1);b=math.radians(lon2-lon1)
    v=math.sin(a/2)**2+math.cos(math.radians(lat1))*math.cos(math.radians(lat2))*math.sin(b/2)**2
    return 12742*math.atan2(math.sqrt(v),math.sqrt(max(0,1-v)))

def contains_boundaries(pt,boundaries,shapes,tree):
    if tree is None:return []
    idx=tree.query(pt,predicate='intersects')
    return [boundaries[int(i)] for i in idx]

def choose_admin(areas,lev):
    subset=[x for x in areas if x['admin_level']==lev]
    if not subset:return None
    # If overlaps (edge or embedded discontiguous areas), prefer smallest area using geometry if added.
    return sorted(subset,key=lambda v:v.get('area',float('inf')))[0]

def lookup_placement(feat,boundaries,shapes,tree,settlements,settlement_tree):
    if feat['lat'] is None or feat['lon'] is None:
        return {'admin4':'','admin6':'','admin8':'','city':'','location_method':'no_geometry','nearest_settlement':'','distance_km':''}
    point=Point(feat['lon'],feat['lat'])
    contained=contains_boundaries(point,boundaries,shapes,tree)
    a4=choose_admin(contained,4);a6=choose_admin(contained,6);a8=choose_admin(contained,8)
    nearest,d=nearest_city_feature(point,settlements,settlement_tree)
    city='';method='unresolved'
    if feat['explicit_city']:
        city=feat['explicit_city'];method='explicit_osm_tag'
    elif a8 is not None and nearest is not None and normalize(a8['name']) in {normalize(nearest['name']),normalize(nearest['name_ru']),normalize(nearest['name_kk'])}:
        # Exact names and matching polygon; nearest is only hint to confirm settlement type.
        city=a8['name'];method='polygon_and_settlement_name'
    # If no explicit city or validated city polygon, city is deliberately NULL.
    if not city and contained:method='admin_polygon_only'
    return {'admin4':feat['explicit_province'] or (a4['name'] if a4 else ''),
            'admin6':feat['explicit_district'] or (a6['name'] if a6 else ''),
            'admin8':a8['name'] if a8 else '',
            'city':city,'location_method':method,
            'nearest_settlement':nearest['name'] if nearest else '',
            'distance_km':round(d,2) if d is not None else ''}

def write_csv(path,columns,rows):
    with open(path,'w',newline='',encoding='utf-8') as f:
        wr=csv.DictWriter(f,fieldnames=columns,extrasaction='ignore');wr.writeheader();wr.writerows(rows)

def main():
    if len(sys.argv)!=3:
        print('Usage: python build_reference_v2.py kazakhstan.osm.pbf output-dir');sys.exit(2)
    source=Path(sys.argv[1]);out=Path(sys.argv[2]);out.mkdir(parents=True,exist_ok=True)
    if not source.is_file():raise FileNotFoundError(source)
    log('input',source.name,'size',source.stat().st_size)
    feats,admin,mids,stats=scan_features(source)
    log('pass1 result',len(feats),'features; admin relations',len(admin),'midrefs',len(mids))
    boundary_ways,bnodes=scan_boundary_ways(source,admin)
    all_ids=mids|bnodes
    log('pass2 result',len(boundary_ways),'boundary ways; unique coords required',len(all_ids))
    node_feats,coordinates,ns,ncount=scan_nodes(source,all_ids)
    log('pass3 result',len(node_feats),'named node features;',len(coordinates),'coordinates of',len(all_ids),'requested')
    feats+=node_feats
    for feat0 in feats:
        ref=feat0.get('midref')
        if ref is not None and ref in coordinates:
            feat0['lon'],feat0['lat']=coordinates[ref]
    # Remove any unmatched way features which are outside Kazakhstan's broad bbox.
    feats=[f for f in feats if f['lat'] is None or valid_coord(f['lat'],f['lon'])]
    boundaries,polygons,tree,geo_stats=build_boundaries(admin,boundary_ways,coordinates)
    for i,b in enumerate(boundaries):b['area']=polygons[i].area
    settlements=[f for f in feats if f['kind']=='places' and f['object_type'] in SETTLEMENT_TYPES and f['lat'] is not None and f['osm_type']=='node']
    # Way place polygons may also have midpoint representative without validity guarantee, excluded.
    place_tree=STRtree([Point(f['lon'],f['lat']) for f in settlements]) if settlements else None
    log('settlement point candidates',len(settlements))
    placecols=['osm_type','osm_id','name','name_ru','name_kk','place_type','lat','lon','province','district','admin8','city','location_method','nearest_settlement','nearest_settlement_km','source']
    streetcols=['osm_type','osm_id','name','name_ru','name_kk','street_type','highway','lat','lon','province','district','admin8','city','location_method','nearest_settlement','nearest_settlement_km','source']
    livingcols=['osm_type','osm_id','name','name_ru','name_kk','area_type','lat','lon','province','district','admin8','city','location_method','nearest_settlement','nearest_settlement_km','source']
    aliascols=['object_kind','osm_type','osm_id','alias','lang_or_tag','normalized_alias']
    admincols=['osm_relation_id','name','name_ru','name_kk','admin_level','place','geometry_status','center_lat','center_lon','way_members','source']
    count=collections.Counter();aliases=set();has_city=collections.Counter();methods=collections.Counter()
    with (out/'places.csv').open('w',newline='',encoding='utf-8') as pf,(out/'streets.csv').open('w',newline='',encoding='utf-8') as sf,(out/'living_areas.csv').open('w',newline='',encoding='utf-8') as lf,(out/'aliases.csv').open('w',newline='',encoding='utf-8') as af:
        outputs={}
        for key,fp,cols in [('places',pf,placecols),('streets',sf,streetcols),('living_areas',lf,livingcols),('aliases',af,aliascols)]:
            wr=csv.DictWriter(fp,fieldnames=cols);wr.writeheader();outputs[key]=wr
        for idx,f in enumerate(feats):
            if f['kind']=='streets' and f['osm_type']!='way':
                # Most named pedestrian nodes or relation roads are non-street entities. Keep only named way streets.
                continue
            place=lookup_placement(f,boundaries,polygons,tree,settlements,place_tree)
            kind=f['kind']
            row={'osm_type':f['osm_type'],'osm_id':f['osm_id'],'name':f['name'],
                 'name_ru':f['name_ru'],'name_kk':f['name_kk'],
                 'lat':round(f['lat'],7) if f['lat'] is not None else '',
                 'lon':round(f['lon'],7) if f['lon'] is not None else '',
                 'province':place['admin4'],'district':place['admin6'],'admin8':place['admin8'],
                 'city':place['city'],'location_method':place['location_method'],
                 'nearest_settlement':place['nearest_settlement'],
                 'nearest_settlement_km':place['distance_km'],'source':SOURCE,
                 'place_type':f['object_type'],
                 'area_type':f['object_type'] or f['landuse'],
                 'street_type':street_type(f['name']),'highway':f['object_type']}
            outputs[kind].writerow({k:row.get(k,'') for k in outputs[kind].fieldnames})
            count[kind]+=1;methods[place['location_method']]+=1
            if place['city']:has_city[kind]+=1
            for tag,lang in ALIAS_FIELDS.items():
                value=f['tags'].get(tag,'')
                if not value:continue
                # OSM alt_name/old_name lists may contain semicolon-separated variants.
                for alias in value.split(';'):
                    alias=alias.strip()
                    if alias and normalize(alias)!=normalize(f['name']):
                        outputs['aliases'].writerow({'object_kind':kind,'osm_type':f['osm_type'],
                                  'osm_id':f['osm_id'],'alias':alias,'lang_or_tag':lang,
                                  'normalized_alias':normalize(alias)})
                        count['aliases']+=1
            if (idx+1)%30000==0:log('linked',idx+1,'/',len(feats),'features; cities',dict(has_city))
    write_csv(out/'admin_areas.csv',admincols,[{'osm_relation_id':a['osm_id'],'name':a['name'],
        'name_ru':a['name_ru'],'name_kk':a['name_kk'],'admin_level':a['admin_level'],
        'place':a['place'],'geometry_status':a['geometry_status'],
        'center_lat':a['centroid_lat'],'center_lon':a['centroid_lon'],
        'way_members':a['n_members'],'source':SOURCE} for a in admin.values()])
    count['admin_areas']=len(admin)
    stamp=re.search(r'kazakhstan-(\d{2})(\d{2})(\d{2})',source.name)
    date_from_name=(f'20{stamp.group(1)}-{stamp.group(2)}-{stamp.group(3)}' if stamp else None)
    report={'source_file':source.name,'source_bytes':source.stat().st_size,
            'osm_date_from_filename':date_from_name,'processing':{'count':dict(count),
            'admin_geometry_status':dict(geo_stats),'location_methods':dict(methods),
            'rows_with_verified_city':dict(has_city),'dense_nodes_scanned':ncount,
            'settlement_node_candidates':len(settlements),
            'geometry_nodes_requested':len(all_ids),'geometry_nodes_found':len(coordinates)},
            'limitations':['Not a complete KATO dataset; no official KATO IDs.',
              'Admin polygon may be missing for incomplete OSM boundaries; city remains blank unless explicitly tagged or a valid polygon name matches nearest settlement node.',
              'nearest_settlement is advisory only; do not silently treat it as verified city.',
              'OSM way features may be repeated per street; join identical names only within verified place and provenance.',
              'OSM PBF extract may include small border-area geometry; validate against Kazakhstan-specific boundaries before claiming national exhaustive accuracy.',
              'Coordinates from way midpoint node, not exact feature geometry centroid.',
              'Original OSM attribution and ODbL license must be retained.']}
    (out/'quality_report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    log('FINISHED',count,'verified_city',has_city,'methods',methods)

if __name__=='__main__':main()

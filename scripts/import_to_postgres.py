#!/usr/bin/env python3
"""Load validated CSV reference bundle to PostgreSQL in one transaction.
No deletion of app tables: uses only jana_reference.*.

Requires: pip install "psycopg[binary]"
Usage: DATABASE_URL='postgresql://...' python scripts/import_to_postgres.py
To re-import into already filled tables: add --replace (transaction-safe).
"""
from __future__ import annotations
import argparse
import csv
import os
import sys
from pathlib import Path

try:
    import psycopg
    from psycopg import sql
except ImportError as e:
    raise SystemExit('Install dependency: pip install "psycopg[binary]"') from e

TABLES=('regions','districts','settlements','places','streets','living_areas','admin_areas','aliases')

def run():
    parser=argparse.ArgumentParser(description='Import offline OSM reference CSV into a dedicated PostgreSQL schema.')
    parser.add_argument('--replace',action='store_true',help='Replace only jana_reference tables atomically.')
    parser.add_argument('--data-dir',type=Path,default=Path(__file__).resolve().parents[1]/'data'/'reference')
    opts=parser.parse_args()
    url=os.getenv('DATABASE_URL')
    if not url:raise SystemExit('Set DATABASE_URL in environment (do not commit actual passwords).')
    ddl=Path(__file__).resolve().with_name('create_reference_tables.sql').read_text(encoding='utf-8')
    with psycopg.connect(url) as conn:
        with conn.transaction():
            # psycopg.connect defaults to a transaction; transaction() is nested savepoint if needed.
            conn.execute(ddl)
            counts={}
            for table in TABLES:
                path=opts.data_dir/(table+'.csv')
                if not path.is_file():raise FileNotFoundError(path)
                with path.open('r',encoding='utf-8',newline='') as f:
                    cols=next(csv.reader(f))
                if not cols:raise ValueError(f'Empty header: {path}')
                dest=sql.Identifier('jana_reference',table)
                current=conn.execute(sql.SQL('SELECT COUNT(*) FROM {}').format(dest)).fetchone()[0]
                if current and not opts.replace:
                    raise RuntimeError(f'{table} already contains {current} rows; run with --replace to replace reference data')
                if current and opts.replace:
                    conn.execute(sql.SQL('TRUNCATE TABLE {}').format(dest))
                query=sql.SQL("COPY {} ({}) FROM STDIN WITH (FORMAT CSV, HEADER TRUE, NULL '')").format(dest,sql.SQL(',').join(map(sql.Identifier,cols)))
                with conn.cursor() as cursor:
                    with cursor.copy(query) as copy:
                        with path.open('rb') as data:
                            while True:
                                chunk=data.read(1024*1024)
                                if not chunk:break
                                copy.write(chunk)
                counts[table]=conn.execute(sql.SQL('SELECT COUNT(*) FROM {}').format(dest)).fetchone()[0]
            print('Imported atomically into schema jana_reference:',counts)

if __name__=='__main__':run()

# c 2025-01-27
# m 2025-08-09

import datetime as dt
import json
import sqlite3 as sql
import types

from constants import *
import errors
import utils


class Cursor:
    '''
    Context manager for a database connection and cursor
    '''

    def __init__(self, path: str) -> None:
        self.path: str = path

    def __enter__(self) -> sql.Cursor:
        self.con: sql.Connection = sql.connect(self.path)
        self.con.row_factory = sql.Row
        self.cur: sql.Cursor = self.con.cursor()
        self.cur.execute('BEGIN')
        return self.cur

    def __exit__(self, exc_type: type, exc_val: Exception, exc_tb: types.TracebackType) -> None:
        self.cur.close()

        if exc_type is exc_val is exc_tb is None:
            self.con.commit()
        else:
            self.con.rollback()

        self.con.close()


@errors.safelogged(int)
def handle_tops(tops: list[dict], uid: str, name: str) -> int:
    for top in tops:
        top.pop('timestamp')
        top.pop('zoneId')
        top.pop('zoneName')

    with Cursor(FILE_DB) as db:
        db.execute(f'''
            CREATE TABLE IF NOT EXISTS Tops2 (
                mapName   TEXT,
                mapUid    VARCHAR(27),
                timestamp INT,
                tops      TEXT
            );
        ''')

        db.execute(f'''
            INSERT INTO Tops2 (
                mapName,
                mapUid,
                timestamp,
                tops
            ) VALUES (
                "{utils.strip_format_codes(name)}",
                "{uid}",
                {utils.stamp()},
                "{str(tops)}"
            );
        ''')

    return tops[0]['score']


def get_next_warrior() -> int:
    seasonal: int = read_timestamp('next_warrior_seasonal')
    seasonal = seasonal if seasonal else MAX_TIMESTAMP

    totd: int = read_timestamp('next_warrior_totd')
    totd = totd if totd else MAX_TIMESTAMP

    weekly: int = read_timestamp('next_warrior_weekly')
    weekly = weekly if weekly else MAX_TIMESTAMP

    return min(seasonal, totd, weekly)


@errors.safelogged(list, log=False)
def read_table(table: str) -> list[dict]:
    with Cursor(FILE_DB) as db:
        return [dict(item) for item in db.execute(f'SELECT * FROM {table}').fetchall()]


@errors.safelogged(int, log=False)
def read_timestamp(key: str) -> int:
    with Cursor(FILE_DB) as db:
        return db.execute(f'SELECT * FROM Timestamps WHERE key = "{key}"').fetchone()[1]


@errors.safelogged()
def tables_to_json() -> None:
    for table_name, output_file in (
        ('Seasonal', FILE_SEASONAL),
        ('Totd',     FILE_TOTD),
        ('Weekly',   FILE_WEEKLY),
    ):
        with open(output_file, 'w', newline='\n') as f:
            json.dump({item['mapUid']: item for item in read_table(table_name)}, f, indent=4)
            f.write('\n')

    with open(FILE_ZONE, 'w', newline='\n') as f:
        json.dump({item['zoneId']: item for item in read_table('Zone')}, f, indent=4)
        f.write('\n')


@errors.safelogged()
def warriors_to_json() -> None:
    warriors: dict = {}

    for table in ('Seasonal', 'Weekly', 'Totd', 'Other'):
        warriors[table] = read_table(f'Warrior{table}')

        if table == 'Totd':
            warriors[table] = sorted(warriors[table], key=lambda x: x['date'])  # todo: re-sort table to avoid this

    with open(FILE_WARRIOR, 'w', newline='\n') as f:
        json.dump(warriors, f, indent=4)
        f.write('\n')

    with open(FILE_WARRIOR_NEXT, 'w', newline='\n') as f:
        f.write(f'[{get_next_warrior()}]\n')


@errors.safelogged()
def write_timestamp(key: str, ts: int) -> None:
    with Cursor(FILE_DB) as db:
        db.execute('CREATE TABLE IF NOT EXISTS Timestamps (key TEXT PRIMARY KEY, ts INT, utc CHAR(19));')
        db.execute(f'REPLACE INTO Timestamps (key, ts, utc) VALUES ("{key}", "{ts}", "{dt.datetime.fromtimestamp(ts, dt.UTC).strftime('%F %T')}");')

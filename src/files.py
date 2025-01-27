# c 2025-01-27
# m 2025-01-27

from errors import safelogged
from utils import *


@safelogged(str, True)
def read_db_key_val(key: str) -> str:
    with sql.connect(FILE_DB) as con:
        cur: sql.Cursor = con.cursor()
        return cur.execute(f'SELECT * FROM KeyVals WHERE key = "{key}"').fetchone()[1]


@safelogged(list)
def read_table(table: str) -> list[dict]:
    with sql.connect(FILE_DB) as con:
        con.row_factory = sql.Row
        cur: sql.Cursor = con.cursor()

        return [dict(item) for item in cur.execute(f'SELECT * FROM {table}').fetchall()]


@safelogged()
def tables_to_json() -> None:
    for table_name, output_file in (
        ('Royal',    FILE_ROYAL),
        ('Seasonal', FILE_SEASONAL),
        ('Totd',     FILE_TOTD),
        # ('Warrior',  FILE_WARRIOR),
        ('Weekly',   FILE_WEEKLY),
    ):
        with open(output_file, 'w', newline='\n') as f:
            json.dump({item['mapUid']: item for item in read_table(table_name)}, f, indent=4)
            f.write('\n')


@safelogged()
def warriors_to_json() -> None:
    pass


@safelogged()
def write_db_key_val(key: str, val) -> None:
    with sql.connect(FILE_DB) as con:
        cur: sql.Cursor = con.cursor()
        cur.execute('BEGIN')
        cur.execute('CREATE TABLE IF NOT EXISTS KeyVals (key TEXT PRIMARY KEY, val TEXT);')
        cur.execute(f'REPLACE INTO KeyVals (key, val) VALUES ("{key}", "{val}")')
        cur.execute(f'REPLACE INTO KeyVals (key, val) VALUES ("last_updated", "{stamp()}")')

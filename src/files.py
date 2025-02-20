# c 2025-01-27
# m 2025-02-20

from errors import safelogged
from types import TracebackType
from utils import *


class Cursor:
    '''
    Context manager for a database connection and cursor
    '''

    def __init__(self, path: str) -> None:
        self.path = path

    def __enter__(self):
        self.con = sql.connect(self.path)
        self.con.row_factory = sql.Row
        self.cur = self.con.cursor()
        self.cur.execute('BEGIN')
        return self.cur

    def __exit__(self, exc_type: type, exc_val: Exception, exc_tb: TracebackType) -> None:
        self.cur.close()

        if exc_type is exc_val is exc_tb is None:
            self.con.commit()
        else:
            self.con.rollback()

        self.con.close()


@safelogged()
def handle_tops(tops: list[dict], uid: str) -> int:
    with Cursor(FILE_DB) as db:
        db.execute(f'''
            CREATE TABLE IF NOT EXISTS Tops (
                timestamp INT PRIMARY KEY,
                mapUid    VARCHAR(27),
                score1    INT,
                score2    INT,
                score3    INT,
                score4    INT,
                score5    INT,
                account1  TEXT,
                account2  TEXT,
                account3  TEXT,
                account4  TEXT,
                account5  TEXT
            );
        ''')

        db.execute(f'''
            INSERT INTO Tops (
                timestamp,
                mapUid,
                score1,
                score2,
                score3,
                score4,
                score5,
                account1,
                account2,
                account3,
                account4,
                account5
            ) VALUES (
                "{stamp()}",
                "{uid}",
                "{tops[0]['score']}",
                "{tops[1]['score']}",
                "{tops[2]['score']}",
                "{tops[3]['score']}",
                "{tops[4]['score']}",
                "{tops[0]['accountId']}",
                "{tops[1]['accountId']}",
                "{tops[2]['accountId']}",
                "{tops[3]['accountId']}",
                "{tops[4]['accountId']}"
            )
        ''')

    return tops[0]['score']


@safelogged(str, True)
def read_db_key_val(key: str) -> str:
    with Cursor(FILE_DB) as db:
        return db.execute(f'SELECT * FROM KeyVals WHERE key = "{key}"').fetchone()[1]


@safelogged(list)
def read_table(table: str) -> list[dict]:
    with Cursor(FILE_DB) as db:
        return [dict(item) for item in db.execute(f'SELECT * FROM {table}').fetchall()]


@safelogged()
def tables_to_json() -> None:
    for table_name, output_file in (
        ('Royal',    FILE_ROYAL),
        ('Seasonal', FILE_SEASONAL),
        ('Totd',     FILE_TOTD),
        ('Weekly',   FILE_WEEKLY),
    ):
        with open(output_file, 'w', newline='\n') as f:
            json.dump({item['mapUid']: item for item in read_table(table_name)}, f, indent=4)
            f.write('\n')


@safelogged()
def warriors_to_json() -> None:
    warriors = {}

    for table in ('Seasonal', 'Weekly', 'Totd', 'Other'):
        warriors[table] = read_table(f'Warrior{table}')

    with open(FILE_WARRIOR, 'w', newline='\n') as f:
        json.dump(warriors, f, indent=4)
        f.write('\n')


@safelogged()
def warriors_to_old_json() -> None:
    warriors = {}

    for table_type in ('Seasonal', 'Totd', 'Other'):
        for map in read_table(f'Warrior{table_type}'):
            map['uid'] = map['mapUid']
            map.pop('mapUid')

            if table_type == 'Seasonal':
                map['clubId'] = 0
            elif table_type == 'Other':
                map['campaignIndex'] = map['mapIndex']
                map.pop('mapIndex')

            warriors[map['uid']] = dict(sorted(map.items()))

    with open(FILE_WARRIOR_OLD, 'w', newline='\n') as f:
        json.dump(warriors, f, indent=4)
        f.write('\n')


@safelogged()
def write_db_key_val(key: str, val) -> None:
    with Cursor(FILE_DB) as db:
        db.execute('CREATE TABLE IF NOT EXISTS KeyVals (key TEXT PRIMARY KEY, val TEXT);')
        db.execute(f'REPLACE INTO KeyVals (key, val) VALUES ("{key}", "{val}")')
        db.execute(f'REPLACE INTO KeyVals (key, val) VALUES ("last_updated", "{stamp()}")')

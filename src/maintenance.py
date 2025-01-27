# c 2025-01-27
# m 2025-01-27

from utils import *


def migrate_old_warriors() -> None:
    with sql.connect('C:/Users/Ezio/Code/e416dev_api/tm.db') as con:
        con.row_factory = sql.Row
        cur: sql.Cursor = con.cursor()
        cur.execute('BEGIN')

        camp: list[dict] = []
        for entry in cur.execute('SELECT * FROM CampaignWarriors').fetchall():
            camp.append(dict(entry))

        other: list[dict] = []
        for entry in cur.execute('SELECT * FROM OtherWarriors').fetchall():
            other.append(dict(entry))

        totd: list[dict] = []
        for entry in cur.execute('SELECT * FROM TotdWarriors').fetchall():
            totd.append(dict(entry))

    def migrate_seasonal() -> None:
        with sql.connect(FILE_DB) as con:
            cur: sql.Cursor = con.cursor()

            cur.execute('BEGIN')

            cur.execute('DROP TABLE IF EXISTS WarriorSeasonal')
            cur.execute(f'''
                CREATE TABLE IF NOT EXISTS WarriorSeasonal (
                    authorTime  INT,
                    campaignId  INT,
                    custom      INT,
                    mapUid      VARCHAR(27) PRIMARY KEY,
                    name        TEXT,
                    reason      TEXT,
                    warriorTime INT,
                    worldRecord INT
                );
            ''')

            for map in camp:
                cur.execute(f'''
                    INSERT INTO WarriorSeasonal (
                        authorTime,
                        campaignId,
                        custom,
                        mapUid,
                        name,
                        reason,
                        warriorTime,
                        worldRecord
                    ) VALUES (
                        "{map['authorTime']}",
                        "{map['campaignId']}",
                        {f'"{map['custom']}"' if 'custom' in map and map['custom'] is not None else 'NULL'},
                        "{map['uid']}",
                        "{map['name']}",
                        {f'"{map['reason']}"' if 'reason' in map and map['reason'] is not None else 'NULL'},
                        "{map['warriorTime']}",
                        "{map['worldRecord']}"
                    )
                ''')

    def migrate_other() -> None:
        with sql.connect(FILE_DB) as con:
            cur: sql.Cursor = con.cursor()

            cur.execute('BEGIN')

            cur.execute('DROP TABLE IF EXISTS WarriorOther')
            cur.execute(f'''
                CREATE TABLE IF NOT EXISTS WarriorOther (
                    authorTime   INT,
                    campaignId   INT,
                    campaignName TEXT,
                    clubId       INT,
                    clubName     TEXT,
                    custom       INT,
                    mapIndex     INT,
                    mapUid       VARCHAR(27) PRIMARY KEY,
                    name         TEXT,
                    reason       TEXT,
                    warriorTime  INT,
                    worldRecord  INT
                );
            ''')

            for map in other:
                cur.execute(f'''
                    INSERT INTO WarriorOther (
                        authorTime,
                        campaignId,
                        campaignName,
                        clubId,
                        clubName,
                        custom,
                        mapIndex,
                        mapUid,
                        name,
                        reason,
                        warriorTime,
                        worldRecord
                    ) VALUES (
                        "{map['authorTime']}",
                        "{map['campaignId']}",
                        "{map['campaignName']}",
                        "{map['clubId']}",
                        "{map['clubName']}",
                        {f'"{map['custom']}"' if 'custom' in map and map['custom'] is not None else 'NULL'},
                        "{map['campaignIndex']}",
                        "{map['uid']}",
                        "{map['name']}",
                        {f'"{map['reason']}"' if 'reason' in map and map['reason'] is not None else 'NULL'},
                        "{map['warriorTime']}",
                        "{map['worldRecord']}"
                    )
                ''')

    def migrate_totd() -> None:
        with sql.connect(FILE_DB) as con:
            cur: sql.Cursor = con.cursor()

            cur.execute('BEGIN')

            cur.execute('DROP TABLE IF EXISTS WarriorTotd')
            cur.execute(f'''
                CREATE TABLE IF NOT EXISTS WarriorTotd (
                    authorTime  INT,
                    custom      INT,
                    date        CHAR(10),
                    mapUid      VARCHAR(27) PRIMARY KEY,
                    name        TEXT,
                    reason      TEXT,
                    warriorTime INT,
                    worldRecord INT
                );
            ''')

            for map in totd:
                cur.execute(f'''
                    INSERT INTO WarriorTotd (
                        authorTime,
                        custom,
                        date,
                        mapUid,
                        name,
                        reason,
                        warriorTime,
                        worldRecord
                    ) VALUES (
                        "{map['authorTime']}",
                        {f'"{map['custom']}"' if 'custom' in map and map['custom'] is not None else 'NULL'},
                        "{map['date']}",
                        "{map['uid']}",
                        "{map['name']}",
                        {f'"{map['reason']}"' if 'reason' in map and map['reason'] is not None else 'NULL'},
                        "{map['warriorTime']}",
                        "{map['worldRecord']}"
                    )
                ''')

    migrate_seasonal()
    migrate_other()
    migrate_totd()

    pass


if __name__ == '__main__':
    # migrate_old_warriors()
    pass

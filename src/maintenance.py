# c 2025-01-27
# m 2025-04-02

from datetime import timezone

from nadeo_api import live

from api import *
from files import *
from github import *
from utils import *
from webhooks import *


def display_db_epoch_vals() -> None:
    table = read_table('KeyVals')

    stage2 = []
    for i, _ in enumerate(table):
        stage2.append((table[i]['key'], int(table[i]['val'])))

    stage3 = sorted(stage2, key=lambda pair: pair[1])

    for key, val in stage3:
        diff = val - stamp()
        print(
            f'{key:<16}',
            f'{dt.fromtimestamp(int(val), timezone.utc).strftime('%Y-%m-%d %H:%M:%Sz')}',
            f'({'in ' if diff > 0 else ''}{format_long_time(abs(diff))}{' ago' if diff <= 0 else ''})'
        )


def migrate_old_warriors() -> None:
    with Cursor('C:/Users/Ezio/Code/e416dev_api/tm.db') as db:
        camp: list[dict] = []
        for entry in db.execute('SELECT * FROM CampaignWarriors').fetchall():
            camp.append(dict(entry))

        other: list[dict] = []
        for entry in db.execute('SELECT * FROM OtherWarriors').fetchall():
            other.append(dict(entry))

        totd: list[dict] = []
        for entry in db.execute('SELECT * FROM TotdWarriors').fetchall():
            totd.append(dict(entry))

    def migrate_seasonal() -> None:
        with Cursor(FILE_DB) as db:
            db.execute('DROP TABLE IF EXISTS WarriorSeasonal')
            db.execute(f'''
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
                db.execute(f'''
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
        with Cursor(FILE_DB) as db:
            db.execute('DROP TABLE IF EXISTS WarriorOther')
            db.execute(f'''
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
                db.execute(f'''
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
        with Cursor(FILE_DB) as db:
            db.execute('DROP TABLE IF EXISTS WarriorTotd')
            db.execute(f'''
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
                db.execute(f'''
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


def test_club_campaign_error() -> None:
    tokens = get_tokens()

    req = live.get(
        tokens['live'],
        'api/token/club/17893/campaign/3348'
    )

    pass


def test_unicode_encode_error() -> None:
    s = 'Ma\u0142opolskie'
    with open('locals.txt', 'a', newline='\n') as f:
        f.write(f'{s.encode('unicode-escape').decode('ascii')}\n')

    log(s)
    # with open('locals.txt', 'ab') as f:
    #     f.write(s.encode())


def warriors_to_github() -> None:
    warriors_to_json()
    to_github()
    # warriors_to_old_json()
    # to_github_old()


if __name__ == '__main__':
    # display_db_epoch_vals()
    # migrate_old_warriors()
    # test_unicode_encode_error()
    # warriors_to_github()
    # to_github_old()
    # test_club_campaign_error()
    # print(webhook_seasonal(None))

    pass

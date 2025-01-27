# c 2025-01-27
# m 2025-01-27

import zipfile

from nadeo_api import live

from api import get_map_infos
from errors import safelogged
from files import read_db_key_val, write_db_key_val
from utils import *


@safelogged(bool)
def schedule_royal_maps(tokens: dict) -> bool:
    time.sleep(WAIT_TIME)
    maps_royal: dict = live.maps_royal(tokens['live'], 99)

    if os.path.isfile(FILE_ROYAL_RAW):
        ts: int = stamp()
        with zipfile.ZipFile(f'{DIR_DATA}/history/royal_raw_{ts}.zip', 'w', zipfile.ZIP_LZMA, compresslevel=5) as zip:
            zip.write(FILE_ROYAL_RAW, 'royal_raw.json')

    with open(FILE_ROYAL_RAW, 'w', newline='\n') as f:
        json.dump(maps_royal, f, indent=4)
        f.write('\n')

    with sql.connect(FILE_DB) as con:
        cur: sql.Cursor = con.cursor()

        cur.execute('BEGIN')
        cur.execute('DROP TABLE IF EXISTS Royal')
        cur.execute(f'''
            CREATE TABLE IF NOT EXISTS Royal (
                author          CHAR(36),
                authorTime      INT,
                bronzeTime      INT,
                campaignId      INT,
                goldTime        INT,
                mapId           CHAR(36),
                mapUid          VARCHAR(27) PRIMARY KEY,
                month           INT,
                monthDay        INT,
                name            TEXT,
                number          INT,
                silverTime      INT,
                submitter       CHAR(36),
                timestampEnd    INT,
                timestampStart  INT,
                timestampUpload INT,
                weekDay         INT,
                year            INT
            );
        ''')

        mapUids: set = set()

        number: int = 0

        for month in reversed(maps_royal['monthList']):
            for map in month['days']:
                mapUid: str = map['mapUid']
                if len(mapUid) == 0:
                    break

                if mapUid in mapUids:
                    # log(f'schedule_royal_maps duplicate: {mapUid}')
                    continue
                else:
                    mapUids.add(mapUid)

                number += 1
                cur.execute(f'''
                    INSERT INTO Royal (
                        campaignId,
                        mapUid,
                        month,
                        monthDay,
                        number,
                        timestampEnd,
                        timestampStart,
                        weekDay,
                        year
                    ) VALUES (
                        "{map['campaignId']}",
                        "{mapUid}",
                        "{month['month']}",
                        "{map['monthDay']}",
                        "{number}",
                        "{map['endTimestamp']}",
                        "{map['startTimestamp']}",
                        "{map['day']}",
                        "{month['year']}"
                    )
                ''')

    write_db_key_val('next_royal', maps_royal['nextRequestTimestamp'])
    return True


@safelogged(bool)
def schedule_seasonal_maps(tokens: dict) -> bool:
    time.sleep(WAIT_TIME)
    maps_seasonal: dict = live.maps_campaign(tokens['live'], 99)

    if os.path.isfile(FILE_SEASONAL_RAW):
        ts: int = stamp()
        with zipfile.ZipFile(f'{DIR_DATA}/history/seasonal_raw_{ts}.zip', 'w', zipfile.ZIP_LZMA, compresslevel=5) as zip:
            zip.write(FILE_SEASONAL_RAW, 'seasonal_raw.json')

    with open(FILE_SEASONAL_RAW, 'w', newline='\n') as f:
        json.dump(maps_seasonal, f, indent=4)
        f.write('\n')

    with sql.connect(FILE_DB) as con:
        cur: sql.Cursor = con.cursor()

        cur.execute('BEGIN')
        cur.execute('DROP TABLE IF EXISTS Seasonal')
        cur.execute(f'''
            CREATE TABLE IF NOT EXISTS Seasonal (
                author               CHAR(36),
                authorTime           INT,
                bronzeTime           INT,
                campaignId           INT,
                campaignIndex        INT,
                goldTime             INT,
                leaderboardGroupUid  CHAR(36),
                mapId                CHAR(36),
                mapIndex             INT,
                mapUid               VARCHAR(27) PRIMARY KEY,
                name                 VARCHAR(16),
                number               INT,
                seasonUid            CHAR(36),
                silverTime           INT,
                submitter            CHAR(36),
                timestampEdition     INT,
                timestampEnd         INT,
                timestampPublished   INT,
                timestampRankingSent INT,
                timestampStart       INT,
                timestampUpload      INT
            );
        ''')

        for i, campaign in enumerate(reversed(maps_seasonal['campaignList'])):
            timestampRankingSent: int | None = campaign['rankingSentTimestamp']

            for map in campaign['playlist']:
                cur.execute(f'''
                    INSERT INTO Seasonal (
                        campaignId,
                        campaignIndex,
                        leaderboardGroupUid,
                        mapIndex,
                        mapUid,
                        number,
                        seasonUid,
                        timestampEdition,
                        timestampEnd,
                        timestampPublished,
                        timestampRankingSent,
                        timestampStart
                    ) VALUES (
                        "{campaign['id']}",
                        "{i}",
                        "{campaign['leaderboardGroupUid']}",
                        "{map['position']}",
                        "{map['mapUid']}",
                        "{i * 25 + map['position'] + 1}",
                        "{campaign['seasonUid']}",
                        "{campaign['editionTimestamp']}",
                        "{campaign['endTimestamp']}",
                        "{campaign['publicationTimestamp']}",
                        {f'"{timestampRankingSent}"' if timestampRankingSent is not None else 'NULL'},
                        "{campaign['startTimestamp']}"
                    )
                ''')

    write_db_key_val('next_seasonal', maps_seasonal['nextRequestTimestamp'])
    write_db_key_val('warrior_seasonal', maps_seasonal['nextRequestTimestamp'] + 60*60*24*14)
    return True


@safelogged(bool)
def schedule_seasonal_warriors(tokens: dict) -> bool:
    maps: dict = {}

    with sql.connect(FILE_DB) as con:
        con.row_factory = sql.Row
        cur: sql.Cursor = con.cursor()

        cur.execute('BEGIN')
        for entry in cur.execute('SELECT * FROM Seasonal ORDER BY campaignIndex DESC').fetchmany(25):
            map = dict(entry)
            maps[map['mapUid']] = map

    for uid, map in maps.items():
        log(f'info: getting records for "{map['name']}"')

        time.sleep(WAIT_TIME)
        req: dict = live.get(
            tokens['live'],
            f'api/token/leaderboard/group/Personal_Best/map/{uid}/top'
        )

        maps[uid]['worldRecord'] = req['tops'][0]['top'][0]['score']
        maps[uid]['warriorTime'] = get_warrior_time(map['authorTime'], map['worldRecord'])

    with sql.connect(FILE_DB) as con:
        cur: sql.Cursor = con.cursor()

        cur.execute('BEGIN')
        cur.execute(f'''
            CREATE TABLE IF NOT EXISTS WarriorSeasonal (
                authorTime  INT,
                custom      INT,
                mapUid      VARCHAR(27) PRIMARY KEY,
                name        TEXT,
                reason      TEXT,
                warriorTime INT,
                worldRecord INT
            );
        ''')

        for uid, map in maps.items():
            cur.execute(f'''
                INSERT INTO WarriorSeasonal (
                    authorTime,
                    custom,
                    mapUid,
                    name,
                    reason,
                    warriorTime,
                    worldRecord
                ) VALUES (
                    "{map['authorTime']}",
                    {f'"{map['custom']}"' if 'custom' in map and map['custom'] is not None else 'NULL'},
                    "{map['mapUid']}",
                    "{map['name']}",
                    {f'"{map['reason']}"' if 'reason' in map and map['reason'] is not None else 'NULL'},
                    "{map['warriorTime']}",
                    "{map['worldRecord']}"
                )
            ''')

    return True


@safelogged(bool)
def schedule_totd_maps(tokens: dict) -> bool:
    time.sleep(WAIT_TIME)
    maps_totd: dict = live.maps_totd(tokens['live'], 99)

    if os.path.isfile(FILE_TOTD_RAW):
        ts: int = stamp()
        with zipfile.ZipFile(f'{DIR_DATA}/history/totd_raw_{ts}.zip', 'w', zipfile.ZIP_LZMA, compresslevel=5) as zip:
            zip.write(FILE_TOTD_RAW, 'totd_raw.json')

    with open(FILE_TOTD_RAW, 'w', newline='\n') as f:
        json.dump(maps_totd, f, indent=4)
        f.write('\n')

    with sql.connect(FILE_DB) as con:
        cur: sql.Cursor = con.cursor()

        cur.execute('BEGIN')
        cur.execute('DROP TABLE IF EXISTS Totd')
        cur.execute(f'''
            CREATE TABLE IF NOT EXISTS Totd (
                author          CHAR(36),
                authorTime      INT,
                bronzeTime      INT,
                campaignId      INT,
                goldTime        INT,
                mapId           CHAR(36),
                mapUid          VARCHAR(27) PRIMARY KEY,
                month           INT,
                monthDay        INT,
                name            TEXT,
                number          INT,
                seasonUid       CHAR(36),
                silverTime      INT,
                submitter       CHAR(36),
                timestampEnd    INT,
                timestampStart  INT,
                timestampUpload INT,
                weekDay         INT,
                year            INT
            );
        ''')

        number: int = 0

        for month in reversed(maps_totd['monthList']):
            for map in month['days']:
                mapUid: str = map['mapUid']
                if len(mapUid) == 0:
                    break

                number += 1
                cur.execute(f'''
                    INSERT INTO Totd (
                        campaignId,
                        mapUid,
                        month,
                        monthDay,
                        number,
                        seasonUid,
                        timestampEnd,
                        timestampStart,
                        weekDay,
                        year
                    ) VALUES (
                        "{map['campaignId']}",
                        "{mapUid}",
                        "{month['month']}",
                        "{map['monthDay']}",
                        "{number}",
                        "{map['seasonUid']}",
                        "{map['endTimestamp']}",
                        "{map['startTimestamp']}",
                        "{map['day']}",
                        "{month['year']}"
                    )
                ''')

    write_db_key_val('next_totd', maps_totd['nextRequestTimestamp'])
    write_db_key_val('warrior_totd', maps_totd['nextRequestTimestamp'] + 60*60*2)
    return True


@safelogged(bool)
def schedule_totd_warrior(tokens: dict) -> bool:
    with sql.connect(FILE_DB) as con:
        con.row_factory = sql.Row
        cur: sql.Cursor = con.cursor()

        cur.execute('BEGIN')
        map: dict = dict(cur.execute('SELECT * FROM Totd ORDER BY number DESC').fetchone())

    log(f'info: getting records for TOTD {map['year']}-{map['month']}-{map['monthDay']}')

    time.sleep(WAIT_TIME)
    req: dict = live.get(
        tokens['live'],
        f'api/token/leaderboard/group/Personal_Best/map/{map['mapUid']}/top'
    )

    map['worldRecord'] = req['tops'][0]['top'][0]['score']
    map['warriorTime'] = get_warrior_time(map['authorTime'], map['worldRecord'], 0.125)

    with sql.connect(FILE_DB) as con:
        cur: sql.Cursor = con.cursor()

        cur.execute('BEGIN')
        cur.execute(f'''
            CREATE TABLE IF NOT EXISTS WarriorTotd (
                authorTime  INT,
                custom      INT,
                mapUid      VARCHAR(27) PRIMARY KEY,
                month       INT,
                monthDay    INT,
                name        TEXT,
                reason      TEXT,
                warriorTime INT,
                worldRecord INT,
                year        INT
            );
        ''')

        cur.execute(f'''
            INSERT INTO WarriorTotd (
                authorTime,
                custom,
                mapUid,
                month,
                monthDay,
                name,
                reason,
                warriorTime,
                worldRecord,
                year
            ) VALUES (
                "{map['authorTime']}",
                {f'"{map['custom']}"' if 'custom' in map and map['custom'] is not None else 'NULL'},
                "{map['mapUid']}",
                "{map['month']}",
                "{map['monthDay']}",
                "{map['name']}",
                {f'"{map['reason']}"' if 'reason' in map and map['reason'] is not None else 'NULL'},
                "{map['warriorTime']}",
                "{map['worldRecord']}",
                "{map['year']}"
            )
        ''')

    return True


@safelogged(bool)
def schedule_weekly_maps(tokens: dict) -> bool:
    time.sleep(WAIT_TIME)
    maps_weekly: dict = live.get(tokens['live'], 'api/campaign/weekly-shorts?length=99')

    if os.path.isfile(FILE_WEEKLY_RAW):
        ts: int = stamp()
        with zipfile.ZipFile(f'{DIR_DATA}/history/weekly_raw_{ts}.zip', 'w', zipfile.ZIP_LZMA, compresslevel=5) as zip:
            zip.write(FILE_WEEKLY_RAW, 'weekly_raw.json')

    with open(FILE_WEEKLY_RAW, 'w', newline='\n') as f:
        json.dump(maps_weekly, f, indent=4)
        f.write('\n')

    with sql.connect(FILE_DB) as con:
        cur: sql.Cursor = con.cursor()

        cur.execute('BEGIN')
        cur.execute('DROP TABLE IF EXISTS Weekly')
        cur.execute(f'''
            CREATE TABLE IF NOT EXISTS Weekly (
                author               CHAR(36),
                authorTime           INT,
                bronzeTime           INT,
                campaignId           INT,
                goldTime             INT,
                mapId                CHAR(36),
                mapIndex             INT,
                mapUid               VARCHAR(27) PRIMARY KEY,
                name                 TEXT,
                number               INT,
                seasonUid            CHAR(36),
                silverTime           INT,
                submitter            CHAR(36),
                timestampEdition     INT,
                timestampEnd         INT,
                timestampRankingSent INT,
                timestampStart       INT,
                timestampUpload      INT,
                week                 INT,
                year                 INT
            );
        ''')

        for campaign in reversed(maps_weekly['campaignList']):
            timestampRankingSent: int | None = campaign['rankingSentTimestamp']

            for map in campaign['playlist']:
                cur.execute(f'''
                    INSERT INTO Weekly (
                        campaignId,
                        mapIndex,
                        mapUid,
                        number,
                        seasonUid,
                        timestampEdition,
                        timestampEnd,
                        timestampRankingSent,
                        timestampStart,
                        week,
                        year
                    ) VALUES (
                        "{campaign['id']}",
                        "{map['position']}",
                        "{map['mapUid']}",
                        "{(campaign['week'] - 1) * 5 + map['position'] + 1}",
                        "{campaign['seasonUid']}",
                        "{campaign['editionTimestamp']}",
                        "{campaign['endTimestamp']}",
                        {f'"{timestampRankingSent}"' if timestampRankingSent is not None else 'NULL'},
                        "{campaign['startTimestamp']}",
                        "{campaign['week']}",
                        "{campaign['year']}"
                    )
                ''')

    write_db_key_val('next_weekly', maps_weekly['nextRequestTimestamp'])
    write_db_key_val('warrior_weekly', maps_weekly['nextRequestTimestamp'] + 0)
    return True


@safelogged(bool)
def schedule_weekly_warriors(tokens: dict) -> bool:
    maps: dict = {}

    with sql.connect(FILE_DB) as con:
        con.row_factory = sql.Row
        cur: sql.Cursor = con.cursor()

        cur.execute('BEGIN')
        for entry in cur.execute('SELECT * FROM Weekly ORDER BY week DESC, mapIndex ASC;').fetchmany(10)[5:]:
        # for entry in cur.execute('SELECT * FROM Weekly ORDER BY number ASC').fetchall():
            map = dict(entry)
            maps[map['mapUid']] = map

    for uid, map in maps.items():
        print(f'getting records for week {map['week']} map {map['name']}')

        time.sleep(WAIT_TIME)
        req: dict = live.get(
            tokens['live'],
            f'api/token/leaderboard/group/Personal_Best/map/{uid}/top'
        )

        maps[uid]['worldRecord'] = req['tops'][0]['top'][0]['score']
        maps[uid]['warriorTime'] = get_warrior_time(map['authorTime'], map['worldRecord'], 0.5)

    with sql.connect(FILE_DB) as con:
        cur: sql.Cursor = con.cursor()

        cur.execute('BEGIN')
        cur.execute(f'''
            CREATE TABLE IF NOT EXISTS WarriorWeekly (
                authorTime  INT,
                custom      INT,
                mapUid      VARCHAR(27) PRIMARY KEY,
                name        TEXT,
                number      INT,
                reason      TEXT,
                warriorTime INT,
                worldRecord INT
            );
        ''')

        for uid, map in maps.items():
            cur.execute(f'''
                INSERT INTO WarriorWeekly (
                    authorTime,
                    custom,
                    mapUid,
                    name,
                    number,
                    reason,
                    warriorTime,
                    worldRecord
                ) VALUES (
                    "{map['authorTime']}",
                    "{map['campaignId']}",
                    {f'"{map['custom']}"' if 'custom' in map and map['custom'] is not None else 'NULL'},
                    "{map['mapUid']}",
                    "{map['name']}",
                    "{map['number']}",
                    {f'"{map['reason']}"' if 'reason' in map and map['reason'] is not None else 'NULL'},
                    "{map['warriorTime']}",
                    "{map['worldRecord']}"
                )
            ''')

    return True


@safelogged(bool, do_log=False)
def schedule(tokens: dict, key: str, ts: int, schedule_func, table: str, webhook_func) -> bool:
    val: str = read_db_key_val(key)
    if ts <= (int(val) if len(val) else 0):
        return False

    tries = 4  # total = this + 1
    while not (success := schedule_func(tokens)) and tries:
        log(f'error: {schedule_func.__name__}(), waiting... (trying {tries} more time{'s' if tries != 1 else ''})')
        tries -= 1
        time.sleep(5)
    if not success:
        write_db_key_val(key, ts + 60*3)
        raise RuntimeError(f'error: {schedule_func.__name__}(), trying again in 3 minutes')

    tries = 4
    while not (success := get_map_infos(tokens, table)) and tries:
        log(f'error: get_map_infos({table}), waiting... (trying {tries} more time{'s' if tries != 1 else ''})')
        tries -= 1
        time.sleep(5)
    if not success:
        write_db_key_val(key, ts + 60*3)
        raise RuntimeError(f'error: get_map_infos({table}), trying again in 3 minutes')

    if not webhook_func(tokens):
        raise RuntimeError(f'error: {webhook_func.__name__}()')

    return True


@safelogged(bool, do_log=False)
def schedule_warriors(tokens: dict, key: str, ts: int, warrior_func, webhook_func) -> bool:
    val: str = read_db_key_val(key)
    if ts <= (int(val) if len(val) else 0):
        return False

    tries = 4  # total = this + 1
    while not (success := warrior_func(tokens)) and tries:
        log(f'error: {warrior_func.__name__}(), waiting... (trying {tries} more time{'s' if tries != 1 else ''})')
        tries -= 1
        time.sleep(5)
    if not success:
        write_db_key_val(key, ts + 60*3)
        raise RuntimeError(f'error: {warrior_func.__name__}(), trying again in 3 minutes')

    if not webhook_func(tokens):
        raise RuntimeError(f'error: {webhook_func.__name__}()')

    return True

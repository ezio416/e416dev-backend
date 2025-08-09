# c 2025-01-27
# m 2025-08-09

import json
import time
import typing
import zipfile

from nadeo_api import live

import api
from constants import *
import errors
import files
import utils


@errors.safelogged(bool)
def seasonal(tokens: dict) -> bool:
    next_seasonal: int = files.read_timestamp('next_seasonal')
    if 0 < next_seasonal < MAX_TIMESTAMP:
        files.write_timestamp('next_warrior_seasonal', next_seasonal + utils.weeks_to_seconds(2))

    maps_seasonal: dict = live.get_maps_seasonal(tokens['live'], 144)

    if os.path.isfile(FILE_SEASONAL_RAW):
        with zipfile.ZipFile(
            f'{DIR_DATA}/history/seasonal_raw_{utils.stamp()}.zip',
            'w',
            zipfile.ZIP_LZMA,
            compresslevel=5
        ) as zip:
            zip.write(FILE_SEASONAL_RAW, 'seasonal_raw.json')

    with open(FILE_SEASONAL_RAW, 'w', newline='\n') as f:
        json.dump(maps_seasonal, f, indent=4)
        f.write('\n')

    TABLE: str = 'Seasonal'

    with files.Cursor(FILE_DB) as db:
        db.execute(f'DROP TABLE IF EXISTS {TABLE}')
        db.execute(f'''
            CREATE TABLE IF NOT EXISTS {TABLE} (
                author               CHAR(36),
                authorTime           INT,
                bronzeTime           INT,
                campaignId           INT,
                campaignIndex        INT,
                goldTime             INT,
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
                timestampRankingSent INT,
                timestampStart       INT,
                timestampUpload      INT
            );
        ''')

        for i, campaign in enumerate(reversed(maps_seasonal['campaignList'])):
            sent: int | None = campaign['rankingSentTimestamp']

            for map in campaign['playlist']:
                db.execute(f'''
                    INSERT INTO {TABLE} (
                        campaignId,
                        campaignIndex,
                        mapIndex,
                        mapUid,
                        number,
                        seasonUid,
                        timestampEdition,
                        timestampEnd,
                        timestampRankingSent,
                        timestampStart
                    ) VALUES (
                        "{campaign['id']}",
                        "{i}",
                        "{map['position']}",
                        "{map['mapUid']}",
                        "{i * 25 + map['position'] + 1}",
                        "{campaign['seasonUid']}",
                        "{campaign['editionTimestamp']}",
                        "{campaign['endTimestamp']}",
                        {f'"{sent}"' if sent else 0},
                        "{campaign['startTimestamp']}"
                    );
                ''')

    # different order below from totd/weekly since the next totd/weekly is almost always exactly a day/week away
    # better to handle it automatically and only fix manually if it happens to fail around DST

    if maps_seasonal['nextRequestTimestamp'] > 0:
        files.write_timestamp('next_seasonal', maps_seasonal['nextRequestTimestamp'])
    else:
        files.write_timestamp('next_seasonal', MAX_TIMESTAMP)
        errors.notify(f'seasonal nextRequestTimestamp invalid: {maps_seasonal['nextRequestTimestamp']}')

    return api.get_map_infos(tokens, TABLE)


@errors.safelogged(bool)
def seasonal_warriors(tokens: dict) -> bool:
    maps: dict = {}

    with files.Cursor(FILE_DB) as db:
        for entry in db.execute('SELECT * FROM Seasonal ORDER BY campaignIndex DESC').fetchmany(25):
            map: dict = dict(entry)
            maps[map['mapUid']] = map

    for uid, map in maps.items():
        utils.log(f'info: getting records for "{map['name']}"')

        req: dict = live.get_map_leaderboard(tokens['live'], uid, length=10)

        maps[uid]['worldRecord'] = files.handle_tops(req['tops'][0]['top'], map['mapUid'], map['name'])
        maps[uid]['warriorTime'] = utils.calc_warrior_time(map['authorTime'], map['worldRecord'])

    with files.Cursor(FILE_DB) as db:
        db.execute(f'''
            CREATE TABLE IF NOT EXISTS WarriorSeasonal (
                authorTime  INT,
                campaignId  INT,
                mapUid      VARCHAR(27) PRIMARY KEY,
                name        TEXT,
                reason      TEXT,
                warriorTime INT,
                worldRecord INT,
                mapId       CHAR(36),
                goldTime    INT
            );
        ''')

        for uid, map in maps.items():
            db.execute(f'''
                INSERT INTO WarriorSeasonal (
                    authorTime,
                    campaignId,
                    mapUid,
                    name,
                    reason,
                    warriorTime,
                    worldRecord,
                    mapId,
                    goldTime
                ) VALUES (
                    "{map['authorTime']}",
                    "{map['campaignId']}",
                    "{map['mapUid']}",
                    "{map['name']}",
                    {f'"{map['reason']}"' if 'reason' in map and map['reason'] is not None else 'NULL'},
                    "{map['warriorTime']}",
                    "{map['worldRecord']}",
                    "{map['mapId']}",
                    "{map['goldTime']}"
                )
            ''')

    return True


@errors.safelogged(bool)
def totd(tokens: dict) -> bool:
    next_totd: int = files.read_timestamp('next_totd')
    if 0 < next_totd < MAX_TIMESTAMP:
        files.write_timestamp('next_warrior_totd', next_totd + utils.hours_to_seconds(2))

    maps_totd: dict = live.get_maps_totd(tokens['live'], 144)

    if os.path.isfile(FILE_TOTD_RAW):
        with zipfile.ZipFile(
            f'{DIR_DATA}/history/totd_raw_{utils.stamp()}.zip',
            'w',
            zipfile.ZIP_LZMA,
            compresslevel=5
        ) as zip:
            zip.write(FILE_TOTD_RAW, 'totd_raw.json')

    with open(FILE_TOTD_RAW, 'w', newline='\n') as f:
        json.dump(maps_totd, f, indent=4)
        f.write('\n')

    TABLE: str = 'Totd'

    with files.Cursor(FILE_DB) as db:
        db.execute(f'DROP TABLE IF EXISTS {TABLE}')
        db.execute(f'''
            CREATE TABLE IF NOT EXISTS {TABLE} (
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
                if not len(mapUid):
                    break

                number += 1
                db.execute(f'''
                    INSERT INTO {TABLE} (
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
                    );
                ''')

    if not api.get_map_infos(tokens, TABLE):
        return False

    if maps_totd['nextRequestTimestamp'] > 0:
        files.write_timestamp('next_totd', maps_totd['nextRequestTimestamp'])
    else:
        files.write_timestamp('next_totd', next_totd + utils.days_to_seconds(1))
        errors.notify(f'totd nextRequestTimestamp invalid: {maps_totd['nextRequestTimestamp']}')

    return True


@errors.safelogged(bool)
def totd_warrior(tokens: dict) -> bool:
    with files.Cursor(FILE_DB) as db:
        map: dict = dict(db.execute('SELECT * FROM Totd ORDER BY number DESC').fetchone())

    utils.log(f'info: getting records for TOTD {map['year']}-{str(map['month']).zfill(2)}-{str(map['monthDay']).zfill(2)}')

    req: dict = live.get_map_leaderboard(tokens['live'], map['mapUid'], length=10)

    map['worldRecord'] = files.handle_tops(req['tops'][0]['top'], map['mapUid'], map['name'])
    map['warriorTime'] = utils.calc_warrior_time(map['authorTime'], map['worldRecord'], 0.125)

    with files.Cursor(FILE_DB) as db:
        db.execute(f'''
            CREATE TABLE IF NOT EXISTS WarriorTotd (
                authorTime  INT,
                date        CHAR(10),
                mapUid      VARCHAR(27) PRIMARY KEY,
                name        TEXT,
                reason      TEXT,
                warriorTime INT,
                worldRecord INT,
                mapId       CHAR(36),
                goldTime    INT
            );
        ''')

        db.execute(f'''
            INSERT INTO WarriorTotd (
                authorTime,
                date,
                mapUid,
                name,
                reason,
                warriorTime,
                worldRecord,
                mapId,
                goldTime
            ) VALUES (
                "{map['authorTime']}",
                "{map['year']}-{str(map['month']).zfill(2)}-{str(map['monthDay']).zfill(2)}",
                "{map['mapUid']}",
                "{map['name']}",
                {f'"{map['reason']}"' if 'reason' in map and map['reason'] is not None else 'NULL'},
                "{map['warriorTime']}",
                "{map['worldRecord']}",
                "{map['mapId']}",
                "{map['goldTime']}"
            )
        ''')

    return True


@errors.safelogged(bool)
def weekly(tokens: dict) -> bool:
    next_weekly: int = files.read_timestamp('next_weekly')
    if 0 < next_weekly < MAX_TIMESTAMP:
        files.write_timestamp('next_warrior_weekly', next_weekly + utils.weeks_to_seconds(1))

    maps_weekly: dict = live.get_maps_weekly(tokens['live'], 144)

    if os.path.isfile(FILE_WEEKLY_RAW):
        with zipfile.ZipFile(
            f'{DIR_DATA}/history/weekly_raw_{utils.stamp()}.zip',
            'w',
            zipfile.ZIP_LZMA,
            compresslevel=5
        ) as zip:
            zip.write(FILE_WEEKLY_RAW, 'weekly_raw.json')

    with open(FILE_WEEKLY_RAW, 'w', newline='\n') as f:
        json.dump(maps_weekly, f, indent=4)
        f.write('\n')

    TABLE: str = 'Weekly'

    with files.Cursor(FILE_DB) as db:
        db.execute(f'DROP TABLE IF EXISTS {TABLE}')
        db.execute(f'''
            CREATE TABLE IF NOT EXISTS {TABLE} (
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
            sent: int | None = campaign['rankingSentTimestamp']

            for map in campaign['playlist']:
                db.execute(f'''
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
                        {f'"{sent}"' if sent else 0},
                        "{campaign['startTimestamp']}",
                        "{campaign['week']}",
                        "{campaign['year']}"
                    );
                ''')

    if not api.get_map_infos(tokens, TABLE):
        return False

    if maps_weekly['nextRequestTimestamp'] > 0:
        files.write_timestamp('next_weekly', maps_weekly['nextRequestTimestamp'])
    else:
        files.write_timestamp('next_weekly', next_weekly + utils.weeks_to_seconds(1))
        errors.notify(f'weekly nextRequestTimestamp invalid: {maps_weekly['nextRequestTimestamp']}')

    return True


@errors.safelogged(bool)
def weekly_warriors(tokens: dict) -> bool:
    maps: dict = {}

    with files.Cursor(FILE_DB) as db:
        for entry in db.execute('SELECT * FROM Weekly ORDER BY week DESC, mapIndex ASC;').fetchmany(10)[5:]:
            map: dict = dict(entry)
            maps[map['mapUid']] = map

    for uid, map in maps.items():
        utils.log(f'info: getting records for week {map['week']} map "{map['name']}"')

        req: dict = live.get_map_leaderboard(tokens['live'], uid, length=10)

        maps[uid]['worldRecord'] = files.handle_tops(req['tops'][0]['top'], map['mapUid'], map['name'])
        maps[uid]['warriorTime'] = utils.calc_warrior_time(map['authorTime'], map['worldRecord'], 0.5)

    with files.Cursor(FILE_DB) as db:
        db.execute(f'''
            CREATE TABLE IF NOT EXISTS WarriorWeekly (
                authorTime  INT,
                mapUid      VARCHAR(27) PRIMARY KEY,
                name        TEXT,
                number      INT,
                reason      TEXT,
                warriorTime INT,
                worldRecord INT,
                mapId       CHAR(36),
                goldTime    INT,
                campaignId  INT,
                week        INT
            );
        ''')

        for uid, map in maps.items():
            db.execute(f'''
                INSERT INTO WarriorWeekly (
                    authorTime,
                    mapUid,
                    name,
                    number,
                    reason,
                    warriorTime,
                    worldRecord,
                    mapId,
                    goldTime,
                    campaignId,
                    week
                ) VALUES (
                    "{map['authorTime']}",
                    "{map['mapUid']}",
                    "{map['name']}",
                    "{map['number']}",
                    {f'"{map['reason']}"' if 'reason' in map and map['reason'] is not None else 'NULL'},
                    "{map['warriorTime']}",
                    "{map['worldRecord']}",
                    "{map['mapId']}",
                    "{map['goldTime']}",
                    "{map['campaignId']}",
                    "{map['week']}"
                )
            ''')

    return True


@errors.safelogged(bool, log=False)
def schedule(tokens: dict, table: str, schedule_func: typing.Callable[[dict], bool], webhook_func: typing.Callable[[dict], None]) -> bool:
    next_key: str = f'next_{table}'
    next: int = files.read_timestamp(next_key)
    retry_key: str = f'retry_{table}'
    retry: int = files.read_timestamp(retry_key)

    now: int = utils.stamp()
    if now < next and now < retry:
        return False

    if schedule_func(tokens):
        utils.log(f'info: {table} schedule success')
        files.write_timestamp(retry_key, MAX_TIMESTAMP)
        webhook_func(tokens)
        return True
    else:
        utils.log(f'warn: {table} schedule FAILURE')
        files.write_timestamp(next_key, MAX_TIMESTAMP)
        files.write_timestamp(retry_key, now + utils.minutes_to_seconds(1))
        return False


@errors.safelogged(bool, log=False)
def schedule_warriors(tokens: dict, key: str, ts: int, warrior_func, webhook_func) -> bool:
    val: str = files.read_db_key_val(key)
    if ts <= (int(val) if len(val) else 0):
        return False

    tries = 4  # total = this + 1
    while not (success := warrior_func(tokens)) and tries:
        utils.log(f'error: {warrior_func.__name__}(), waiting... (trying {tries} more time{'s' if tries != 1 else ''})')
        tries -= 1
        time.sleep(5)
    if not success:
        files.write_db_key_val(key, ts + utils.minutes_to_seconds(3))
        raise RuntimeError(f'error: {warrior_func.__name__}(), trying again in 3 minutes')

    if not webhook_func():
        raise RuntimeError(f'error: {webhook_func.__name__}()')

    files.write_db_key_val(f'last_{key}', val)

    return True

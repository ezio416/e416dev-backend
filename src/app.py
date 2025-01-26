# c 2024-12-26
# m 2024-01-26

from base64 import b64encode
from datetime import datetime as dt
import hashlib
import json
import os
import re
import sqlite3 as sql
import time
import traceback
import zipfile

from discord_webhook import DiscordEmbed, DiscordWebhook
from nadeo_api import auth, core, live, oauth
from pytz import timezone as tz
from requests import ConnectionError, get, put, Response


CAMPAIGN_SERIES: tuple[str] = 'FFFFFF', '66FF66', '6666FF', 'FF4444', '666666'
PAR_DIR:         str        = f'{os.path.dirname(__file__).replace('\\', '/')}/..'
DATA_DIR:        str        = f'{PAR_DIR}/data'
WAIT_TIME:       float      = 0.5

accounts:          dict = {}
tokens:            dict = {}
file_db:           str  = f'{DATA_DIR}/tm.db'
file_log:          str  = f'{DATA_DIR}/tm.log'
file_royal:        str  = f'{DATA_DIR}/royal.json'
file_royal_raw:    str  = f'{DATA_DIR}/royal_raw.json'
file_seasonal:     str  = f'{DATA_DIR}/seasonal.json'
file_seasonal_raw: str  = f'{DATA_DIR}/seasonal_raw.json'
file_totd:         str  = f'{DATA_DIR}/totd.json'
file_totd_raw:     str  = f'{DATA_DIR}/totd_raw.json'
file_warrior:      str  = f'{DATA_DIR}/warrior.json'
file_weekly:       str  = f'{DATA_DIR}/weekly.json'
file_weekly_raw:   str  = f'{DATA_DIR}/weekly_raw.json'
file_zone:         str  = f'{DATA_DIR}/zone.json'
file_zone_raw:     str  = f'{DATA_DIR}/zone_raw.json'


def exception_causing_code(e: BaseException) -> traceback.FrameSummary:
    return traceback.TracebackException.from_exception(e).stack[-1]


def error(e: Exception, silent: bool = False) -> None:
    code: traceback.FrameSummary = exception_causing_code(e)

    loc: str = f'line {code.lineno}, column {code.colno} in {code.name}()'

    log(f'error: {loc}: {type(e).__name__}: {e} id<{id(e)}>')

    if not silent:
        DiscordWebhook(
            os.environ['dcwh-site-backend-errors'],
            content=f'<@&1205257336252534814> id<`{id(e)}`>\n`{now(False)}`\n`{type(e).__name__}: {e}`\n`{loc}`\n\n`{code.line}`'
        ).execute()


def safelogged(return_type: type = None, silent: bool = False, do_log: bool = True):
    def inner(func):
        def wrapper(*args, **kwargs):
            if return_type is not None and return_type.__class__ is not type:
                print(f'{return_type.__name__} is not a type')
                return None

            if do_log and not silent:
                log(f'info: called {func.__name__}({', '.join([f"{type(s).__name__}('{s}')" for s in args])})')

            try:
                return func(*args, **kwargs)
            except Exception as e:
                error(e, silent)
                return return_type() if return_type is not None else None

        wrapper.__name__ = func.__name__  # feels like a bad idea but it works
        return wrapper
    return inner


def format_race_time(input_ms: int) -> str:
    min: int = int(input_ms / 60000)
    sec: int = int((input_ms - (min * 60000)) / 1000)
    ms:  int = input_ms % 1000

    return f'{min}:{str(sec).zfill(2)}.{str(ms).zfill(3)}'


@safelogged(str)
def get_account_name(account_id: str) -> str:
    global accounts

    ts: int = stamp()

    if account_id in accounts and ts < accounts[account_id]['ts']:
        return accounts[account_id]['name']

    time.sleep(WAIT_TIME)
    req = oauth.account_names_from_ids(tokens['oauth'], account_id)

    name: str = req[account_id]
    accounts[account_id] = {}
    accounts[account_id]['name'] = name
    accounts[account_id]['ts'] = ts + 60*60  # keep valid for 1 hour

    return name


@safelogged(bool)
def get_map_infos(table: str) -> bool:
    maps_by_uid: dict = {}
    uid_groups:  list = []
    uid_limit:   int  = 270
    uids:        list = []

    with sql.connect(file_db) as con:
        con.row_factory = sql.Row
        cur: sql.Cursor = con.cursor()

        cur.execute('BEGIN')
        for entry in cur.execute(f'SELECT * FROM {table}').fetchall():
            map: dict = dict(entry)
            maps_by_uid[map['mapUid']] = map

    uids = list(maps_by_uid)
    while True:
        if len(uids) > uid_limit:
            uid_groups.append(','.join(uids[:uid_limit]))
            uids = uids[uid_limit:]
        else:
            uid_groups.append(','.join(uids))
            break

    for i, group in enumerate(uid_groups):
        log(f'info: get_map_info {i + 1}/{len(uid_groups)} groups...')

        time.sleep(WAIT_TIME)
        info: dict = core.get(tokens['core'], 'maps', {'mapUidList': group})

        for entry in info:
            map: dict = maps_by_uid[entry['mapUid']]

            map['author']          = entry['author']
            map['authorTime']      = entry['authorScore']
            map['bronzeTime']      = entry['bronzeScore']
            map['goldTime']        = entry['goldScore']
            map['mapId']           = entry['mapId']
            map['name']            = entry['name']
            map['silverTime']      = entry['silverScore']
            map['submitter']       = entry['submitter']
            map['timestampUpload'] = int(dt.fromisoformat(entry['timestamp']).timestamp())

    with sql.connect(file_db) as con:
        cur: sql.Cursor = con.cursor()

        cur.execute('BEGIN')
        for uid, map in maps_by_uid.items():
            cur.execute(f'''
                UPDATE {table}
                SET author          = "{map['author']}",
                    authorTime      = "{map['authorTime']}",
                    bronzeTime      = "{map['bronzeTime']}",
                    goldTime        = "{map['goldTime']}",
                    mapId           = "{map['mapId']}",
                    name            = "{map['name']}",
                    silverTime      = "{map['silverTime']}",
                    submitter       = "{map['submitter']}",
                    timestampUpload = "{map['timestampUpload']}"
                WHERE mapUid = "{uid}"
                ;
            ''')

    return True


def get_tokens() -> dict:
    log('info: getting core token')
    token_core: auth.Token = auth.get_token(
        auth.audience_core,
        os.environ['TM_E416DEV_SERVER_USERNAME'],
        os.environ['TM_E416DEV_SERVER_PASSWORD'],
        os.environ['TM_E416DEV_AGENT'],
        True
    )

    log('info: getting live token')
    token_live: auth.Token = auth.get_token(
        auth.audience_live,
        os.environ['TM_E416DEV_SERVER_USERNAME'],
        os.environ['TM_E416DEV_SERVER_PASSWORD'],
        os.environ['TM_E416DEV_AGENT'],
        True
    )

    log('info: getting oauth token')
    token_oauth: auth.Token = auth.get_token(
        auth.audience_oauth,
        os.environ['TM_OAUTH_IDENTIFIER'],
        os.environ['TM_OAUTH_SECRET']
    )

    return {
        'core': token_core,
        'live': token_live,
        'oauth': token_oauth
    }


def get_warrior_time(author_time: int, world_record: int, factor: float | None = 0.25) -> int:
    '''
    - `factor` is offset from AT
        - between `0.0` and `1.0`
        - examples, given AT is `10.000` and WR is `8.000`:
            - `0.000` - AT (`10.000`)
            - `0.125` - 1/8 of the way between AT and WR (`9.750`) (default for TOTD)
            - `0.250` - 1/4 of the way between AT and WR (`9.500`) (default, default for seasonal)
            - `0.500` - 1/2 of the way between AT and WR (`9.000`) (default for weekly)
            - `0.750` - 3/4 of the way between AT and WR (`8.500`)
            - `1.000` - WR (`8.000`)
    '''

    return author_time - max(
        int((author_time - world_record) * (factor if factor is not None else 0.25)),
        1
    )


def log(msg: str, print_term: bool = True) -> None:
    text: str = f'{now()} {msg}'

    if print_term:
        print(text)

    with open(file_log, 'a', newline='\n') as f:
        f.write(f'{text}\n')


def now(brackets: bool = True) -> str:
    utc    = dt.now(tz('UTC')).strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
    denver = f'Denver {dt.now(tz('America/Denver')).strftime('%H:%M')}'
    paris  = f'Paris {dt.now(tz('Europe/Paris')).strftime('%H:%M')}'
    return f'{'[' if brackets else ''}{utc} ({denver}, {paris}){']' if brackets else ''}'


@safelogged(str, True)
def read_db_key_val(key: str) -> str:
    with sql.connect(file_db) as con:
        cur: sql.Cursor = con.cursor()
        return cur.execute(f'SELECT * FROM KeyVals WHERE key = "{key}"').fetchone()[1]


@safelogged(list)
def read_table(table: str) -> list[dict]:
    with sql.connect(file_db) as con:
        con.row_factory = sql.Row
        cur: sql.Cursor = con.cursor()

        return [dict(item) for item in cur.execute(f'SELECT * FROM {table}').fetchall()]


@safelogged(bool)
def schedule_royal_maps() -> bool:
    time.sleep(WAIT_TIME)
    maps_royal: dict = live.maps_royal(tokens['live'], 99)

    if os.path.isfile(file_royal_raw):
        ts: int = stamp()
        with zipfile.ZipFile(f'{PAR_DIR}/data/history/royal_raw_{ts}.zip', 'w', zipfile.ZIP_LZMA, compresslevel=5) as zip:
            zip.write(file_royal_raw, 'royal_raw.json')

    with open(file_royal_raw, 'w', newline='\n') as f:
        json.dump(maps_royal, f, indent=4)
        f.write('\n')

    with sql.connect(file_db) as con:
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
def schedule_seasonal_maps() -> bool:
    time.sleep(WAIT_TIME)
    maps_seasonal: dict = live.maps_campaign(tokens['live'], 99)

    if os.path.isfile(file_seasonal_raw):
        ts: int = stamp()
        with zipfile.ZipFile(f'{PAR_DIR}/data/history/seasonal_raw_{ts}.zip', 'w', zipfile.ZIP_LZMA, compresslevel=5) as zip:
            zip.write(file_seasonal_raw, 'seasonal_raw.json')

    with open(file_seasonal_raw, 'w', newline='\n') as f:
        json.dump(maps_seasonal, f, indent=4)
        f.write('\n')

    with sql.connect(file_db) as con:
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
def schedule_seasonal_warriors() -> bool:
    maps: dict = {}

    with sql.connect(file_db) as con:
        con.row_factory = sql.Row
        cur: sql.Cursor = con.cursor()

        cur.execute('BEGIN')
        for entry in cur.execute('SELECT * FROM Seasonal ORDER BY campaignIndex DESC').fetchmany(25):
            map = dict(entry)
            maps[map['mapUid']] = map

    for uid, map in maps.items():
        print(f'getting records for {map['name']}')

        time.sleep(WAIT_TIME)
        req: dict = live.get(
            tokens['live'],
            f'api/token/leaderboard/group/Personal_Best/map/{uid}/top'
        )

        maps[uid]['worldRecord'] = req['tops'][0]['top'][0]['score']
        maps[uid]['warriorTime'] = get_warrior_time(map['authorTime'], map['worldRecord'])

    with sql.connect(file_db) as con:
        cur: sql.Cursor = con.cursor()

        cur.execute('BEGIN')
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

        for uid, map in maps.items():
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
                    "{map['mapUid']}",
                    "{map['name']}",
                    {f'"{map['reason']}"' if 'reason' in map and map['reason'] is not None else 'NULL'},
                    "{map['warriorTime']}",
                    "{map['worldRecord']}"
                )
            ''')

    return True


@safelogged(bool)
def schedule_totd_maps() -> bool:
    time.sleep(WAIT_TIME)
    maps_totd: dict = live.maps_totd(tokens['live'], 99)

    if os.path.isfile(file_totd_raw):
        ts: int = stamp()
        with zipfile.ZipFile(f'{PAR_DIR}/data/history/totd_raw_{ts}.zip', 'w', zipfile.ZIP_LZMA, compresslevel=5) as zip:
            zip.write(file_totd_raw, 'totd_raw.json')

    with open(file_totd_raw, 'w', newline='\n') as f:
        json.dump(maps_totd, f, indent=4)
        f.write('\n')

    with sql.connect(file_db) as con:
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
def schedule_totd_warrior() -> bool:
    return True


@safelogged(bool)
def schedule_weekly_maps() -> bool:
    time.sleep(WAIT_TIME)
    maps_weekly: dict = live.get(tokens['live'], 'api/campaign/weekly-shorts?length=99')

    if os.path.isfile(file_weekly_raw):
        ts: int = stamp()
        with zipfile.ZipFile(f'{PAR_DIR}/data/history/weekly_raw_{ts}.zip', 'w', zipfile.ZIP_LZMA, compresslevel=5) as zip:
            zip.write(file_weekly_raw, 'weekly_raw.json')

    with open(file_weekly_raw, 'w', newline='\n') as f:
        json.dump(maps_weekly, f, indent=4)
        f.write('\n')

    with sql.connect(file_db) as con:
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
    return True


@safelogged(bool)
def schedule_weekly_warriors() -> bool:
    maps: dict = {}

    with sql.connect(file_db) as con:
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

    with sql.connect(file_db) as con:
        cur: sql.Cursor = con.cursor()

        cur.execute('BEGIN')
        cur.execute(f'''
            CREATE TABLE IF NOT EXISTS WarriorWeekly (
                authorTime  INT,
                campaignId  INT,
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
                    campaignId,
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


def stamp() -> int:
    return int(time.time())


def strip_format_codes(raw: str) -> str:
    return re.sub(r'\$([0-9a-fA-F]{1,3}|[iIoOnNmMwWsSzZtTgG<>]|[lLhHpP](\[[^\]]+\])?)', '', raw).strip()


@safelogged()
def tables_to_json() -> None:
    for table_name, output_file in (
        ('Royal',    file_royal),
        ('Seasonal', file_seasonal),
        ('Totd',     file_totd),
        # ('Warrior',  file_warrior),
        ('Weekly',   file_weekly),
    ):
        with open(output_file, 'w', newline='\n') as f:
            json.dump({item['mapUid']: item for item in read_table(table_name)}, f, indent=4)
            f.write('\n')


@safelogged()
def to_github() -> None:
    base_url: str = 'https://api.github.com/repos/ezio416/tm-json/contents'
    headers: dict = {
        'Accept': 'application/vnd.github+json',
        'Authorization': f'Bearer {os.environ['GITHUB_TM_JSON_TOKEN']}',
        'X_GitHub-Api-Version': '2022-11-28'
    }

    time.sleep(WAIT_TIME)
    log('info: getting info from Github')
    req:      Response   = get(base_url, headers=headers)
    contents: list[dict] = req.json()

    for file in (
        file_royal,
        file_seasonal,
        file_totd,
        file_warrior,
        file_weekly
    ):
        if not os.path.isfile(file):
            print(f'to_github(): not found: {file}')
            continue

        with open(file) as f:
            file_data: str = f.read()

        basename: str = os.path.basename(file)
        sha:      str = hashlib.sha1(f'blob {len(file_data)}\x00{file_data}'.encode()).hexdigest()

        for item in contents:
            if basename != item['name'] or sha == item['sha']:
                continue

            time.sleep(WAIT_TIME)
            log(f'info: sending to Github: {basename}')
            sent: Response = put(
                f'{base_url}/{basename}',
                headers=headers,
                json={
                    'content': b64encode(file_data.encode()).decode(),
                    'message': now(False),
                    'sha': item['sha']
                }
            )

            if sent.status_code == 200:
                log(f'info: sent {basename}')
            else:
                raise ConnectionError(f'error: bad req ({sent.status_code}) for "{basename}": {sent.text}')


@safelogged(bool)
def webhook_royal_map() -> bool:
    raise Exception('oops')
    return True


def _webhook_seasonal(map: dict) -> None:
    webhook: DiscordWebhook = DiscordWebhook(os.environ['dcwh-tm-seasonal-updates'])

    embed: DiscordEmbed = DiscordEmbed(
        strip_format_codes(map['name']),
        f'[Trackmania.io](https://trackmania.io/#/leaderboard/{map['mapUid']})',
        color=CAMPAIGN_SERIES[int(map['mapIndex'] / 5)]
    )

    embed.add_embed_field(
        'Medals',
        f'''
<:MedalAuthor:736600847219294281> {format_race_time(map['authorTime'])}
<:MedalGold:736600847588261988> {format_race_time(map['goldTime'])}
<:MedalSilver:736600847454175363> {format_race_time(map['silverTime'])}
<:MedalBronze:736600847630336060> {format_race_time(map['bronzeTime'])}
''',
        False
    )

    embed.set_thumbnail(f'https://core.trackmania.nadeo.live/maps/{map['mapId']}/thumbnail.jpg')

    webhook.add_embed(embed)
    webhook.execute()


@safelogged(bool)
def webhook_seasonal_maps() -> bool:
    maps: list[dict] = []

    with sql.connect(file_db) as con:
        con.row_factory = sql.Row
        cur: sql.Cursor = con.cursor()

        cur.execute('BEGIN')
        for entry in cur.execute('SELECT * FROM Seasonal ORDER BY campaignIndex DESC').fetchmany(25):
            maps.append(dict(entry))

    for map in maps:
        time.sleep(1)
        _webhook_seasonal(map)

    return True


@safelogged(bool)
def webhook_totd_map() -> bool:
    return True


def _webhook_weekly(map: dict) -> None:
    webhook: DiscordWebhook = DiscordWebhook(os.environ['dcwh-tm-weekly-updates'])

    embed: DiscordEmbed = DiscordEmbed(
        f'Week {map['week']}, Map {map['number']}',
        f'[{strip_format_codes(map['name'])}](https://trackmania.io/#/leaderboard/{map['mapUid']\
            })\nby [{get_account_name(map['author'])}](https://trackmania.io/#/player/{map['author']})',
        color=CAMPAIGN_SERIES[map['mapIndex']]
    )

    embed.add_embed_field(
        'Medals',
        f'''
<:MedalAuthor:736600847219294281> {format_race_time(map['authorTime'])}
<:MedalGold:736600847588261988> {format_race_time(map['goldTime'])}
<:MedalSilver:736600847454175363> {format_race_time(map['silverTime'])}
<:MedalBronze:736600847630336060> {format_race_time(map['bronzeTime'])}
''',
        False
    )

    embed.set_thumbnail(f'https://core.trackmania.nadeo.live/maps/{map['mapId']}/thumbnail.jpg')

    webhook.add_embed(embed)
    webhook.execute()


@safelogged(bool)
def webhook_weekly_maps() -> bool:
    maps: list[dict] = []

    with sql.connect(file_db) as con:
        con.row_factory = sql.Row
        cur: sql.Cursor = con.cursor()

        cur.execute('BEGIN')
        for entry in cur.execute('SELECT * FROM Weekly ORDER BY week DESC, mapIndex ASC;').fetchmany(5):
            maps.append(dict(entry))

    for map in maps:
        time.sleep(1)
        _webhook_weekly(map)

    return True


@safelogged(bool)
def webhook_weekly_warriors() -> bool:
    return True


@safelogged()
def write_db_key_val(key: str, val) -> None:
    with sql.connect(file_db) as con:
        cur: sql.Cursor = con.cursor()
        cur.execute('BEGIN')
        cur.execute('CREATE TABLE IF NOT EXISTS KeyVals (key TEXT PRIMARY KEY, val TEXT);')
        cur.execute(f'REPLACE INTO KeyVals (key, val) VALUES ("{key}", "{val}")')
        cur.execute(f'REPLACE INTO KeyVals (key, val) VALUES ("last_updated", "{stamp()}")')


@safelogged(bool, do_log=False)
def schedule(key: str, ts: int, schedule_func, table: str, webhook_func, warrior_func = None) -> bool:
    val: str = read_db_key_val(key)
    if ts <= (int(val) if len(val) else 0):
        return False

    tries = 4  # total = this + 1
    while not (success := schedule_func()) and tries:
        log(f'error: {schedule_func.__name__}(), waiting... (trying {tries} more time{'s' if tries != 1 else ''})')
        tries -= 1
        time.sleep(5)
    if not success:
        write_db_key_val(key, ts + 60*3)
        raise RuntimeError(f'error: {schedule_func.__name__}(), trying again in 3 minutes')

    tries = 4
    while not (success := get_map_infos(table)) and tries:
        log(f'error: get_map_infos({table}), waiting... (trying {tries} more time{'s' if tries != 1 else ''})')
        tries -= 1
        time.sleep(5)
    if not success:
        write_db_key_val(key, ts + 60*3)
        raise RuntimeError(f'error: get_map_infos({table}), trying again in 3 minutes')

    if not webhook_func():
        raise RuntimeError(f'error: {webhook_func.__name__}()')

    # if not warrior_func:
    return True
    tries = 9
    while not (success := warrior_func()) and tries:
        log(f'error: {warrior_func.__name__}(), waiting... (trying {tries} more time{'s' if tries != 1 else ''})')
        tries -= 1
        time.sleep(5)
    if not success:
        raise RuntimeError(f'error: {warrior_func.__name__}()')

    return True


def main() -> None:
    global tokens
    tokens = get_tokens()

    while True:
        time.sleep(1)
        print(f'{now()} loop')
        ts: int = stamp()

        if any((
            schedule('next_royal',    ts, schedule_royal_maps,    'Royal',    webhook_royal_map),
            schedule('next_seasonal', ts, schedule_seasonal_maps, 'Seasonal', webhook_seasonal_maps),
            schedule('next_totd',     ts, schedule_totd_maps,     'Totd',     webhook_totd_map),
            schedule('next_weekly',   ts, schedule_weekly_maps,   'Weekly',   webhook_weekly_maps, schedule_weekly_warriors),
        )):
            tables_to_json()
            to_github()


if __name__ == '__main__':
    main()
    # tables_to_json()
    # to_github()

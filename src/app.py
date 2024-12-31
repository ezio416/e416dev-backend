# c 2024-12-26
# m 2024-12-31

from base64 import b64encode
from datetime import datetime as dt
import json
from math import ceil
import os
import re
import sqlite3 as sql
from time import sleep, time
import zipfile

from discord_webhook import DiscordEmbed, DiscordWebhook
from nadeo_api import auth, core, live, oauth
from pytz import timezone as tz
from requests import get, put, Response


accounts:          dict  = {}
tokens:            dict  = {}
par_dir:           str   = f'{os.path.dirname(__file__)}/..'
file_seasonal:     str   = f'{par_dir}/data/seasonal.json'
file_seasonal_raw: str   = f'{par_dir}/data/seasonal_raw.json'
file_db:           str   = f'{par_dir}/data/tm.db'
file_log:          str   = f'{par_dir}/data/tm.log'
file_royal:        str   = f'{par_dir}/data/royal.json'
file_royal_raw:    str   = f'{par_dir}/data/royal_raw.json'
file_totd:         str   = f'{par_dir}/data/totd.json'
file_totd_raw:     str   = f'{par_dir}/data/totd_raw.json'
file_warrior:      str   = f'{par_dir}/data/warrior.json'
file_weekly:       str   = f'{par_dir}/data/weekly.json'
file_weekly_raw:   str   = f'{par_dir}/data/weekly_raw.json'
file_zone:         str   = f'{par_dir}/data/zone.json'
wait_time:         float = 0.5

def error(func: str, e: Exception) -> None:
    log(f'{func} error: {type(e)} | {e}')

    DiscordWebhook(
        os.environ['dcwh-site-backend-errors'],
        content=f'<@174350279158792192>\n`{now(False)}`\n`{func}()`\n`{type(e)}`\n`{e}`'
    ).execute()


def format_race_time(input_ms: int) -> str:
    min: int = int(input_ms / 60000)
    sec: int = int((input_ms - (min * 60000)) / 1000)
    ms:  int = input_ms % 1000

    return f'{min}:{str(sec).zfill(2)}.{str(ms).zfill(3)}'


def get_account_name(account_id: str) -> str:
    log(f"called get_account_name('{account_id}')")

    global accounts

    ts: int = int(time())

    if account_id in accounts and ts < accounts[account_id]['ts']:
        return accounts[account_id]['name']

    sleep(wait_time)
    req = oauth.account_names_from_ids(tokens['oauth'], account_id)

    name: str = req[account_id]
    accounts[account_id] = {}
    accounts[account_id]['name'] = name
    accounts[account_id]['ts'] = ts + 3600  # keep valid for 1 hour

    log(f"get_account_name('{account_id}'): {name}")

    return name


def get_map_infos(table: str) -> None:
    log(f"called get_map_info('{table}')")

    maps_by_uid: dict = {}
    uid_groups:  list = []
    uid_limit:   int  = 270
    uids:        list = []

    try:
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
            log(f'get_map_info {i + 1}/{len(uid_groups)} groups...')

            sleep(wait_time)
            info: dict = core.get(tokens['core'], 'maps', {'mapUidList': group})

            for entry in info:
                map: dict = maps_by_uid[entry['mapUid']]

                map['author']          = entry['author']
                map['authorTime']      = entry['authorScore']
                map['bronzeTime']      = entry['bronzeScore']
                map['downloadUrl']     = entry['fileUrl']
                map['goldTime']        = entry['goldScore']
                map['mapId']           = entry['mapId']
                map['name']            = entry['name']
                map['silverTime']      = entry['silverScore']
                map['submitter']       = entry['submitter']
                map['thumbnailUrl']    = entry['thumbnailUrl']
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
                        downloadUrl     = "{map['downloadUrl']}",
                        goldTime        = "{map['goldTime']}",
                        mapId           = "{map['mapId']}",
                        name            = "{map['name']}",
                        silverTime      = "{map['silverTime']}",
                        submitter       = "{map['submitter']}",
                        thumbnailUrl    = "{map['thumbnailUrl']}",
                        timestampUpload = "{map['timestampUpload']}"
                    WHERE mapUid = "{uid}"
                    ;
                ''')

    except Exception as e:
        error('get_map_info', e)


def get_tokens() -> dict:
    log('getting core token')
    token_core: auth.Token = auth.get_token(
        auth.audience_core,
        os.environ['TM_E416DEV_SERVER_USERNAME'],
        os.environ['TM_E416DEV_SERVER_PASSWORD'],
        os.environ['TM_E416DEV_AGENT'],
        True
    )

    log('getting live token')
    token_live: auth.Token = auth.get_token(
        auth.audience_live,
        os.environ['TM_E416DEV_SERVER_USERNAME'],
        os.environ['TM_E416DEV_SERVER_PASSWORD'],
        os.environ['TM_E416DEV_AGENT'],
        True
    )

    log('getting oauth token')
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


def read_db_key_val(key: str) -> str:
    # log(f'called read_db_key_val({key})')

    try:
        with sql.connect(file_db) as con:
            cur: sql.Cursor = con.cursor()
            return cur.execute(f'SELECT * FROM KeyVals WHERE key = "{key}"').fetchone()[1]

    except TypeError as e:
        log(f"(silent) read_db_key_val('{key}') TypeError {e}")
        return ''

    except Exception as e:
        error('read_db_key_val', e)
        return ''


def schedule_royal_maps() -> None:
    log('called schedule_royal_maps()')

    try:
        sleep(wait_time)
        maps_royal: dict = live.maps_royal(tokens['live'], 99)

        if os.path.isfile(file_royal_raw):
            ts: int = int(time())
            with zipfile.ZipFile(f'{par_dir}/data/history/royal_raw_{ts}.zip', 'w', zipfile.ZIP_LZMA, compresslevel=5) as zip:
                zip.write(file_royal_raw, 'royal_raw.json')

        with open(file_royal_raw, 'w', newline='\n') as f:
            json.dump(maps_royal, f, indent=4)
            f.write('\n')

        write_db_key_val('next_royal', maps_royal['nextRequestTimestamp'])

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
                    downloadUrl     CHAR(86),
                    goldTime        INT,
                    mapId           CHAR(36),
                    mapUid          VARCHAR(27) PRIMARY KEY,
                    month           INT,
                    monthDay        INT,
                    name            TEXT,
                    silverTime      INT,
                    submitter       CHAR(36),
                    thumbnailUrl    CHAR(90),
                    timestampEnd    INT,
                    timestampStart  INT,
                    timestampUpload INT,
                    weekDay         INT,
                    year            INT
                );
            ''')

            mapUids: set = set()

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

                    cur.execute(f'''
                        INSERT INTO Royal (
                            campaignId,
                            mapUid,
                            month,
                            monthDay,
                            timestampEnd,
                            timestampStart,
                            weekDay,
                            year
                        ) VALUES (
                            "{map['campaignId']}",
                            "{mapUid}",
                            "{month['month']}",
                            "{map['monthDay']}",
                            "{map['endTimestamp']}",
                            "{map['startTimestamp']}",
                            "{map['day']}",
                            "{month['year']}"
                        )
                    ''')

    except Exception as e:
        error('schedule_royal_maps', e)


def schedule_seasonal_maps() -> None:
    log('called schedule_seasonal_maps()')

    try:
        sleep(wait_time)
        maps_seasonal: dict = live.maps_campaign(tokens['live'], 99)

        if os.path.isfile(file_seasonal_raw):
            ts: int = int(time())
            with zipfile.ZipFile(f'{par_dir}/data/history/seasonal_raw_{ts}.zip', 'w', zipfile.ZIP_LZMA, compresslevel=5) as zip:
                zip.write(file_seasonal_raw, 'seasonal_raw.json')

        with open(file_seasonal_raw, 'w', newline='\n') as f:
            json.dump(maps_seasonal, f, indent=4)
            f.write('\n')

        write_db_key_val('next_seasonal', maps_seasonal['nextRequestTimestamp'])
        write_db_key_val('warrior_seasonal', maps_seasonal['nextRequestTimestamp'] + 1209600)  # +2 weeks

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
                    downloadUrl          CHAR(86),
                    goldTime             INT,
                    leaderboardGroupUid  CHAR(36),
                    mapId                CHAR(36),
                    mapIndex             INT,
                    mapUid               VARCHAR(27) PRIMARY KEY,
                    name                 VARCHAR(16),
                    seasonUid            CHAR(36),
                    silverTime           INT,
                    submitter            CHAR(36),
                    thumbnailUrl         CHAR(90),
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
                            "{campaign['seasonUid']}",
                            "{campaign['editionTimestamp']}",
                            "{campaign['endTimestamp']}",
                            "{campaign['publicationTimestamp']}",
                            {f'"{timestampRankingSent}"' if timestampRankingSent is not None else 'NULL'},
                            "{campaign['startTimestamp']}"
                        )
                    ''')

    except Exception as e:
        error('schedule_seasonal_maps', e)


def schedule_seasonal_warriors() -> None:
    log('called schedule_seasonal_warriors()')


def schedule_totd_maps() -> None:
    log('called schedule_totd_maps()')

    try:
        sleep(wait_time)
        maps_totd: dict = live.maps_totd(tokens['live'], 99)

        if os.path.isfile(file_totd_raw):
            ts: int = int(time())
            with zipfile.ZipFile(f'{par_dir}/data/history/totd_raw_{ts}.zip', 'w', zipfile.ZIP_LZMA, compresslevel=5) as zip:
                zip.write(file_totd_raw, 'totd_raw.json')

        with open(file_totd_raw, 'w', newline='\n') as f:
            json.dump(maps_totd, f, indent=4)
            f.write('\n')

        write_db_key_val('next_totd', maps_totd['nextRequestTimestamp'])
        write_db_key_val('warrior_totd', maps_totd['nextRequestTimestamp'] + 7200)  # +2 hours

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
                    downloadUrl     CHAR(86),
                    goldTime        INT,
                    mapId           CHAR(36),
                    mapUid          VARCHAR(27) PRIMARY KEY,
                    month           INT,
                    monthDay        INT,
                    name            TEXT,
                    seasonUid       CHAR(36),
                    silverTime      INT,
                    submitter       CHAR(36),
                    thumbnailUrl    CHAR(90),
                    timestampEnd    INT,
                    timestampStart  INT,
                    timestampUpload INT,
                    weekDay         INT,
                    year            INT
                );
            ''')

            for month in reversed(maps_totd['monthList']):
                for map in month['days']:
                    mapUid: str = map['mapUid']
                    if len(mapUid) == 0:
                        break

                    cur.execute(f'''
                        INSERT INTO Totd (
                            campaignId,
                            mapUid,
                            month,
                            monthDay,
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
                            "{map['seasonUid']}",
                            "{map['endTimestamp']}",
                            "{map['startTimestamp']}",
                            "{map['day']}",
                            "{month['year']}"
                        )
                    ''')

    except Exception as e:
        error('schedule_totd_maps', e)


def schedule_totd_warrior() -> None:
    log('called schedule_totd_warrior()')


def schedule_weekly_maps() -> None:
    log('called schedule_weekly_maps()')

    try:
        sleep(wait_time)
        maps_weekly: dict = live.get(tokens['live'], 'api/campaign/weekly-shorts?length=99')

        if os.path.isfile(file_weekly_raw):
            ts: int = int(time())
            with zipfile.ZipFile(f'{par_dir}/data/history/weekly_raw_{ts}.zip', 'w', zipfile.ZIP_LZMA, compresslevel=5) as zip:
                zip.write(file_weekly_raw, 'weekly_raw.json')

        with open(file_weekly_raw, 'w', newline='\n') as f:
            json.dump(maps_weekly, f, indent=4)
            f.write('\n')

        write_db_key_val('next_weekly', maps_weekly['nextRequestTimestamp'])

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
                    downloadUrl          CHAR(86),
                    goldTime             INT,
                    mapId                CHAR(36),
                    mapIndex             INT,
                    mapUid               VARCHAR(27) PRIMARY KEY,
                    name                 TEXT,
                    seasonUid            CHAR(36),
                    silverTime           INT,
                    submitter            CHAR(36),
                    thumbnailUrl         CHAR(90),
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
                            "{campaign['seasonUid']}",
                            "{campaign['editionTimestamp']}",
                            "{campaign['endTimestamp']}",
                            {f'"{timestampRankingSent}"' if timestampRankingSent is not None else 'NULL'},
                            "{campaign['startTimestamp']}",
                            "{campaign['week']}",
                            "{campaign['year']}"
                        )
                    ''')

    except Exception as e:
        error('schedule_weekly_maps', e)


def schedule_weekly_warriors() -> None:
    log('called schedule_weekly_warriors()')


def strip_format_codes(raw: str) -> str:
    # return re.sub(r'\$(?:(\$)|[0-9a-fA-F]{2,3}|[lh]\[.*?\]|[lh]\[|.)', '', raw).strip()
    return re.sub(r'\$([0-9a-fA-F]{1,3}|[iIoOnNmMwWsSzZtTgG<>]|[lLhHpP](\[[^\]]+\])?)', '', raw).strip()


def webhook_royal_map() -> None:
    pass


def webhook_seasonal_maps() -> None:
    log(f'called webhook_seasonal_maps()')

    maps: list[dict] = []
    series: tuple[str] = 'FFFFFF', '66FF66', '6666FF', 'FF4444', '666666'

    try:
        with sql.connect(file_db) as con:
            con.row_factory = sql.Row
            cur: sql.Cursor = con.cursor()

            cur.execute('BEGIN')
            for entry in cur.execute('SELECT * FROM Seasonal ORDER BY campaignIndex DESC').fetchmany(25):
                maps.append(dict(entry))

        for map in maps:
            sleep(1)

            webhook: DiscordWebhook = DiscordWebhook(os.environ['dcwh-tm-seasonal-updates'])

            embed: DiscordEmbed = DiscordEmbed(
                strip_format_codes(map['name']),
                color=series[int(map['mapIndex'] / 5)]
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

            embed.add_embed_field('Links', f'[Trackmania.io](https://trackmania.io/#/leaderboard/{map['mapUid']})')

            embed.set_thumbnail(map['thumbnailUrl'])
            webhook.add_embed(embed)
            webhook.execute()

    except Exception as e:
        error('webhook_seasonal_maps', e)


def webhook_totd_map() -> None:
    pass


def webhook_weekly_maps() -> None:
    log(f'called webhook_weekly_maps()')

    maps: list[dict] = []

    try:
        with sql.connect(file_db) as con:
            con.row_factory = sql.Row
            cur: sql.Cursor = con.cursor()

            cur.execute('BEGIN')
            for entry in cur.execute('SELECT * FROM Weekly ORDER BY week DESC, mapIndex ASC;').fetchmany(5):
                maps.append(dict(entry))

        for map in maps:
            sleep(1)

            webhook: DiscordWebhook = DiscordWebhook(os.environ['dcwh-tm-weekly-updates'])

            embed: DiscordEmbed = DiscordEmbed(
                strip_format_codes(map['name']),
                f'by [{get_account_name(map['author'])}](https://trackmania.io/#/player/{map['author']})\nWeek {map['week']}',
                color='FFDD00'
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

            embed.add_embed_field('Links', f'[Trackmania.io](https://trackmania.io/#/leaderboard/{map['mapUid']})')

            embed.set_thumbnail(map['thumbnailUrl'])
            webhook.add_embed(embed)
            webhook.execute()

    except Exception as e:
        error('webhook_weekly_maps', e)


def write_db_key_val(key: str, val) -> None:
    log(f"called write_db_key_val('{key}', '{val}')")

    try:
        with sql.connect(file_db) as con:
            cur: sql.Cursor = con.cursor()
            cur.execute('BEGIN')
            cur.execute('CREATE TABLE IF NOT EXISTS KeyVals (key TEXT PRIMARY KEY, val TEXT);')
            cur.execute(f'REPLACE INTO KeyVals (key, val) VALUES ("{key}", "{val}")')

    except Exception as e:
        error('write_db_key_val', e)


def main() -> None:
    global tokens
    tokens = get_tokens()

    while True:
        sleep(1)
        print(f'{now()} loop')
        ts: int = int(time())

        val: str = read_db_key_val('next_weekly')
        if ts > (int(val) if len(val) > 0 else 0):
            schedule_weekly_maps()
            get_map_infos('Weekly')
            webhook_weekly_maps()

        val = read_db_key_val('next_seasonal')
        if ts > (int(val) if len(val) > 0 else 0):
            schedule_seasonal_maps()
            get_map_infos('Seasonal')
            webhook_seasonal_maps()

        val = read_db_key_val('next_totd')
        if ts > (int(val) if len(val) > 0 else 0):
            schedule_totd_maps()
            get_map_infos('Totd')
            webhook_totd_map()

        val = read_db_key_val('next_royal')
        if ts > (int(val) if len(val) > 0 else 0):
            schedule_royal_maps()
            get_map_infos('Royal')
            webhook_royal_map()

        pass


if __name__ == '__main__':
    main()

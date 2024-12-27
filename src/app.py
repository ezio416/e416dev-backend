# c 2024-12-26
# m 2024-12-27

from base64 import b64encode
from datetime import datetime as dt
import json
from math import ceil
import os
import re
import sqlite3 as sql
from time import sleep, time

from discord_webhook import DiscordEmbed, DiscordWebhook
from nadeo_api import auth, core, live, oauth
from pytz import timezone as tz
from requests import get, put, Response


par_dir:           str = f'{os.path.dirname(__file__)}/..'
file_campaign:     str = f'{par_dir}/data/campaign.json'
file_campaign_raw: str = f'{par_dir}/data/campaign_raw.json'
file_db:           str = f'{par_dir}/data/tm.db'
file_log:          str = f'{par_dir}/data/tm.log'
file_royal:        str = f'{par_dir}/data/royal.json'
file_royal_raw:    str = f'{par_dir}/data/royal_raw.json'
file_totd:         str = f'{par_dir}/data/totd.json'
file_totd_raw:     str = f'{par_dir}/data/totd_raw.json'
file_warrior:      str = f'{par_dir}/data/warrior.json'
file_weekly:       str = f'{par_dir}/data/weekly.json'
file_weekly_raw:   str = f'{par_dir}/data/weekly_raw.json'
file_zone:         str = f'{par_dir}/data/zone.json'


def error(func: str, e: Exception) -> None:
    log(f'{func} error: {type(e)} | {e}')

    DiscordWebhook(
        os.environ['dcwh-site-backend-errors'],
        content=f'<@174350279158792192>\n`{func}()`\n`{type(e)}`\n`{e}`'
    ).execute()


def format_race_time(input_ms: int) -> str:
    min: int = int(input_ms / 60000)
    sec: int = int((input_ms - (min * 60000)) / 1000)
    ms:  int = input_ms % 1000

    return f'{min}:{str(sec).zfill(2)}.{str(ms).zfill(3)}'


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
            - `0.125` - 1/8 of the way between AT and WR (`9.750`) (default for TOTDs)
            - `0.250` - 1/4 of the way between AT and WR (`9.500`) (default, default for campaigns)
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


def schedule_campaign_maps(tokens: dict[auth.Token]) -> None:
    log(f'called schedule_campaign_maps({tokens})')

    try:
        sleep(1)
        maps_campaign: dict = live.maps_campaign(tokens['live'], 99)
        with open(file_campaign_raw, 'w', newline='\n') as f:
            json.dump(maps_campaign, f, indent=4)
            f.write('\n')

        write_db_key_val('next_campaign', maps_campaign['nextRequestTimestamp'])

    except Exception as e:
        error('schedule_campaign_maps', e)


def schedule_campaign_warriors(tokens: dict[auth.Token]) -> None:
    log(f'called schedule_campaign_warriors({tokens})')


def schedule_totd_map(tokens: dict[auth.Token]) -> None:
    log(f'called schedule_totd_map({tokens})')


def schedule_totd_warrior(tokens: dict[auth.Token]) -> None:
    log(f'called schedule_totd_warrior({tokens})')


def schedule_weekly_maps(tokens: dict[auth.Token]) -> None:
    log(f'called schedule_weekly_maps({tokens})')


def schedule_weekly_warriors(tokens: dict[auth.Token]) -> None:
    log(f'called schedule_weekly_warriors({tokens})')


def strip_format_codes(raw: str) -> str:
    # return re.sub(r'\$(?:(\$)|[0-9a-fA-F]{2,3}|[lh]\[.*?\]|[lh]\[|.)', '', raw).strip()
    return re.sub(r'\$([0-9a-fA-F]{1,3}|[iIoOnNmMwWsSzZtTgG<>]|[lLhHpP](\[[^\]]+\])?)', '', raw).strip()


def write_db_key_val(key: str, val) -> None:
    log(f'called write_db_key_val({key}, {val})')

    with sql.connect(file_db) as con:
        cur: sql.Cursor = con.cursor()
        cur.execute('BEGIN')
        cur.execute('CREATE TABLE IF NOT EXISTS KeyVals (key TEXT PRIMARY KEY, val TEXT);')
        cur.execute(f'INSERT INTO KeyVals (key, val) VALUES ("{key}", "{val}")')


def main() -> None:
    tokens: dict[auth.Token] = get_tokens()

    while True:
        sleep(1)
        now: int = time()

        # if now >= next_campaign:
        if True:
            schedule_campaign_maps(tokens)

        pass


if __name__ == '__main__':
    main()

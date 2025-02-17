# c 2025-01-27
# m 2025-02-17

from datetime import datetime as dt
import json
import re
import sqlite3 as sql
import time

from pytz import timezone as tz

from globals import *


def calc_warrior_time(author_time: int, world_record: int, factor: float | None = 0.25) -> int:
    '''
    - `factor` is offset from AT
        - between `0.0` and `1.0`
        - examples, given AT is `10.000` and WR is `8.000`:
            - `0.000` - AT (`10.000`)
            - `0.125` - 1/8 of the way between AT and WR (`9.750`) (default for TOTD)
            - `0.250` - 1/4 of the way between AT and WR (`9.500`) (default, default for seasonal)
            - `0.500` - 1/2 of the way between AT and WR (`9.000`) (default for weekly shorts)
            - `0.750` - 3/4 of the way between AT and WR (`8.500`)
            - `1.000` - WR (`8.000`)
    '''

    return author_time - max(
        int((author_time - world_record) * (factor if factor is not None else 0.25)),
        1
    )


def format_long_time(input_s: int):
    sec = int(input_s)

    week = int(sec / 604_800)
    sec -= week * 604_800

    day = int(sec / 86_400)
    sec -= day * 86_400

    hour = int(sec / 3_600)
    sec -= hour * 3_600

    min = int(sec / 60)
    sec -= min * 60

    ret = ''
    if week:
        ret += f'{week}w'
    if day:
        ret += f'{day}d'
    if hour:
        ret += f'{hour}h'
    if min:
        ret += f'{min}m'
    return f'{ret}{sec}s'


def format_race_time(input_ms: int) -> str:
    min: int = int(input_ms / 60000)
    sec: int = int((input_ms - (min * 60000)) / 1000)
    ms:  int = input_ms % 1000

    return f'{min}:{str(sec).zfill(2)}.{str(ms).zfill(3)}'


def log(msg: str, print_term: bool = True) -> None:
    text: str = f'{now()} {msg}'

    if print_term:
        print(text)

    with open(FILE_LOG, 'a', newline='\n') as f:
        f.write(f'{text.encode('unicode-escape').decode('ascii')}\n')


def now(brackets: bool = True) -> str:
    utc    = dt.now(tz('UTC')).strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
    denver = f'Denver {dt.now(tz('America/Denver')).strftime('%H:%M')}'
    paris  = f'Paris {dt.now(tz('Europe/Paris')).strftime('%H:%M')}'
    return f'{'[' if brackets else ''}{utc} ({denver}, {paris}){']' if brackets else ''}'


def stamp() -> int:
    return int(time.time())


def strip_format_codes(raw: str) -> str:
    return re.sub(r'\$([0-9a-fA-F]{1,3}|[iIoOnNmMwWsSzZtTgG<>]|[lLhHpP](\[[^\]]+\])?)', '', raw).strip()

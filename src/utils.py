# c 2025-01-27
# m 2025-08-04

import datetime
import re
import time

from pytz import timezone as tz

from constants import *


def calc_warrior_time(author_time: int, world_record: int, factor: float | None = 0.25) -> int:
    '''
    - `factor` is offset from AT
        - between `0.0` and `1.0`
        - examples, given AT is `10.000` and WR is `8.000`:
            - `0.000` - AT (`10.000`)
            - `0.125` - 1/8 of the way between AT and WR (`9.750`) (tracks of the day)
            - `0.250` - 1/4 of the way between AT and WR (`9.500`) (seasonal campaigns)
            - `0.500` - 1/2 of the way between AT and WR (`9.000`) (weekly shorts/club campaigns)
            - `0.750` - 3/4 of the way between AT and WR (`8.500`)
            - `1.000` - WR (`8.000`)
    '''

    return author_time - max(
        int((author_time - world_record) * (factor if factor is not None else 0.25)),
        1
    )


def days_to_seconds(days: int) -> int:
    return days * SECONDS_IN_DAY


def format_long_time(input_s: int) -> str:
    sec = int(input_s)

    week = int(sec / SECONDS_IN_WEEK)
    sec -= week * SECONDS_IN_WEEK

    day = int(sec / SECONDS_IN_DAY)
    sec -= day * SECONDS_IN_DAY

    hour = int(sec / SECONDS_IN_HOUR)
    sec -= hour * SECONDS_IN_HOUR

    min = int(sec / SECONDS_IN_MINUTE)
    sec -= min * SECONDS_IN_MINUTE

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
    min: int = int(input_ms / 60_000)
    sec: int = int((input_ms - (min * 60_000)) / 1_000)
    ms:  int = input_ms % 1_000

    return f'{min}:{str(sec).zfill(2)}.{str(ms).zfill(3)}'


def hours_to_seconds(hours: int) -> int:
    return hours * SECONDS_IN_HOUR


def log(msg: str, print_term: bool = True, log_file: bool = True) -> None:
    text = f'{now()} {msg}'

    if print_term:
        print(text, end='\r' if text.endswith(')] loop') else '\n')

    if log_file:
        with open(FILE_LOG, 'a', newline='\n') as f:
            f.write(f'{text.encode('unicode-escape').decode('ascii')}\n')


def minutes_to_seconds(minutes: int) -> int:
    return minutes * SECONDS_IN_MINUTE


def now(brackets: bool = True) -> str:
    utc    = datetime.datetime.now(tz('UTC')).strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
    denver = f'Denver {datetime.datetime.now(tz('America/Denver')).strftime('%H:%M')}'
    paris  = f'Paris {datetime.datetime.now(tz('Europe/Paris')).strftime('%H:%M')}'
    return f'{'[' if brackets else ''}{utc} ({denver}, {paris}){']' if brackets else ''}'


def stamp() -> int:
    return int(time.time())


def strip_format_codes(raw: str) -> str:
    return re.sub(r'\$([0-9a-f]{1,3}|[gimnostuwz<>]|[hlp](\[[^\]]+\])?)', '', raw, flags=re.IGNORECASE).strip()


def weeks_to_seconds(weeks: int) -> int:
    return weeks * SECONDS_IN_WEEK

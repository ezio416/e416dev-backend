# c 2025-01-27
# m 2025-04-01

from discord_webhook import DiscordEmbed, DiscordWebhook

from api import get_account_name
from errors import safelogged
from files import Cursor
from utils import *


def execute_schedule(webhook: DiscordWebhook, embed: DiscordEmbed, map: dict) -> None:
    embed_str: str = f'{MEDAL_AUTHOR} {format_race_time(map['authorTime'])}'
    embed_str += f'\n{MEDAL_GOLD} {format_race_time(map['goldTime'])}'
    embed_str += f'\n{MEDAL_SILVER} {format_race_time(map['silverTime'])}'
    embed_str += f'\n{MEDAL_BRONZE} {format_race_time(map['bronzeTime'])}'
    embed.add_embed_field('Medals', embed_str, False)

    embed.set_thumbnail(f'https://core.trackmania.nadeo.live/maps/{map['mapId']}/thumbnail.jpg')

    webhook.add_embed(embed)
    time.sleep(DISCORD_WAIT_TIME)
    webhook.execute()


def execute_warrior(webhook: DiscordWebhook, embed: DiscordEmbed, map: dict) -> None:
    at: int = map['authorTime']
    wm: int = map['warriorTime']
    wr: int = map['worldRecord']

    fmt_rt = format_race_time

    if wr <= wm:
        embed_str: str = f'🥇 {fmt_rt(wr)}'
        embed_str += f'\n{MEDAL_WARRIOR} **{fmt_rt(wm)}** *(+{fmt_rt(wm - wr)})*'
        embed_str += f'\n{MEDAL_AUTHOR} {fmt_rt(at)} *(+{fmt_rt(at - wm)})*'

    else:
        embed_str: str = f'{MEDAL_WARRIOR} **{fmt_rt(wm)}**'
        embed_str += f'\n{MEDAL_AUTHOR} {fmt_rt(at)} *(+{fmt_rt(at - wm)})*'
        embed_str += f'\n🥇 {fmt_rt(wr)} *(+{fmt_rt(wr - at)})*'

    embed.add_embed_field('Times', embed_str, False)

    webhook.add_embed(embed)
    time.sleep(DISCORD_WAIT_TIME)
    webhook.execute()
    pass


@safelogged(bool)
def webhook_royal(tokens: dict) -> bool:  # still need to check if map is new
    with Cursor(FILE_DB) as db:
        map: dict = dict(db.execute('SELECT * FROM Royal ORDER BY number DESC').fetchone())

    if not (account_name := get_account_name(tokens, map['author'])):
        raise ValueError(f'no account name for {map['author']}')

    execute_schedule(
        DiscordWebhook(os.environ['DCWH_TM_ROYAL_UPDATES']),
        DiscordEmbed(
            f'{map['year']}-{str(map['month']).zfill(2)}-{str(map['monthDay']).zfill(2)}',
            f'[{strip_format_codes(map['name'])}](https://trackmania.io/#/leaderboard/{map['mapUid']\
                })\nby [{account_name}](https://trackmania.io/#/player/{map['author']})',
            color='FFAA00'
        ),
        map
    )

    return True


@safelogged(bool)
def webhook_seasonal(tokens: dict) -> bool:
    maps: list[dict] = []

    with Cursor(FILE_DB) as db:
        for entry in db.execute('SELECT * FROM Seasonal ORDER BY campaignIndex DESC').fetchmany(25):
            maps.append(dict(entry))

    for map in maps:
        execute_schedule(
            DiscordWebhook(os.environ['DCWH_TM_SEASONAL_UPDATES']),
            DiscordEmbed(
                strip_format_codes(map['name']),
                f'[Trackmania.io](https://trackmania.io/#/leaderboard/{map['mapUid']})',
                color=CAMPAIGN_SERIES[int(map['mapIndex'] / 5)]
            ),
            map
        )

    return True


@safelogged(bool)
def webhook_seasonal_warriors() -> bool:
    maps: list[dict] = []

    with Cursor(FILE_DB) as db:
        for entry in db.execute('SELECT * FROM WarriorSeasonal ORDER BY campaignId DESC, name ASC;').fetchmany(25):
            maps.append(dict(entry))

    for map in maps:
        execute_warrior(
            DiscordWebhook(os.environ['DCWH_TM_WARRIOR_UPDATES']),
            DiscordEmbed(
                f'{map['name']}',
                f'[Trackmania.io](https://trackmania.io/#/leaderboard/{map['mapUid']})',
                color=COLOR_WARRIOR
            ),
            map
        )

    return True


@safelogged(bool)
def webhook_totd(tokens: dict) -> bool:
    with Cursor(FILE_DB) as db:
        map: dict = dict(db.execute('SELECT * FROM Totd ORDER BY number DESC').fetchone())

    if not (account_name := get_account_name(tokens, map['author'])):
        raise ValueError(f'no account name for {map['author']}')

    execute_schedule(
        DiscordWebhook(os.environ['DCWH_TM_TOTD_UPDATES']),
        DiscordEmbed(
            f'{map['year']}-{str(map['month']).zfill(2)}-{str(map['monthDay']).zfill(2)}',
            f'[{strip_format_codes(map['name'])}](https://trackmania.io/#/leaderboard/{map['mapUid']\
                })\nby [{account_name}](https://trackmania.io/#/player/{map['author']})',
            color='00CCFF'
        ),
        map
    )

    return True


@safelogged(bool)
def webhook_totd_warrior() -> bool:
    with Cursor(FILE_DB) as db:
        map: dict = dict(db.execute('SELECT * FROM WarriorTotd ORDER BY date DESC').fetchone())

    execute_warrior(
        DiscordWebhook(os.environ['DCWH_TM_WARRIOR_UPDATES']),
        DiscordEmbed(
            f'Track of the Day {map['date']}',
            f'[{strip_format_codes(map['name'])}](https://trackmania.io/#/leaderboard/{map['mapUid']})',
            color=COLOR_WARRIOR
        ),
        map
    )

    return True


@safelogged(bool)
def webhook_weekly(tokens: dict) -> bool:
    maps: list[dict] = []

    with Cursor(FILE_DB) as db:
        for entry in db.execute('SELECT * FROM Weekly ORDER BY week DESC, mapIndex ASC;').fetchmany(5):
            maps.append(dict(entry))

    for map in maps:
        if not (account_name := get_account_name(tokens, map['author'])):
            raise ValueError(f'no account name for {map['author']}')

        execute_schedule(
            DiscordWebhook(os.environ['DCWH_TM_WEEKLY_UPDATES']),
            DiscordEmbed(
                f'Week {map['week']}, Map {map['number']}',
                f'[{strip_format_codes(map['name'])}](https://trackmania.io/#/leaderboard/{map['mapUid']\
                    })\nby [{account_name}](https://trackmania.io/#/player/{map['author']})',
                color=CAMPAIGN_SERIES[map['mapIndex']]
            ),
            map
        )

    return True


@safelogged(bool)
def webhook_weekly_warriors() -> bool:
    maps: list[dict] = []

    with Cursor(FILE_DB) as db:
        for entry in reversed(db.execute('SELECT * FROM WarriorWeekly ORDER BY number DESC').fetchmany(5)):
            maps.append(dict(entry))

    for map in maps:
        execute_warrior(
            DiscordWebhook(os.environ['DCWH_TM_WARRIOR_UPDATES']),
            DiscordEmbed(
                f'Weekly Short #{map['number']}',
                f'[{strip_format_codes(map['name'])}](https://trackmania.io/#/leaderboard/{map['mapUid']})',
                color=COLOR_WARRIOR
            ),
            map
        )

    return True

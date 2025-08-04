# c 2025-01-27
# m 2025-08-04

import time

import discord_webhook

import api
from constants import *
import errors
import files
import utils


def execute_schedule(url: str, embed: discord_webhook.DiscordEmbed, map: dict) -> None:
    embed_str: str = f'{MEDAL_AUTHOR} {utils.format_race_time(map['authorTime'])}'
    embed_str += f'\n{MEDAL_GOLD} {utils.format_race_time(map['goldTime'])}'
    embed_str += f'\n{MEDAL_SILVER} {utils.format_race_time(map['silverTime'])}'
    embed_str += f'\n{MEDAL_BRONZE} {utils.format_race_time(map['bronzeTime'])}'
    embed.add_embed_field('Medals', embed_str, False)

    embed.set_thumbnail(f'https://core.trackmania.nadeo.live/maps/{map['mapId']}/thumbnail.jpg')

    webhook = discord_webhook.DiscordWebhook(url)
    webhook.add_embed(embed)
    time.sleep(DISCORD_WAIT_TIME)
    webhook.execute()


def execute_warrior(url: str, embed: discord_webhook.DiscordEmbed, map: dict) -> None:
    at: int = map['authorTime']
    wm: int = map['warriorTime']
    wr: int = map['worldRecord']

    if wr <= wm:
        embed_str: str = f'🥇 {utils.format_race_time(wr)}'
        embed_str += f'\n{MEDAL_WARRIOR} **{utils.format_race_time(wm)}** *(+{utils.format_race_time(wm - wr)})*'
        embed_str += f'\n{MEDAL_AUTHOR} {utils.format_race_time(at)} *(+{utils.format_race_time(at - wm)})*'

    else:
        embed_str: str = f'{MEDAL_WARRIOR} **{utils.format_race_time(wm)}**'
        embed_str += f'\n{MEDAL_AUTHOR} {utils.format_race_time(at)} *(+{utils.format_race_time(at - wm)})*'
        embed_str += f'\n🥇 {utils.format_race_time(wr)} *(+{utils.format_race_time(wr - at)})*'

    embed.add_embed_field('Times', embed_str, False)

    webhook = discord_webhook.DiscordWebhook(url)
    webhook.add_embed(embed)
    time.sleep(DISCORD_WAIT_TIME)
    webhook.execute()


@errors.safelogged(bool)
def webhook_seasonal(tokens: dict) -> bool:
    maps: list[dict] = []

    with files.Cursor(FILE_DB) as db:
        for entry in db.execute('SELECT * FROM Seasonal ORDER BY campaignIndex DESC').fetchmany(25):
            maps.append(dict(entry))

    for map in maps:
        execute_schedule(
            os.environ['DCWH_TM_SEASONAL_UPDATES'],
            discord_webhook.DiscordEmbed(
                utils.strip_format_codes(map['name']),
                f'[Trackmania.io](https://trackmania.io/#/leaderboard/{map['mapUid']})',
                color=CAMPAIGN_SERIES[int(map['mapIndex'] / 5)]
            ),
            map
        )

    return True


@errors.safelogged(bool)
def webhook_seasonal_warriors() -> bool:
    maps: list[dict] = []

    with files.Cursor(FILE_DB) as db:
        for entry in db.execute('SELECT * FROM WarriorSeasonal ORDER BY campaignId DESC, name ASC;').fetchmany(25):
            maps.append(dict(entry))

    for map in maps:
        execute_warrior(
            os.environ['DCWH_TM_WARRIOR_UPDATES'],
            discord_webhook.DiscordEmbed(
                f'{map['name']}',
                f'[Trackmania.io](https://trackmania.io/#/leaderboard/{map['mapUid']})',
                color=COLOR_WARRIOR
            ),
            map
        )

    return True


@errors.safelogged(bool)
def webhook_totd(tokens: dict) -> bool:
    with files.Cursor(FILE_DB) as db:
        map: dict = dict(db.execute('SELECT * FROM Totd ORDER BY number DESC').fetchone())

    if not (account_name := api.get_account_name(tokens, map['author'])):
        raise ValueError(f'no account name for {map['author']}')

    execute_schedule(
        os.environ['DCWH_TM_TOTD_UPDATES'],
        discord_webhook.DiscordEmbed(
            f'{map['year']}-{str(map['month']).zfill(2)}-{str(map['monthDay']).zfill(2)}',
            f'[{utils.strip_format_codes(map['name'])}](https://trackmania.io/#/leaderboard/{map['mapUid']\
                })\nby [{account_name}](https://trackmania.io/#/player/{map['author']})',
            color='00CCFF'
        ),
        map
    )

    return True


@errors.safelogged(bool)
def webhook_totd_warrior() -> bool:
    with files.Cursor(FILE_DB) as db:
        map: dict = dict(db.execute('SELECT * FROM WarriorTotd ORDER BY date DESC').fetchone())

    execute_warrior(
        os.environ['DCWH_TM_WARRIOR_UPDATES'],
        discord_webhook.DiscordEmbed(
            f'Track of the Day {map['date']}',
            f'[{utils.strip_format_codes(map['name'])}](https://trackmania.io/#/leaderboard/{map['mapUid']})',
            color=COLOR_WARRIOR
        ),
        map
    )

    return True


@errors.safelogged(bool)
def webhook_weekly(tokens: dict) -> bool:
    maps: list[dict] = []

    with files.Cursor(FILE_DB) as db:
        for entry in db.execute('SELECT * FROM Weekly ORDER BY week DESC, mapIndex ASC;').fetchmany(5):
            maps.append(dict(entry))

    for map in maps:
        if not (account_name := api.get_account_name(tokens, map['author'])):
            raise ValueError(f'no account name for {map['author']}')

        execute_schedule(
            os.environ['DCWH_TM_WEEKLY_UPDATES'],
            discord_webhook.DiscordEmbed(
                f'Week {map['week']}, Map {map['number']}',
                f'[{utils.strip_format_codes(map['name'])}](https://trackmania.io/#/leaderboard/{map['mapUid']\
                    })\nby [{account_name}](https://trackmania.io/#/player/{map['author']})',
                color=CAMPAIGN_SERIES[map['mapIndex']]
            ),
            map
        )

    return True


@errors.safelogged(bool)
def webhook_weekly_warriors() -> bool:
    maps: list[dict] = []

    with files.Cursor(FILE_DB) as db:
        for entry in reversed(db.execute('SELECT * FROM WarriorWeekly ORDER BY number DESC').fetchmany(5)):
            maps.append(dict(entry))

    for map in maps:
        execute_warrior(
            os.environ['DCWH_TM_WARRIOR_UPDATES'],
            discord_webhook.DiscordEmbed(
                f'Weekly Short #{map['number']}',
                f'[{utils.strip_format_codes(map['name'])}](https://trackmania.io/#/leaderboard/{map['mapUid']})',
                color=COLOR_WARRIOR
            ),
            map
        )

    return True

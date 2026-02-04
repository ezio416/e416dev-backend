# c 2025-01-27
# m 2026-02-04

import time

import discord_webhook as dc

import api
from constants import *
import errors
import files
import utils


def execute(webhook: dc.DiscordWebhook) -> None:
    time.sleep(DISCORD_WAIT_TIME)
    webhook.execute()


def execute_schedule(url: str, embed: dc.DiscordEmbed, map: dict, tmx: dict = {}) -> None:
    embed_str: str = f'{MEDAL_AUTHOR} {utils.format_race_time(map['authorTime'])}'
    embed_str += f'\n{MEDAL_GOLD} {utils.format_race_time(map['goldTime'])}'
    embed_str += f'\n{MEDAL_SILVER} {utils.format_race_time(map['silverTime'])}'
    embed_str += f'\n{MEDAL_BRONZE} {utils.format_race_time(map['bronzeTime'])}'
    embed.add_embed_field('Medals', embed_str, False)

    if tmx:
        embed.add_embed_field('TMX', f'[{tmx['id']}]({TMX_BASE_URL}/mapshow/{tmx['id']})')
        if tmx['tags']:
            embed.add_embed_field('Tags', ', '.join(tmx['tags']))

    embed.set_thumbnail(f'https://core.trackmania.nadeo.live/maps/{map['mapId']}/thumbnail.jpg')

    webhook = dc.DiscordWebhook(url)
    webhook.add_embed(embed)
    execute(webhook)


def execute_warrior(url: str, embed: dc.DiscordEmbed, map: dict) -> None:
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

    webhook = dc.DiscordWebhook(url)
    webhook.add_embed(embed)
    execute(webhook)


@errors.safelogged()
def seasonal(tokens: dict) -> None:
    maps: list[dict] = []

    with files.Cursor(FILE_DB) as db:
        for entry in db.execute('SELECT * FROM Seasonal ORDER BY campaignIndex DESC').fetchmany(25):
            maps.append(dict(entry))

    for map in maps:
        execute_schedule(
            os.environ['DCWH_TM_SEASONAL_UPDATES'],
            dc.DiscordEmbed(
                utils.strip_format_codes(map['name']),
                f'[Trackmania.io](https://trackmania.io/#/leaderboard/{map['mapUid']})',
                color=CAMPAIGN_SERIES[int(map['mapIndex'] / 5)]
            ),
            map
        )


@errors.safelogged()
def seasonal_warriors(tokens: dict) -> None:
    maps: list[dict] = []

    with files.Cursor(FILE_DB) as db:
        for entry in db.execute('SELECT * FROM WarriorSeasonal ORDER BY campaignId DESC, name ASC;').fetchmany(25):
            maps.append(dict(entry))

    for map in maps:
        execute_warrior(
            os.environ['DCWH_TM_WARRIOR_UPDATES'],
            dc.DiscordEmbed(
                f'{map['name']}',
                f'[Trackmania.io](https://trackmania.io/#/leaderboard/{map['mapUid']})',
                color=COLOR_WARRIOR
            ),
            map
        )

    return True


@errors.safelogged()
def totd(tokens: dict) -> None:
    with files.Cursor(FILE_DB) as db:
        map: dict = dict(db.execute('SELECT * FROM Totd ORDER BY number DESC').fetchone())

    if not (account_name := api.get_account_name(tokens, map['author'])):
        raise ValueError(f'no account name for {map['author']}')

    execute_schedule(
        os.environ['DCWH_TM_TOTD_UPDATES'],
        dc.DiscordEmbed(
            f'{map['year']}-{str(map['month']).zfill(2)}-{str(map['monthDay']).zfill(2)}',
            f'[{utils.strip_format_codes(map['name'])}](https://trackmania.io/#/leaderboard/{map['mapUid']\
                })\nby [{account_name}](https://trackmania.io/#/player/{map['author']})',
            color='00CCFF'
        ),
        map#,
        #api.get_tmx_info(map['mapUid'])
    )


@errors.safelogged()
def totd_warrior(tokens: dict) -> None:
    with files.Cursor(FILE_DB) as db:
        map: dict = dict(db.execute('SELECT * FROM WarriorTotd ORDER BY date DESC').fetchone())

    execute_warrior(
        os.environ['DCWH_TM_WARRIOR_UPDATES'],
        dc.DiscordEmbed(
            f'Track of the Day {map['date']}',
            f'[{utils.strip_format_codes(map['name'])}](https://trackmania.io/#/leaderboard/{map['mapUid']})',
            color=COLOR_WARRIOR
        ),
        map
    )

    return True


@errors.safelogged()
def weekly_grand(tokens: dict) -> None:
    map: dict = {}

    with files.Cursor(FILE_DB) as db:
        map = dict(db.execute('SELECT * FROM Grand ORDER BY week DESC, mapIndex ASC;').fetchone())

    if not (account_name := api.get_account_name(tokens, map['author'])):
        raise ValueError(f'no account name for {map['author']}')

    execute_schedule(
        os.environ['DCWH_TM_WEEKLY_UPDATES'],
        dc.DiscordEmbed(
            f'Weekly Grand #{map['number']}',
            f'[{utils.strip_format_codes(map['name'])}](https://trackmania.io/#/leaderboard/{map['mapUid']\
                })\nby [{account_name}](https://trackmania.io/#/player/{map['author']})',
            color='DDDD33'
        ),
        map
    )


@errors.safelogged()
def weekly_shorts(tokens: dict) -> None:
    maps: list[dict] = []

    with files.Cursor(FILE_DB) as db:
        for entry in db.execute('SELECT * FROM Weekly ORDER BY week DESC, mapIndex ASC;').fetchmany(5):
            maps.append(dict(entry))

    for map in maps:
        if not (account_name := api.get_account_name(tokens, map['author'])):
            raise ValueError(f'no account name for {map['author']}')

        execute_schedule(
            os.environ['DCWH_TM_WEEKLY_UPDATES'],
            dc.DiscordEmbed(
                f'Week {map['week']}, Map {map['number']}',
                f'[{utils.strip_format_codes(map['name'])}](https://trackmania.io/#/leaderboard/{map['mapUid']\
                    })\nby [{account_name}](https://trackmania.io/#/player/{map['author']})',
                color=CAMPAIGN_SERIES[map['mapIndex']]
            ),
            map
        )


@errors.safelogged()
def weekly_shorts_warriors(tokens: dict) -> None:
    maps: list[dict] = []

    with files.Cursor(FILE_DB) as db:
        for entry in reversed(db.execute('SELECT * FROM WarriorWeekly ORDER BY number DESC').fetchmany(5)):
            maps.append(dict(entry))

    for map in maps:
        execute_warrior(
            os.environ['DCWH_TM_WARRIOR_UPDATES'],
            dc.DiscordEmbed(
                f'Weekly Short #{map['number']}',
                f'[{utils.strip_format_codes(map['name'])}](https://trackmania.io/#/leaderboard/{map['mapUid']})',
                color=COLOR_WARRIOR
            ),
            map
        )

    return True

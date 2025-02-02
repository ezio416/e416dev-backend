# c 2025-01-27
# m 2025-02-02

from discord_webhook import DiscordEmbed, DiscordWebhook

from api import get_account_name
from errors import safelogged
from utils import *


def _webhook_execute(webhook: DiscordWebhook, embed: DiscordEmbed, map: dict) -> None:
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


def _webhook_royal(tokens: dict, map: dict) -> None:
    webhook: DiscordWebhook = DiscordWebhook(os.environ['dcwh-tm-royal-updates'])

    account_name: str = get_account_name(tokens, map['author'])
    if not account_name:
        raise ValueError(f'no account name for {map['author']}')

    embed: DiscordEmbed = DiscordEmbed(
        f'{map['year']}-{str(map['month']).zfill(2)}-{str(map['monthDay']).zfill(2)}',
        f'[{strip_format_codes(map['name'])}](https://trackmania.io/#/leaderboard/{map['mapUid']\
            })\nby [{account_name}](https://trackmania.io/#/player/{map['author']})',
        color='FFAA00'
    )

    _webhook_execute(webhook, embed, map)


@safelogged(bool)
def webhook_royal(tokens: dict) -> bool:  # need to check if map is new
    with sql.connect(FILE_DB) as con:
        con.row_factory = sql.Row
        cur: sql.Cursor = con.cursor()

        cur.execute('BEGIN')
        latest: dict = dict(cur.execute('SELECT * FROM Royal ORDER BY number DESC').fetchone())

    _webhook_royal(tokens, latest)
    return True


def _webhook_seasonal(map: dict) -> None:
    webhook: DiscordWebhook = DiscordWebhook(os.environ['dcwh-tm-seasonal-updates'])

    embed: DiscordEmbed = DiscordEmbed(
        strip_format_codes(map['name']),
        f'[Trackmania.io](https://trackmania.io/#/leaderboard/{map['mapUid']})',
        color=CAMPAIGN_SERIES[int(map['mapIndex'] / 5)]
    )

    _webhook_execute(webhook, embed, map)


@safelogged(bool)
def webhook_seasonal() -> bool:
    maps: list[dict] = []

    with sql.connect(FILE_DB) as con:
        con.row_factory = sql.Row
        cur: sql.Cursor = con.cursor()

        cur.execute('BEGIN')
        for entry in cur.execute('SELECT * FROM Seasonal ORDER BY campaignIndex DESC').fetchmany(25):
            maps.append(dict(entry))

    for map in maps:
        time.sleep(1)
        _webhook_seasonal(map)

    return True


def _webhook_seasonal_warrior(map: dict) -> None:
    webhook: DiscordWebhook = DiscordWebhook(os.environ['dcwh-tm-warrior-updates'])

    embed: DiscordEmbed = DiscordEmbed(
        f'{map['name']}',
        f'[Trackmania.io](https://trackmania.io/#/leaderboard/{map['mapUid']})',
        color='33CCFF'
    )

    at: int = map['authorTime']
    wm: int = map['warriorTime']
    wr: int = map['worldRecord']

    fmt_rt = format_race_time

    if wr <= wm:
        embed_str: str = f'\n🥇 {fmt_rt(wr)}'
        embed_str += f'\n<:MedalWarrior:1305798298690392155> **{fmt_rt(wm)}** *(+{fmt_rt(wm - wr)})*'
        embed_str += f'\n<:MedalAuthor:736600847219294281> {fmt_rt(at)} *(+{fmt_rt(at - wm)})*'

    else:
        embed_str: str = f'\n<:MedalWarrior:1305798298690392155> **{fmt_rt(wm)}**'
        embed_str += f'\n<:MedalAuthor:736600847219294281> {fmt_rt(at)} *(+{fmt_rt(at - wm)})*'
        embed_str += f'\n🥇 {fmt_rt(wr)} *(+{fmt_rt(wr - at)})*'

    embed.add_embed_field('Times', embed_str, False)

    webhook.add_embed(embed)
    webhook.execute()


@safelogged(bool)
def webhook_seasonal_warriors() -> bool:
    maps: list[dict] = []

    with sql.connect(FILE_DB) as con:
        con.row_factory = sql.Row
        cur: sql.Cursor = con.cursor()

        cur.execute('BEGIN')
        for entry in cur.execute('SELECT * FROM WarriorSeasonal ORDER BY campaignId DESC, name ASC;').fetchmany(25):
            maps.append(dict(entry))

    for map in maps:
        time.sleep(1)
        _webhook_seasonal_warrior(map)

    return True


def _webhook_totd(tokens: dict, map: dict) -> None:
    webhook: DiscordWebhook = DiscordWebhook(os.environ['dcwh-tm-totd-updates'])

    account_name: str = get_account_name(tokens, map['author'])
    if not account_name:
        raise ValueError(f'no account name for {map['author']}')

    embed: DiscordEmbed = DiscordEmbed(
        f'{map['year']}-{str(map['month']).zfill(2)}-{str(map['monthDay']).zfill(2)}',
        f'[{strip_format_codes(map['name'])}](https://trackmania.io/#/leaderboard/{map['mapUid']\
            })\nby [{account_name}](https://trackmania.io/#/player/{map['author']})',
        color='00CCFF'
    )

    _webhook_execute(webhook, embed, map)


@safelogged(bool)
def webhook_totd(tokens: dict) -> bool:
    with sql.connect(FILE_DB) as con:
        con.row_factory = sql.Row
        cur: sql.Cursor = con.cursor()
        cur.execute('BEGIN')

        latest: dict = dict(cur.execute('SELECT * FROM Totd ORDER BY number DESC').fetchone())

    _webhook_totd(tokens, latest)
    return True


@safelogged(bool)
def webhook_totd_warrior() -> bool:
    with sql.connect(FILE_DB) as con:
        con.row_factory = sql.Row
        cur: sql.Cursor = con.cursor()
        cur.execute('BEGIN')

        latest: dict = dict(cur.execute('SELECT * FROM WarriorTotd ORDER BY date DESC').fetchone())

    webhook: DiscordWebhook = DiscordWebhook(os.environ['dcwh-tm-warrior-updates'])

    embed: DiscordEmbed = DiscordEmbed(
        f'Track of the Day {latest['date']}',
        f'[{strip_format_codes(latest['name'])}](https://trackmania.io/#/leaderboard/{latest['mapUid']})',
        color='33CCFF'
    )

    at: int = latest['authorTime']
    wm: int = latest['warriorTime']
    wr: int = latest['worldRecord']

    fmt_rt = format_race_time

    if wr <= wm:
        embed_str: str = f'\n🥇 {fmt_rt(wr)}'
        embed_str += f'\n<:MedalWarrior:1305798298690392155> **{fmt_rt(wm)}** *(+{fmt_rt(wm - wr)})*'
        embed_str += f'\n<:MedalAuthor:736600847219294281> {fmt_rt(at)} *(+{fmt_rt(at - wm)})*'

    else:
        embed_str: str = f'\n<:MedalWarrior:1305798298690392155> **{fmt_rt(wm)}**'
        embed_str += f'\n<:MedalAuthor:736600847219294281> {fmt_rt(at)} *(+{fmt_rt(at - wm)})*'
        embed_str += f'\n🥇 {fmt_rt(wr)} *(+{fmt_rt(wr - at)})*'

    embed.add_embed_field('Times', embed_str, False)

    webhook.add_embed(embed)
    webhook.execute()

    return True


def _webhook_weekly(tokens: dict, map: dict) -> None:
    webhook: DiscordWebhook = DiscordWebhook(os.environ['dcwh-tm-weekly-updates'])

    account_name: str = get_account_name(tokens, map['author'])
    if not account_name:
        raise ValueError(f'no account name for {map['author']}')

    embed: DiscordEmbed = DiscordEmbed(
        f'Week {map['week']}, Map {map['number']}',
        f'[{strip_format_codes(map['name'])}](https://trackmania.io/#/leaderboard/{map['mapUid']\
            })\nby [{account_name}](https://trackmania.io/#/player/{map['author']})',
        color=CAMPAIGN_SERIES[map['mapIndex']]
    )

    _webhook_execute(webhook, embed, map)


@safelogged(bool)
def webhook_weekly(tokens: dict) -> bool:
    maps: list[dict] = []

    with sql.connect(FILE_DB) as con:
        con.row_factory = sql.Row
        cur: sql.Cursor = con.cursor()

        cur.execute('BEGIN')
        for entry in cur.execute('SELECT * FROM Weekly ORDER BY week DESC, mapIndex ASC;').fetchmany(5):
            maps.append(dict(entry))

    for map in maps:
        time.sleep(1)
        _webhook_weekly(tokens, map)

    return True


def _webhook_weekly_warrior(map: dict) -> None:
    webhook: DiscordWebhook = DiscordWebhook(os.environ['dcwh-tm-warrior-updates'])

    embed: DiscordEmbed = DiscordEmbed(
        f'Weekly Short #{map['number']}',
        f'[{strip_format_codes(map['name'])}](https://trackmania.io/#/leaderboard/{map['mapUid']})',
        color='33CCFF'
    )

    at: int = map['authorTime']
    wm: int = map['warriorTime']
    wr: int = map['worldRecord']

    fmt_rt = format_race_time

    if wr <= wm:
        embed_str: str = f'\n🥇 {fmt_rt(wr)}'
        embed_str += f'\n<:MedalWarrior:1305798298690392155> **{fmt_rt(wm)}** *(+{fmt_rt(wm - wr)})*'
        embed_str += f'\n<:MedalAuthor:736600847219294281> {fmt_rt(at)} *(+{fmt_rt(at - wm)})*'

    else:
        embed_str: str = f'\n<:MedalWarrior:1305798298690392155> **{fmt_rt(wm)}**'
        embed_str += f'\n<:MedalAuthor:736600847219294281> {fmt_rt(at)} *(+{fmt_rt(at - wm)})*'
        embed_str += f'\n🥇 {fmt_rt(wr)} *(+{fmt_rt(wr - at)})*'

    embed.add_embed_field('Times', embed_str, False)

    webhook.add_embed(embed)
    webhook.execute()


@safelogged(bool)
def webhook_weekly_warriors() -> bool:
    maps: list[dict] = []

    with sql.connect(FILE_DB) as con:
        con.row_factory = sql.Row
        cur: sql.Cursor = con.cursor()

        cur.execute('BEGIN')
        for entry in reversed(cur.execute('SELECT * FROM WarriorWeekly ORDER BY number DESC').fetchmany(5)):
            maps.append(dict(entry))

    for map in maps:
        time.sleep(1)
        _webhook_weekly_warrior(map)

    return True


if __name__ == '__main__':
    webhook_weekly_warriors()

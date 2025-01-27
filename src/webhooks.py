# c 2025-01-27
# m 2025-01-27

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


@safelogged(bool)
def webhook_seasonal_warriors() -> bool:
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


@safelogged(bool)
def webhook_weekly_warriors() -> bool:
    return True

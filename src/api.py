# c 2025-01-27
# m 2025-08-05

import datetime

from nadeo_api import auth, core, oauth

from constants import *
import errors
import files
import utils


accounts: dict[str, dict] = {}


@errors.safelogged(str)
def get_account_name(tokens: dict, account_id: str) -> str:
    if account_id in ('d2372a08-a8a1-46cb-97fb-23a161d85ad0', 'aa02b90e-0652-4a1c-b705-4677e2983003'):
        return 'Nadeo'

    global accounts

    ts: int = utils.stamp()

    if account_id in accounts and ts < accounts[account_id]['ts']:
        return accounts[account_id]['name']

    req: dict = {}

    try:
        req = oauth.get_account_names_from_ids(tokens['oauth'], [account_id])

    except ValueError:
        tokens['oauth'] = get_token_oauth()
        req = oauth.get_account_names_from_ids(tokens['oauth'], [account_id])

    if not req or type(req) is not dict:
        raise ValueError(f'bad account ID: {account_id}')

    name: str = req[account_id]
    accounts[account_id] = {}
    accounts[account_id]['name'] = name
    accounts[account_id]['ts'] = ts + utils.days_to_seconds(1)

    return name


@errors.safelogged(bool)
def get_map_infos(tokens: dict, table: str) -> bool:
    maps_by_uid: dict = {}

    with files.Cursor(FILE_DB) as db:
        for entry in db.execute(f'SELECT * FROM {table}').fetchall():
            map: dict = dict(entry)
            maps_by_uid[map['mapUid']] = map

    info: list[dict] = core.get_map_info(tokens['core'], list(maps_by_uid))

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
        map['timestampUpload'] = int(datetime.datetime.fromisoformat(entry['timestamp']).timestamp())

    with files.Cursor(FILE_DB) as db:
        for uid, map in maps_by_uid.items():
            db.execute(f'''
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


def get_token_core() -> auth.Token:
    utils.log('info: getting core token')
    return auth.get_token(
        auth.audience_core,
        os.environ['TM_E416DEV_SERVER_USERNAME'],
        os.environ['TM_E416DEV_SERVER_PASSWORD'],
        os.environ['TM_E416DEV_AGENT'],
        True
    )


def get_token_live() -> auth.Token:
    utils.log('info: getting live token')
    return auth.get_token(
        auth.audience_live,
        os.environ['TM_E416DEV_SERVER_USERNAME'],
        os.environ['TM_E416DEV_SERVER_PASSWORD'],
        os.environ['TM_E416DEV_AGENT'],
        True
    )


def get_token_oauth() -> auth.Token:
    utils.log('info: getting oauth token')
    return auth.get_token(
        auth.audience_oauth,
        os.environ['TM_OAUTH_IDENTIFIER'],
        os.environ['TM_OAUTH_SECRET']
    )


def get_tokens() -> dict[str, auth.Token]:
    return {
        'core': get_token_core(),
        'live': get_token_live(),
        'oauth': get_token_oauth()
    }

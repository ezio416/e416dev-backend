# c 2025-01-27
# m 2025-02-15

from nadeo_api import auth, core, oauth

from errors import safelogged
from files import Cursor
from utils import *


accounts: dict[str, dict] = {}


@safelogged(str)
def get_account_name(tokens: dict, account_id: str) -> str:
    if account_id == 'd2372a08-a8a1-46cb-97fb-23a161d85ad0':
        return 'Nadeo'

    global accounts

    ts: int = stamp()

    if account_id in accounts and ts < accounts[account_id]['ts']:
        return accounts[account_id]['name']

    req: dict = {}

    try:
        time.sleep(WAIT_TIME)
        req = oauth.account_names_from_ids(tokens['oauth'], account_id)

    except ValueError:
        tokens['oauth'] = get_token_oauth()

        time.sleep(WAIT_TIME)
        req = oauth.account_names_from_ids(tokens['oauth'], account_id)

    if not req or type(req) is not dict:
        raise ValueError(f'bad account ID: {account_id}')

    name: str = req[account_id]
    accounts[account_id] = {}
    accounts[account_id]['name'] = name
    accounts[account_id]['ts'] = ts + 60*60*24

    return name


@safelogged(bool)
def get_map_infos(tokens: dict, table: str) -> bool:
    UID_LIMIT: int = 270

    maps_by_uid: dict = {}
    uid_groups:  list = []
    uids:        list = []

    with Cursor(FILE_DB) as db:
        for entry in db.execute(f'SELECT * FROM {table}').fetchall():
            map: dict = dict(entry)
            maps_by_uid[map['mapUid']] = map

    uids = list(maps_by_uid)
    while True:
        if len(uids) > UID_LIMIT:
            uid_groups.append(','.join(uids[:UID_LIMIT]))
            uids = uids[UID_LIMIT:]
        else:
            uid_groups.append(','.join(uids))
            break

    for i, group in enumerate(uid_groups):
        log(f'info: get_map_info {i + 1}/{len(uid_groups)} groups...')

        time.sleep(WAIT_TIME)
        info: dict = core.get(tokens['core'], 'maps', {'mapUidList': group})

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
            map['timestampUpload'] = int(dt.fromisoformat(entry['timestamp']).timestamp())

    with Cursor(FILE_DB) as db:
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


def get_token_oauth() -> auth.Token:  # workaround for oauth refreshing
    log('info: getting oauth token')
    return auth.get_token(
        auth.audience_oauth,
        os.environ['TM_OAUTH_IDENTIFIER'],
        os.environ['TM_OAUTH_SECRET']
    )


def get_tokens() -> dict:
    log('info: getting core token')
    token_core: auth.Token = auth.get_token(
        auth.audience_core,
        os.environ['TM_E416DEV_SERVER_USERNAME'],
        os.environ['TM_E416DEV_SERVER_PASSWORD'],
        os.environ['TM_E416DEV_AGENT'],
        True
    )

    log('info: getting live token')
    token_live: auth.Token = auth.get_token(
        auth.audience_live,
        os.environ['TM_E416DEV_SERVER_USERNAME'],
        os.environ['TM_E416DEV_SERVER_PASSWORD'],
        os.environ['TM_E416DEV_AGENT'],
        True
    )

    return {
        'core': token_core,
        'live': token_live,
        'oauth': get_token_oauth()
    }

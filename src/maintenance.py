# c 2025-01-27
# m 2025-08-04

import csv
from datetime import timezone

from nadeo_api import live
from requests import post

from api import *
from files import *
from github import *
from utils import *
from webhooks import *


def add_campaign_ids_and_weeks_to_weekly_warriors() -> None:
    with Cursor(FILE_DB) as db:
        for entry in db.execute(f'SELECT * from Weekly').fetchall():
            map = dict(entry)
            db.execute(f'UPDATE WarriorWeekly SET campaignId = "{map['campaignId']}" where mapUid = "{map['mapUid']}"')
            db.execute(f'UPDATE WarriorWeekly SET week = "{map['week']}" where mapUid = "{map['mapUid']}"')

    pass


def add_club_campaign_warriors(club_id: int, campaign_id: int, factor: float = 0.5) -> None:
    # tokens = get_tokens()
    tokens = {'live': get_token_live()}
    maps = get_tops_for_club_campaign(tokens, club_id, campaign_id, factor)

    with Cursor(FILE_DB) as db:
        for i, map in enumerate(maps):
            uid = map['uid']

            db.execute(f'''
                INSERT INTO WarriorOther (
                    authorTime,
                    campaignId,
                    campaignName,
                    clubId,
                    clubName,
                    mapIndex,
                    mapUid,
                    name,
                    warriorTime,
                    worldRecord,
                    mapId,
                    goldTime
                ) VALUES (
                    "{map['at']}",
                    "{map['campaign_id']}",
                    "{map['campaign_name']}",
                    "{map['club_id']}",
                    "{map['club_name']}",
                    "{i}",
                    "{uid}",
                    "{map['name']}",
                    "{map['wm']}",
                    "{map['wr']}",
                    "{map['id']}",
                    "{map['gt']}"
                )
            ''')

    pass


def add_gold_times_to_warriors() -> None:
    with Cursor(FILE_DB) as db:
        # for table_name in 'Seasonal', 'Totd', 'Weekly':
        #     for entry in db.execute(f'SELECT * FROM {table_name}').fetchall():
        #         map = dict(entry)
        #         db.execute(f'UPDATE Warrior{table_name} SET goldTime = {map['goldTime']} WHERE mapUid = "{map['mapUid']}"')

        MAX_UIDS = 291
        token= get_token_core()

        maps = {}
        for entry in db.execute(f'SELECT * from WarriorOther').fetchall():
            map = dict(entry)
            maps[map['mapUid']] = map

        uids = list(maps)
        while len(uids):
            print(f'{len(uids)} maps left')

            uid_count = min(len(uids), MAX_UIDS)
            uids_this_req = uids[:uid_count]
            uids = uids[uid_count:]
            endpoint = f'maps/?mapUidList={','.join(uids_this_req)}'

            time.sleep(0.5)
            req = core.get(token, endpoint)
            for map in req:
                db.execute(f'UPDATE WarriorOther SET goldTime = {map['goldScore']} WHERE mapUid = "{map['mapUid']}"')

    pass


def add_map_ids_to_warriors() -> None:
    MAX_UIDS = 291
    token= get_token_core()

    with Cursor(FILE_DB) as db:
        for table_table in 'Other', 'Seasonal', 'Totd', 'Weekly':
            table_name = f'Warrior{table_table}'

            maps = {}
            for entry in db.execute(f'SELECT * FROM {table_name}').fetchall():
                map = dict(entry)
                maps[map['mapUid']] = map

            uids = list(maps)
            while len(uids):
                print(f'{table_name} has {len(uids)} maps left')

                uid_count = min(len(uids), MAX_UIDS)
                uids_this_req = uids[:uid_count]
                uids = uids[uid_count:]
                endpoint = f'maps/?mapUidList={','.join(uids_this_req)}'

                time.sleep(0.5)
                req = core.get(token, endpoint)
                for map in req:
                    existing = maps[map['mapUid']]
                    existing['mapId'] = map['mapId']

            db.execute(f'ALTER TABLE {table_name} ADD mapId CHAR(36);')
            for uid, map in maps.items():
                db.execute(f'UPDATE {table_name} SET mapId = "{map['mapId']}" WHERE mapUid = "{map['mapUid']}"')


def display_db_epoch_vals() -> None:
    table = read_table('KeyVals')

    stage2 = []
    for i, _ in enumerate(table):
        stage2.append((table[i]['key'], int(table[i]['val'])))

    stage3 = sorted(stage2, key=lambda pair: pair[1])

    for key, val in stage3:
        diff = val - stamp()
        print(
            f'{key:<16}',
            f'{dt.fromtimestamp(int(val), timezone.utc).strftime('%Y-%m-%d %H:%M:%Sz')}',
            f'({'in ' if diff > 0 else ''}{format_long_time(abs(diff))}{' ago' if diff <= 0 else ''})'
        )


def get_tops_for_club_campaign(tokens: dict, club_id: int, campaign_id: int, factor: float = 0.5) -> list:
    print(f'getting maps for club {club_id}, campaign {campaign_id}')

    time.sleep(0.5)
    req = live.get(
        tokens['live'],
        f'api/token/club/{club_id}/campaign/{campaign_id}'
    )

    club_name = req['clubName']
    campaign = req['campaign']
    campaign_name = campaign['name']
    uids = []

    for entry in campaign['playlist']:
        uids.append(entry['mapUid'])

    print(f'getting info for club {club_id}, campaign {campaign_id}')

    time.sleep(0.5)
    info = live.get(
        tokens['live'],
        f'api/token/map/get-multiple?mapUidList={'%2C'.join(uids)}'
    )

    maps = []

    for entry in info['mapList']:
        maps.append({
            'at': entry['authorTime'],
            'campaign_id': campaign_id,
            'campaign_name': campaign_name,
            'club_id': club_id,
            'club_name': club_name,
            'gt': entry['goldTime'],
            'id': entry['mapId'],
            'name': entry['name'],
            'uid': entry['uid']
        })

    for map in maps:
        uid = map['uid']

        print(f'getting top for map {uid}')

        time.sleep(0.5)
        top = live.get(
            tokens['live'],
            f'api/token/leaderboard/group/Personal_Best/map/{uid}/top'
        )

        map['wr'] = top['tops'][0]['top'][0]['score']
        map['wm'] = calc_warrior_time(map['at'], map['wr'], factor)

    return maps


def process_u10s() -> None:
    def load_csv() -> dict:
        data = []

        with open('data/u10s_2.csv') as f:
            for i, line in enumerate(csv.reader(f)):
                if not i:
                    continue

                data.append(line)

        return data

    club_id = 18974
    club_name = 'Everios96'

    maps = load_csv()

    with Cursor(FILE_DB) as db:
        for map in maps:
            db.execute(f'''
                INSERT INTO WarriorOther (
                    name,
                    mapUid,
                    mapId,
                    campaignName,
                    campaignId,
                    authorTime,
                    warriorTime,
                    worldRecord,
                    clubId,
                    clubName
                ) VALUES (
                    "{map[0]}",
                    "{map[1]}",
                    "{map[2]}",
                    "{map[3]}",
                    {int(map[4])},
                    {int(map[5])},
                    {int(map[6])},
                    {int(map[7])},
                    {club_id},
                    "{club_name}"
                )
            ''')

    pass


def test_club_campaign_error() -> None:
    tokens = get_tokens()

    req = live.get(
        tokens['live'],
        'api/token/club/17893/campaign/3348'
    )

    pass


def test_secret_times() -> None:
    token = get_token_oauth()
    req = post(
        'https://trackmania.com/tracks/ZZeF_oCW5MvMrMhJ2dYMirxOc60',
        f'top_secret%5BthresholdScore%5D=29872&top_secret%5B_token%5D={token.access_token}'
    )

    pass


def test_unicode_encode_error() -> None:
    s = 'Ma\u0142opolskie'
    with open('locals.txt', 'a', newline='\n') as f:
        f.write(f'{s.encode('unicode-escape').decode('ascii')}\n')

    log(s)
    # with open('locals.txt', 'ab') as f:
    #     f.write(s.encode())


def warriors_to_github() -> None:
    warriors_to_json()
    to_github()


if __name__ == '__main__':
    # display_db_epoch_vals()
    # test_unicode_encode_error()
    # test_club_campaign_error()
    # print(webhook_seasonal(None))
    print(calc_warrior_time(18518, 14811, 0.5))
    # process_u10s()
    # add_club_campaign_warriors(9, 35357)  # openplanet school
    # add_map_ids_to_warriors()
    # warriors_to_github()
    # tables_to_json()
    # add_gold_times_to_warriors()
    # add_campaign_ids_and_weeks_to_weekly_warriors()
    # test_secret_times()
    # for campaign_id in [77195, 78234, 84886, 91855, 97842]:
    #     add_club_campaign_warriors(65094, campaign_id)

    pass

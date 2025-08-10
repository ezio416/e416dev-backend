# c 2025-01-27
# m 2025-08-09

import csv

from nadeo_api import auth, config, live

import api
from constants import *
import files
import github
import utils


def add_club_campaign_warriors(club_id: int, campaign_id: int, factor: float = 0.5) -> None:
    # tokens = get_tokens()
    tokens: dict[str, auth.Token] = {'live': api.get_token_live()}
    maps: list = get_tops_for_club_campaign(tokens, club_id, campaign_id, factor)

    with files.Cursor(FILE_DB) as db:
        for i, map in enumerate(maps):
            uid: str = map['uid']

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


def get_tops_for_club_campaign(tokens: dict, club_id: int, campaign_id: int, factor: float = 0.5) -> list:
    print(f'getting maps for club {club_id}, campaign {campaign_id}')

    req: dict = live.get_club_campaign(tokens['live'], club_id, campaign_id)

    club_name: str = req['clubName']
    campaign: dict = req['campaign']
    campaign_name: str = campaign['name']
    uids: list = []

    for entry in campaign['playlist']:
        uids.append(entry['mapUid'])

    print(f'getting info for club {club_id}, campaign {campaign_id}')

    info: dict = live.get(
        tokens['live'],
        f'api/token/map/get-multiple?mapUidList={'%2C'.join(uids)}'
    )

    maps: list = []

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
        uid: str = map['uid']

        print(f'getting top for map {uid}')

        top: dict = live.get_map_leaderboard(tokens['live'], uid)

        map['wr'] = top['tops'][0]['top'][0]['score']
        map['wm'] = utils.calc_warrior_time(map['at'], map['wr'], factor)

    return maps


def process_u10s() -> None:
    def load_csv() -> dict:
        data: list = []

        with open('data/u10s_2.csv') as f:
            for i, line in enumerate(csv.reader(f)):
                if not i:
                    continue

                data.append(line)

        return data

    club_id = 18974
    club_name = 'Everios96'

    maps: dict = load_csv()

    with files.Cursor(FILE_DB) as db:
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


def rewrite_timestamps() -> None:
    for ts in files.read_table('Timestamps'):
        files.write_timestamp(ts['key'], ts['ts'])


def warriors_to_github() -> None:
    files.warriors_to_json()
    github.send_warrior()


def main() -> None:
    # print(utils.calc_warrior_time(18518, 14811, 0.5))
    # process_u10s()
    # add_club_campaign_warriors(9, 35357)  # openplanet school
    # warriors_to_github()
    # for campaign_id in [77195, 78234, 84886, 91855, 97842]:
    #     add_club_campaign_warriors(65094, campaign_id)

    config.debug_logging = True
    config.wait_between_requests_ms = 500

    # token = api.get_token_core()
    # req = core.get_zones(token)
    # req = core.get_zones(token)
    # req = core.get_zones(token)

    # github.send_regular()
    # github.send_warrior()

    # rewrite_timestamps()

    pass


if __name__ == '__main__':
    main()

# c 2025-01-27
# m 2025-11-11

import csv

from nadeo_api import auth, config, live

import api
from constants import *
import files
import github
import utils


def process_icy_f25() -> None:
    def load_csv() -> list:
        data: list = []

        with open('data/icy_f25.csv') as f:
            for i, line in enumerate(csv.reader(f)):
                if not i:
                    continue

                data.append(line)

        return data

    maps: dict = {}

    for map in load_csv():
        uid: str = map[0]
        maps[uid] = {}
        maps[uid]['wt'] = int(map[1])

    uids: list[str] = list(maps)

    import nadeo_api
    nadeo_api.config.debug_logging = True

    token: auth.Token = get_token_core()
    info: list[dict] = core.get_map_info(token, uids)

    for map in info:
        uid: str = map['mapUid']
        maps[uid]['at']   = map['authorScore']
        maps[uid]['gt']   = map['goldScore']
        maps[uid]['id']   = map['mapId']
        maps[uid]['name'] = map['name']

    club_id:       int = 84969
    club_name:     str = 'Icy Campaign'
    campaign_id:   int =  112251
    campaign_name: str = 'Icy Fall 2025'

    print('writing db')

    with Cursor(FILE_DB) as db:
        for uid, map in maps.items():
            db.execute(f'''
                INSERT INTO WarriorOther (
                    authorTime,
                    goldTime,
                    mapId,
                    mapUid,
                    campaignId,
                    campaignName,
                    clubId,
                    clubName,
                    name,
                    warriorTime
                ) VALUES (
                    {map['at']},
                    {map['gt']},
                    "{map['id']}",
                    "{uid}",
                    {campaign_id},
                    "{campaign_name}",
                    {club_id},
                    "{club_name}",
                    "{map['name']}",
                    {map['wt']}
                )
            ''')

    ...


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
    config.debug_logging = True
    config.wait_between_requests_ms = 500

    # print(utils.calc_warrior_time(19294, 8272, 0.5))
    # process_u10s()
    # add_club_campaign_warriors(9, 35357)  # openplanet school
    # warriors_to_github()
    # for campaign_id in [77195, 78234, 84886, 91855, 97842]:
    #     add_club_campaign_warriors(65094, campaign_id)

    # token = api.get_token_core()
    # req = core.get_zones(token)
    # req = core.get_zones(token)
    # req = core.get_zones(token)

    # github.send_regular()
    # github.send_warrior()

    # rewrite_timestamps()

    # req = live.get_map_leaderboard(api.get_token_live(), 'F6B8jSu7umawah4kA5fssf8ro7d', length=20)  # please cheat this map

    # api.add_warriors_club_campaign(api.get_tokens(), 65094, 104293)  # microk 6
    # warriors_to_github()

    pass


if __name__ == '__main__':
    main()

# c 2025-01-27
# m 2025-11-11

import csv

from nadeo_api import auth, config, live

import api
from constants import *
import files
import github
import utils


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

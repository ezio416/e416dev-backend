# c 2025-01-27
# m 2025-02-20

import json
import os
import sqlite3 as sql


CAMPAIGN_SERIES:   tuple[str] = 'FFFFFF', '66FF66', '6666FF', 'FF4444', '666666'
DISCORD_WAIT_TIME: float      = 1.0
COLOR_WARRIOR:     str        = '33CCFF'
MEDAL_AUTHOR:      str        = '<:MedalAuthor:736600847219294281>'
MEDAL_BRONZE:      str        = '<:MedalBronze:736600847630336060>'
MEDAL_GOLD:        str        = '<:MedalGold:736600847588261988>'
MEDAL_SILVER:      str        = '<:MedalSilver:736600847454175363>'
MEDAL_WARRIOR:     str        = '<:MedalWarrior:1305798298690392155>'
WAIT_TIME:         float      = 0.5

DIR_PARENT:        str = f'{os.path.dirname(__file__).replace('\\', '/')}/..'
DIR_DATA:          str = f'{DIR_PARENT}/data'
FILE_DB:           str = f'{DIR_DATA}/tm.db'
FILE_LOG:          str = f'{DIR_DATA}/tm.log'
FILE_ROYAL:        str = f'{DIR_DATA}/royal.json'
FILE_ROYAL_RAW:    str = f'{DIR_DATA}/royal_raw.json'
FILE_SEASONAL:     str = f'{DIR_DATA}/seasonal.json'
FILE_SEASONAL_RAW: str = f'{DIR_DATA}/seasonal_raw.json'
FILE_TOTD:         str = f'{DIR_DATA}/totd.json'
FILE_TOTD_RAW:     str = f'{DIR_DATA}/totd_raw.json'
FILE_WARRIOR:      str = f'{DIR_DATA}/warrior.json'
FILE_WARRIOR_OLD:  str = f'{DIR_DATA}/warrior_old.json'
FILE_WEEKLY:       str = f'{DIR_DATA}/weekly.json'
FILE_WEEKLY_RAW:   str = f'{DIR_DATA}/weekly_raw.json'
FILE_ZONE:         str = f'{DIR_DATA}/zone.json'
FILE_ZONE_RAW:     str = f'{DIR_DATA}/zone_raw.json'

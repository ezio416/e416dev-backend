# c 2025-01-27
# m 2026-02-04

import os


MAX_TIMESTAMP:     int = 2_000_000_000
SECONDS_IN_MINUTE: int = 60
SECONDS_IN_HOUR:   int = 3_600
SECONDS_IN_DAY:    int = 86_400
SECONDS_IN_WEEK:   int = 604_800

CAMPAIGN_SERIES:   tuple[str] = 'FFFFFF', '66FF66', '6666FF', 'FF4444', '666666'
COLOR_WARRIOR:     str        = '3388CC'
DISCORD_USER_ROLE: str        = '<@&1205257336252534814>'
DISCORD_WAIT_TIME: float      = 1.0
MEDAL_AUTHOR:      str        = '<:MedalAuthor:736600847219294281>'
MEDAL_BRONZE:      str        = '<:MedalBronze:736600847630336060>'
MEDAL_GOLD:        str        = '<:MedalGold:736600847588261988>'
MEDAL_SILVER:      str        = '<:MedalSilver:736600847454175363>'
MEDAL_WARRIOR:     str        = '<:MedalWarrior:1305798298690392155>'

DIR_PARENT:        str = f'{os.path.dirname(__file__).replace('\\', '/')}/..'
DIR_DATA:          str = f'{DIR_PARENT}/data'
FILE_DB:           str = f'{DIR_DATA}/tm.db'
FILE_GRAND:        str = f'{DIR_DATA}/grand.json'
FILE_GRAND_RAW:    str = f'{DIR_DATA}/grand_raw.json'
FILE_INDICES:      str = f'{DIR_DATA}/indices.json'
FILE_LOG:          str = f'{DIR_DATA}/tm.log'
FILE_SEASONAL:     str = f'{DIR_DATA}/seasonal.json'
FILE_SEASONAL_RAW: str = f'{DIR_DATA}/seasonal_raw.json'
FILE_TOTD:         str = f'{DIR_DATA}/totd.json'
FILE_TOTD_RAW:     str = f'{DIR_DATA}/totd_raw.json'
FILE_WARRIOR:      str = f'{DIR_DATA}/warrior.json'
FILE_WEEKLY:       str = f'{DIR_DATA}/weekly.json'
FILE_WEEKLY_RAW:   str = f'{DIR_DATA}/weekly_raw.json'
FILE_ZONE:         str = f'{DIR_DATA}/zone.json'
FILE_ZONE_RAW:     str = f'{DIR_DATA}/zone_raw.json'

TMX_BASE_URL:      str = 'https://trackmania.exchange'

# c 2025-01-27
# m 2025-01-27

import os


CAMPAIGN_SERIES: tuple[str] = 'FFFFFF', '66FF66', '6666FF', 'FF4444', '666666'
WAIT_TIME:       float      = 0.5

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
FILE_WEEKLY:       str = f'{DIR_DATA}/weekly.json'
FILE_WEEKLY_RAW:   str = f'{DIR_DATA}/weekly_raw.json'
FILE_ZONE:         str = f'{DIR_DATA}/zone.json'
FILE_ZONE_RAW:     str = f'{DIR_DATA}/zone_raw.json'

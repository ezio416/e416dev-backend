# c 2025-02-16
# m 2025-07-26

from flask import Flask, request, Response

from files import Cursor
import re
import time
from utils import *
import uuid


provider = Flask(__name__)


# @provider.route('/tm/map-review')
# @provider.route('/tm/map-review/')
# def tm_map_review():
#     with Cursor(FILE_DB) as db:
#         maps = [dict(map) for map in db.execute(f'SELECT * FROM MapReview').fetchall()]

#     ret = {
#         't': {
#             '1d': 0,
#             '7d': 0,
#             '30d': 0
#         },
#         'w': {
#             '1d': [0,0,0,0,0],
#             '7d': [0,0,0,0,0],
#             '30d': [0,0,0,0,0]
#         }
#     }

#     now = int(time.time())

#     for map in maps:
#         recency = now - map['timestamp']

#         if map['type'] == 'Totd':
#             if recency < 86_400:
#                 ret['t']['1d'] += 1
#             if recency < 604_800:
#                 ret['t']['7d'] += 1
#             if recency < 2_592_000:
#                 ret['t']['30d'] += 1

#         elif map['type'] == 'Weekly':
#             number = int(map['number'])
#             if number and map['authorTime'] < 22000:
#                 if recency < 86_400:
#                     ret['w']['1d'][number - 1] += 1
#                 if recency < 604_800:
#                     ret['w']['7d'][number - 1] += 1
#                 if recency < 2_592_000:
#                     ret['w']['30d'][number - 1] += 1

#     return ret


# @provider.route('/tm/map-review/add', methods=['POST'])
# @provider.route('/tm/map-review/add/', methods=['POST'])
# def tm_map_review_add():
#     received = request.get_json()

#     try:
#         map_name = str(received['mapName'])
#         review_type = str(received['reviewType'])

#         with Cursor(FILE_DB) as db:
#             number = 0
#             if all((
#                 review_type == 'Weekly',
#                 match := re.match(r'^([12345]) *[-‒–—᠆‐‑⁃﹣－] *.+', map_name)
#             )):
#                 number = int(match.group(1))

#             db.execute(f'''
#                 REPLACE INTO MapReview (
#                     authorTime,
#                     mapName,
#                     mapUid,
#                     number,
#                     timestamp,
#                     type
#                 ) VALUES (
#                     {int(received['authorTime'])},
#                     "{map_name}",
#                     "{received['mapUid']}",
#                     {number},
#                     {int(time.time())},
#                     "{review_type}"
#                 );
#             ''')

#     except Exception as e:
#         print(e)
#         return {'success': False}

#     return {'success': True}


# @provider.route('/tm/map-review/auth/create', methods=['POST'])
# @provider.route('/tm/map-review/auth/create/', methods=['POST'])
# def tm_map_review_auth_create():
#     token = str(uuid.uuid4())
#     expiry = int(time.time()) + 86400

#     with Cursor(FILE_DB) as db:
#         db.execute(f'INSERT INTO MapReviewTokens (token, expiry) VALUES ("{token}", {expiry});')

#     return {'token': token, 'expiry': expiry}


# @provider.route('/tm/map-review/auth/verify')
# @provider.route('/tm/map-review/auth/verify/')
# def tm_map_review_auth_verify():
#     if token := request.args.get('token', None, str):
#         with Cursor(FILE_DB) as db:
#             try:
#                 row = dict(db.execute(f'SELECT * FROM MapReviewTokens WHERE token="{token}";').fetchone())
#                 # print(f'row: {row}')
#                 valid = row['expiry'] > int(time.time()) - 86400
#                 # print(f'valid: {valid}')
#                 return {'valid': valid}
#             except Exception:
#                 # print('exception')
#                 return {'valid': False}

#     return {'valid': False}


@provider.route('/tm/calc_warrior_time')
@provider.route('/tm/calc_warrior_time/')
def tm_calc_warrior_time():
    at = request.args.get('at', None, int)
    wr = request.args.get('wr', None, int)
    factor = request.args.get('factor', None, float)

    if all((at, wr, factor)):
        return [calc_warrior_time(at, wr, factor)]

    return [0]


@provider.route('/tm/get_warrior_time')
@provider.route('/tm/get_warrior_time/')
def tm_get_warrior_time():
    uid = request.args.get('uid', None, str)

    if uid and len(uid) in (26, 27):
        with Cursor(FILE_DB) as db:
            for table in ('Totd', 'Weekly', 'Seasonal', 'Other'):  # check largest tables first
                try:
                    ret = dict(db.execute(f'SELECT * FROM Warrior{table} WHERE mapUid = "{uid}"').fetchone())
                    ret['type'] = table
                    return ret

                except TypeError:
                    pass

                except Exception:
                    return Response(status=500)

    return {}


if __name__ == '__main__':
    provider.run('127.0.0.1', 4161, True)

# c 2025-02-16
# m 2025-07-25

from flask import Flask, request, Response

from files import Cursor
import re
import time
from utils import *
import uuid


provider = Flask(__name__)


@provider.route('/tm/map-review/add', methods=['POST'])
@provider.route('/tm/map-review/add/', methods=['POST'])
def tm_map_review_add():
    received = request.get_json()

    try:
        name = str(received['mapName'])
        type = str(received['reviewType'])

        with Cursor(FILE_DB) as db:
            number = 0
            if all((
                type == 'Weekly',
                match := re.match(r'^([12345]) *[-‒–—᠆‐‑⁃﹣－] *.+', name)
            )):
                number = int(match.group(1))

            db.execute(f'''
                REPLACE INTO MapReview (
                    authorTime,
                    mapName,
                    mapUid,
                    number,
                    timestamp,
                    type
                ) VALUES (
                    {int(received['authorTime'])},
                    "{name}",
                    "{received['mapUid']}",
                    {number},
                    {int(time.time())},
                    "{type}"
                );
            ''')

    except Exception as e:
        print(e)
        return {'success': False}

    return {'success': True}


@provider.route('/tm/map-review/auth/create', methods=['POST'])
@provider.route('/tm/map-review/auth/create/', methods=['POST'])
def tm_map_review_auth_create():
    token = str(uuid.uuid4())
    expiry = int(time.time()) + 86400

    with Cursor(FILE_DB) as db:
        db.execute(f'INSERT INTO MapReviewTokens (token, expiry) VALUES ("{token}", {expiry});')

    return {'token': token, 'expiry': expiry}


@provider.route('/tm/map-review/auth/verify')
@provider.route('/tm/map-review/auth/verify/')
def tm_map_review_auth_verify():
    if token := request.args.get('token', None, str):
        with Cursor(FILE_DB) as db:
            try:
                row = dict(db.execute(f'SELECT * FROM MapReviewTokens WHERE token="{token}";').fetchone())
                # print(f'row: {row}')
                valid = row['expiry'] > int(time.time()) - 86400
                # print(f'valid: {valid}')
                return {'valid': valid}
            except Exception:
                # print('exception')
                return {'valid': False}

    return {'valid': False}


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

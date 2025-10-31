# c 2025-02-16
# m 2025-10-30

import datetime as dt
import time
import uuid

import flask

import api
from constants import *
import files
import github
import utils


OK                = 200
NO_CONTENT        = 204
BAD_REQUEST       = 400
UNAUTHORIZED      = 401
FORBIDDEN         = 403
UPGRADE_REQUIRED  = 426
TOO_MANY_REQUESTS = 429
INTERNAL_SERVER   = 500

backend = flask.Flask(__name__)


@backend.route('/tm/warrior')
@backend.route('/tm/warrior/')
def tm_warrior() -> flask.Response:
    uid: None | str = flask.request.args.get('uid', None, str)

    if uid and 24 <= len(uid) <= 27:
        with files.Cursor(FILE_DB) as db:
            for table in ('Totd', 'Weekly', 'Seasonal', 'Other'):  # check largest tables first
                try:
                    ret: dict = dict(db.execute(f'SELECT * FROM Warrior{table} WHERE mapUid = "{uid}"').fetchone())
                    ret['type'] = table
                    return ret

                except TypeError:
                    pass

                except Exception:
                    return '', INTERNAL_SERVER

    return {}


@backend.route('/tm/warrior/add_club_campaign', methods=['POST'])
@backend.route('/tm/warrior/add_club_campaign/', methods=['POST'])
def tm_warrior_add_club_campaign() -> flask.Response:
    club_id: int = flask.request.args.get('club_id', 0, int)
    campaign_id: int = flask.request.args.get('campaign_id', 0, int)

    if not club_id:
        return 'missing/invalid parameter "club_id"', BAD_REQUEST

    if not campaign_id:
        return 'missing/invalid parameter "campaign_id"', BAD_REQUEST

    tokens: dict = api.get_tokens()
    if not api.add_warriors_club_campaign(tokens, club_id, campaign_id):
        return 'adding failed', INTERNAL_SERVER

    files.warriors_to_json()
    if not github.send_warrior():
        return 'sending to github failed', INTERNAL_SERVER

    return '', OK


@backend.route('/tm/warrior/auth', methods=['GET', 'POST'])
@backend.route('/tm/warrior/auth/', methods=['GET', 'POST'])
def tm_warrior_auth() -> flask.Response:
    '''
    get w/ token      -> only token check
    get w/ account id -> only ban check
    post              -> new token
    '''

    id: str = flask.request.args.get('accountId', '', str)

    if flask.request.method == 'POST':
        if not id:
            return 'account ID missing', BAD_REQUEST

        token = str(uuid.uuid4())
        expiry = int(time.time()) + 86400
        expiry_utc: str = dt.datetime.fromtimestamp(expiry, dt.timezone.utc).strftime('%F %T')
        # print(f'generated token {token}, expires at {expiry_utc}Z')

        with files.Cursor(FILE_DB) as db:
            db.execute(f'INSERT INTO WarriorTokens (accountId, expiry, expiryUtc, token) VALUES ("{id}", {expiry}, "{expiry_utc}", "{token}");')

        return {'accountId': id, 'expiry': expiry, 'token': token}

    if id:
        with files.Cursor(FILE_DB) as db:
            if db.execute(f'SELECT * FROM WarriorBanned WHERE accountId="{id}";').fetchone():
                return 'banned', FORBIDDEN
            return '', NO_CONTENT

    token: str = flask.request.args.get('token', '', str)
    if not token:
        return 'token missing', BAD_REQUEST

    with files.Cursor(FILE_DB) as db:
        try:
            row = dict(db.execute(f'SELECT * FROM WarriorTokens WHERE token="{token}";').fetchone())
            if not row:
                return 'token invalid', UNAUTHORIZED
            if row['expiry'] > int(time.time()):
                return {'accountId': row['accountId'], 'expiry': row['expiry'], 'token': token}

        except Exception as e:
            print(f'exception: {e}')
            return '', INTERNAL_SERVER


@backend.route('/tm/warrior/calc')
@backend.route('/tm/warrior/calc/')
def tm_warrior_calc() -> flask.Response:
    at: None | int = flask.request.args.get('at', None, int)
    wr: None | int = flask.request.args.get('wr', None, int)
    factor: None | float = flask.request.args.get('factor', None, float)

    if all((at, wr, factor)):
        return [utils.calc_warrior_time(at, wr, factor)]

    return [0]


@backend.route('/tm/warrior/next')
@backend.route('/tm/warrior/next/')
def tm_warrior_next() -> flask.Response:
    return [files.get_next_warrior()]


if __name__ == '__main__':
    backend.run('127.0.0.1', 4161, True)

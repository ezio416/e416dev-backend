# c 2025-02-16
# m 2025-10-27

import flask

import api
from constants import *
import files
import github
import utils


backend = flask.Flask(__name__)


@backend.route('/tm/warrior')
@backend.route('/tm/warrior/')
def tm_warrior():
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
                    return flask.Response(status=500)

    return {}


@backend.route('/tm/warrior/add_club_campaign', methods=['POST'])
@backend.route('/tm/warrior/add_club_campaign/', methods=['POST'])
def tm_warrior_add_club_campaign() -> flask.Response:
    club_id: int = flask.request.args.get('club_id', 0, int)
    campaign_id: int = flask.request.args.get('campaign_id', 0, int)

    if not club_id:
        return 'missing/invalid parameter "club_id"', 400

    if not campaign_id:
        return 'missing/invalid parameter "campaign_id"', 400

    tokens: dict = api.get_tokens()
    if not api.add_warriors_club_campaign(tokens, club_id, campaign_id):
        return 'adding failed', 500

    files.warriors_to_json()
    if not github.send_warrior():
        return 'sending to github failed', 500

    return flask.Response(status=200)


@backend.route('/tm/warrior/calc')
@backend.route('/tm/warrior/calc/')
    at: None | int = flask.request.args.get('at', None, int)
    wr: None | int = flask.request.args.get('wr', None, int)
    factor: None | float = flask.request.args.get('factor', None, float)

    if all((at, wr, factor)):
        return [utils.calc_warrior_time(at, wr, factor)]

    return [0]


@backend.route('/tm/warrior/next')
@backend.route('/tm/warrior/next/')
def tm_warrior_next() -> list[int]:
    return [files.get_next_warrior()]


if __name__ == '__main__':
    backend.run('127.0.0.1', 4161, True)

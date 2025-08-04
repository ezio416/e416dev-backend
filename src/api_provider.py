# c 2025-02-16
# m 2025-08-04

import flask

from constants import *
import files
import utils


provider = flask.Flask(__name__)


@provider.route('/tm/calc_warrior_time')
@provider.route('/tm/calc_warrior_time/')
def tm_calc_warrior_time():
    at = flask.request.args.get('at', None, int)
    wr = flask.request.args.get('wr', None, int)
    factor = flask.request.args.get('factor', None, float)

    if all((at, wr, factor)):
        return [utils.calc_warrior_time(at, wr, factor)]

    return [0]


@provider.route('/tm/get_warrior_time')
@provider.route('/tm/get_warrior_time/')
def tm_get_warrior_time():
    uid = flask.request.args.get('uid', None, str)

    if uid and 24 <= len(uid) <= 27:
        with files.Cursor(FILE_DB) as db:
            for table in ('Totd', 'Weekly', 'Seasonal', 'Other'):  # check largest tables first
                try:
                    ret = dict(db.execute(f'SELECT * FROM Warrior{table} WHERE mapUid = "{uid}"').fetchone())
                    ret['type'] = table
                    return ret

                except TypeError:
                    pass

                except Exception:
                    return flask.Response(status=500)

    return {}


if __name__ == '__main__':
    provider.run('127.0.0.1', 4161, True)

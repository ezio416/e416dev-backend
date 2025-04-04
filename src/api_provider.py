# c 2025-02-16
# m 2025-02-23

from flask import Flask, request, Response

from files import Cursor
from utils import *


provider = Flask(__name__)


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

# c 2025-02-16
# m 2025-02-17

from flask import Flask, request

from files import Cursor
from utils import *


app = Flask(__name__)


@app.route('/tm/calc_warrior_time/')
def tm_calc_warrior_time():
    at = request.args.get('at', None, int)
    wr = request.args.get('wr', None, int)
    factor = request.args.get('factor', None, float)

    if all((at, wr, factor)):
        return [calc_warrior_time(at, wr, factor)]

    return [0]


@app.route('/tm/get_warrior_time/')
def tm_get_warrior_time():
    uid = request.args.get('uid', None, str)

    if uid and 26 <= len(uid) <= 27:
        with Cursor(FILE_DB) as db:
            for table in ('Totd', 'Weekly', 'Seasonal', 'Other'):  # check largest tables first
                try:
                    ret = dict(db.execute(f'SELECT * FROM Warrior{table} WHERE mapUid = "{uid}"').fetchone())
                    ret['type'] = table
                    return ret
                except TypeError:
                    pass

    return {}


if __name__ == '__main__':
    app.run('0.0.0.0', 4161, True)

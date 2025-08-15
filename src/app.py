# c 2024-12-26
# m 2025-08-15

import multiprocessing
import os
import time

from nadeo_api import auth
import nadeo_api.config

import api
import api_provider
from constants import *
import errors
import files
import github
import schedules
import utils
import webhooks


def backend() -> None:
    tokens: dict[str, auth.Token] = api.get_tokens()

    nadeo_api.config.wait_between_requests_ms = 500

    while True:
        time.sleep(1)
        now: int = utils.stamp()
        utils.log('loop', log_file=False)

        while not os.path.isfile(FILE_DB):
            utils.log('db file not found')
            time.sleep(1)

        try:
            for audience, token in tokens.items():  # bandaid
                if audience != 'oauth' and now + utils.minutes_to_seconds(15) > token.expiration:
                    utils.log(f'warn: {audience} token is 15 minutes to expiry, refreshing...')
                    token.refresh()

            if any((
                schedules.schedule(tokens, 'seasonal', schedules.seasonal, webhooks.seasonal),
                schedules.schedule(tokens, 'totd',     schedules.totd,     webhooks.totd),
                schedules.schedule(tokens, 'weekly',   schedules.weekly,   webhooks.weekly),
                schedules.schedule(tokens, 'zone',     schedules.zone,     None)
            )):
                files.tables_to_json()
                github.send_regular()

            if any((
                schedules.schedule(tokens, 'seasonal', schedules.seasonal_warriors, webhooks.seasonal_warriors, True),
                schedules.schedule(tokens, 'totd',     schedules.totd_warrior,      webhooks.totd_warrior,      True),
                schedules.schedule(tokens, 'weekly',   schedules.weekly_warriors,   webhooks.weekly_warriors,   True),
            )):
                files.warriors_to_json()
                github.send_warrior()

        except Exception as e:
            errors.error(e)


if __name__ == '__main__':
    multiprocessing.Process(target=backend).start()
    api_provider.provider.run('0.0.0.0', 4161)

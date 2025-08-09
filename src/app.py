# c 2024-12-26
# m 2025-08-09

import multiprocessing
import time

import nadeo_api.config

import api
import api_provider
import files
import github
import schedules
import utils
import webhooks


def backend() -> None:
    tokens: dict = api.get_tokens()

    nadeo_api.config.wait_between_requests_ms = 500

    while True:
        time.sleep(1)
        now: int = utils.stamp()
        utils.log('loop', log_file=False)

        for audience, token in tokens.items():  # bandaid
            if audience != 'oauth' and now + utils.minutes_to_seconds(15) > token.expiration:
                utils.log(f'warn: {audience} token is 15 minutes to expiry, refreshing...')
                token.refresh()

        if any((
            schedules.schedule(tokens, 'seasonal', schedules.seasonal, webhooks.seasonal),
            schedules.schedule(tokens, 'totd',     schedules.totd,     webhooks.totd),
            schedules.schedule(tokens, 'weekly',   schedules.weekly,   webhooks.weekly)
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


if __name__ == '__main__':
    multiprocessing.Process(target=backend).start()
    api_provider.provider.run('0.0.0.0', 4161)

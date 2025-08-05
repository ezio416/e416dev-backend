# c 2024-12-26
# m 2025-08-05

import multiprocessing
import time

import nadeo_api

import api
import api_provider
import files
import github
import schedules
import utils
import webhooks


def backend() -> None:
    tokens: dict = api.get_tokens()

    nadeo_api.wait_between_requests_ms = 500

    while True:
        time.sleep(1)
        ts: int = utils.stamp()
        utils.log('loop', log_file=False)

        for audience, token in tokens.items():  # bandaid
            if audience != 'oauth' and ts + utils.minutes_to_seconds(15) > token.expiration:
                utils.log(f'{audience} token is 15 minutes to expiry')
                token.refresh()

        if any((
            schedules.schedule(tokens, 'next_seasonal', schedules.seasonal, 'Seasonal', webhooks.seasonal),
            schedules.schedule(tokens, 'next_totd',     schedules.totd,     'Totd',     webhooks.totd),
            schedules.schedule(tokens, 'next_weekly',   schedules.weekly,   'Weekly',   webhooks.weekly)
        )):
            files.tables_to_json()
            github.send()

        if any((
            schedules.schedule_warriors(tokens, 'warrior_seasonal', schedules.seasonal_warriors, webhooks.seasonal_warriors),
            schedules.schedule_warriors(tokens, 'warrior_totd',     schedules.totd_warrior,      webhooks.totd_warrior),
            schedules.schedule_warriors(tokens, 'warrior_weekly',   schedules.weekly_warriors,   webhooks.weekly_warriors),
        )):
            files.warriors_to_json()
            github.send()


if __name__ == '__main__':
    multiprocessing.Process(target=backend).start()
    api_provider.provider.run('0.0.0.0', 4161)

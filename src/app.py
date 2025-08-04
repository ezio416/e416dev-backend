# c 2024-12-26
# m 2025-08-04

import multiprocessing
import time

import api
import api_provider
import files
import github
import schedules
import utils
import webhooks


def backend() -> None:
    tokens = api.get_tokens()

    while True:
        time.sleep(1)
        ts = utils.stamp()
        utils.log('loop', log_file=False)

        for audience, token in tokens.items():  # bandaid
            if audience != 'oauth' and ts + utils.minutes_to_seconds(15) > token.expiration:
                utils.log(f'{audience} token is 15 minutes to expiry')
                token.refresh()

        if any((
            schedules.schedule(tokens, 'next_seasonal', schedules.schedule_seasonal_maps, 'Seasonal', webhooks.webhook_seasonal),
            schedules.schedule(tokens, 'next_totd',     schedules.schedule_totd_maps,     'Totd',     webhooks.webhook_totd),
            schedules.schedule(tokens, 'next_weekly',   schedules.schedule_weekly_maps,   'Weekly',   webhooks.webhook_weekly)
        )):
            files.tables_to_json()
            github.to_github()

        if any((
            schedules.schedule_warriors(tokens, 'warrior_seasonal', schedules.schedule_seasonal_warriors, webhooks.webhook_seasonal_warriors),
            schedules.schedule_warriors(tokens, 'warrior_totd',     schedules.schedule_totd_warrior,      webhooks.webhook_totd_warrior),
            schedules.schedule_warriors(tokens, 'warrior_weekly',   schedules.schedule_weekly_warriors,   webhooks.webhook_weekly_warriors),
        )):
            files.warriors_to_json()
            github.to_github()


if __name__ == '__main__':
    multiprocessing.Process(target=backend).start()
    api_provider.provider.run('0.0.0.0', 4161)

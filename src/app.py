# c 2024-12-26
# m 2024-03-14

from multiprocessing import Process

from api import get_tokens
from api_provider import provider
from files import tables_to_json, warriors_to_json
from github import *
from schedules import *
from webhooks import *


def backend() -> None:
    tokens = get_tokens()

    while True:
        time.sleep(1)
        ts = stamp()
        log('loop', log_file=False)

        if any((
            schedule(tokens, 'next_seasonal', ts, schedule_seasonal_maps, 'Seasonal', webhook_seasonal),
            schedule(tokens, 'next_totd',     ts, schedule_totd_maps,     'Totd',     webhook_totd),
            schedule(tokens, 'next_weekly',   ts, schedule_weekly_maps,   'Weekly',   webhook_weekly),
            # schedule(tokens, 'next_royal',    ts, schedule_royal_maps,    'Royal',    webhook_royal),
        )):
            tables_to_json()
            to_github()

        if any((
            schedule_warriors(tokens, 'warrior_seasonal', ts, schedule_seasonal_warriors, webhook_seasonal_warriors),
            schedule_warriors(tokens, 'warrior_totd',     ts, schedule_totd_warrior,      webhook_totd_warrior),
            schedule_warriors(tokens, 'warrior_weekly',   ts, schedule_weekly_warriors,   webhook_weekly_warriors),
        )):
            warriors_to_json()
            to_github()


if __name__ == '__main__':
    Process(target=backend).start()
    provider.run('0.0.0.0', 4161)

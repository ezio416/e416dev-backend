# c 2025-01-27
# m 2025-08-04

from base64 import b64encode
from hashlib import sha1

from requests import ConnectionError, get, put

from errors import safelogged
from utils import *


@safelogged()
def to_github() -> None:
    base_url = 'https://api.github.com/repos/ezio416/tm-json/contents'
    headers = {
        'Accept': 'application/vnd.github+json',
        'Authorization': f'Bearer {os.environ['GITHUB_TM_JSON_TOKEN']}',
        'X_GitHub-Api-Version': '2022-11-28'
    }

    time.sleep(WAIT_TIME)
    log('info: getting info from Github')
    req = get(base_url, headers=headers)
    contents = req.json()

    for file in (
        FILE_SEASONAL,
        FILE_TOTD,
        FILE_WARRIOR,
        FILE_WEEKLY,
        FILE_ZONE
    ):
        if not os.path.isfile(file):
            print(f'to_github(): not found: {file}')
            continue

        with open(file) as f:
            file_data = f.read()

        basename = os.path.basename(file)
        sha = sha1(f'blob {len(file_data)}\x00{file_data}'.encode()).hexdigest()

        for item in contents:
            if basename != item['name'] or sha == item['sha']:
                continue

            time.sleep(WAIT_TIME)
            log(f'info: sending to Github: {basename}')
            sent = put(
                f'{base_url}/{basename}',
                headers=headers,
                json={
                    'content': b64encode(file_data.encode()).decode(),
                    'message': now(False),
                    'sha': item['sha']
                }
            )

            if sent.status_code == 200:
                log(f'info: sent {basename}')
            else:
                raise ConnectionError(f'error: bad send req ({sent.status_code}) for "{basename}": {sent.text}')

# c 2025-01-27
# m 2025-01-27

from base64 import b64encode
from hashlib import sha1

from requests import ConnectionError, get, put, Response

from errors import safelogged
from utils import *


@safelogged()
def to_github() -> None:
    base_url: str = 'https://api.github.com/repos/ezio416/tm-json/contents'
    headers: dict = {
        'Accept': 'application/vnd.github+json',
        'Authorization': f'Bearer {os.environ['GITHUB_TM_JSON_TOKEN']}',
        'X_GitHub-Api-Version': '2022-11-28'
    }

    time.sleep(WAIT_TIME)
    log('info: getting info from Github')
    req:      Response   = get(base_url, headers=headers)
    contents: list[dict] = req.json()

    for file in (
        FILE_ROYAL,
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
            file_data: str = f.read()

        basename: str = os.path.basename(file)
        sha:      str = sha1(f'blob {len(file_data)}\x00{file_data}'.encode()).hexdigest()

        for item in contents:
            if basename != item['name'] or sha == item['sha']:
                continue

            time.sleep(WAIT_TIME)
            log(f'info: sending to Github: {basename}')
            sent: Response = put(
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
                raise ConnectionError(f'error: bad req ({sent.status_code}) for "{basename}": {sent.text}')

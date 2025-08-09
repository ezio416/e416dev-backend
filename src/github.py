# c 2025-01-27
# m 2025-08-09

import base64
import hashlib
import time

import requests

from constants import *
import errors
import utils


BASE_URL: str = 'https://api.github.com/repos/ezio416/tm-json/contents'
HEADERS: dict[str, str] = {
    'Accept': 'application/vnd.github+json',
    'Authorization': f'Bearer {os.environ['GITHUB_TM_JSON_TOKEN']}',
    'X_GitHub-Api-Version': '2022-11-28'
}


def _get_contents() -> list[dict]:
    utils.log('info: getting info from Github')
    return requests.get(BASE_URL, headers=HEADERS).json()


def _send_file(file: str, contents: list[dict]) -> requests.Response:
    if not os.path.isfile(file):
        utils.log(f'warn: not found: {file}')
        return -1

    with open(file) as f:
        file_data: str = f.read()

    basename: str = os.path.basename(file)
    sha: str = hashlib.sha1(f'blob {len(file_data)}\x00{file_data}'.encode()).hexdigest()

    for item in contents:
        if basename != item['name']:
            continue

        if sha == item['sha']:
            utils.log(f'info: matches copy on Github: {basename}')
            continue

        utils.log(f'info: sending to Github: {basename}')

        time.sleep(0.5)
        return requests.put(
            f'{BASE_URL}/{basename}',
            headers=HEADERS,
            json={
                'content': base64.b64encode(file_data.encode()).decode(),
                'message': f'update {basename}',
                'sha': item['sha']
            }
        )


@errors.safelogged()
def send_regular() -> None:
    contents: list[dict] = _get_contents()

    for file in (
        FILE_SEASONAL,
        FILE_TOTD,
        FILE_WEEKLY,
        FILE_ZONE
    ):
        req: requests.Response = _send_file(file, contents)

        if req.status_code == 200:
            utils.log(f'info: sent {os.path.basename(file)}')
        else:
            raise ConnectionError(f'error: bad send req ({req.status_code}) for "{os.path.basename(file)}": {req.text}')


@errors.safelogged()
def send_warrior() -> None:
    contents: list[dict] = _get_contents()

    for file in (
        FILE_WARRIOR,
        FILE_WARRIOR_NEXT,
    ):
        req: requests.Response = _send_file(file, contents)

        if req.status_code == 200:
            utils.log(f'info: sent {os.path.basename(file)}')
        else:
            raise ConnectionError(f'error: bad send req ({req.status_code}) for "{os.path.basename(file)}": {req.text}')

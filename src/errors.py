# c 2025-01-27
# m 2025-08-05

import json
import os
import time
import traceback as tb

import discord_webhook as dc

from constants import *
import utils


def add_locals(locals: dict[str, dict[str, str]], frame: tb.FrameSummary) -> dict[str, dict[str, str]]:
    locals[f'{frame.filename.split('\\')[-1].replace('.py', '')}.{frame.name}'] = clean_locals(frame.locals)
    return locals


def clean_locals(locals: dict[str, str]) -> dict[str, str]:
    if not locals:
        return {}

    import constants

    for local, value in locals.copy().items():
        if any((
            local.startswith('__') and local.endswith('__'),
            local in constants.__annotations__,
            value.startswith('<class '),
            value.startswith('<function '),
            value.startswith('<module ')
        )):
            locals.pop(local)

    return locals


def error(e: Exception, silent: bool = False) -> None:
    locals: dict[str, dict[str, str]] = {}

    root_stack: list = []
    summary: tb.StackSummary = tb.StackSummary.extract(tb.walk_stack(e.__traceback__.tb_frame), capture_locals=True)
    for frame in reversed(summary):
        if frame.name != 'wrapper' and 'e416dev-backend' in frame.filename:
            root_stack.append(f'{os.path.basename(frame.filename)}, line {frame.lineno}, in {frame.name}')
            locals = add_locals(locals, frame)

    exc: tb.TracebackException = tb.TracebackException.from_exception(e, capture_locals=True)

    tb_stack: list = []
    formatted: list[str] = list(exc.format())
    for line in formatted[1:-1]:
        parts: list[str] = line.split('\n')[:-1]
        halves: list[str] = parts[0].split('"')
        parts[0] = f'{os.path.basename(halves[1])}{halves[2]}'
        parts = parts[:3]
        if '=' in parts[-1]:  # no col specifier, start of locals
            parts.pop()
        for i, _ in enumerate(parts):
            if parts[i].startswith('    '):
                parts[i] = parts[i][2:]
        tb_stack.append('\n'.join(parts))
    tb_stack.append(formatted[-1].rstrip('\n'))

    utils.log(f'error: eid-{id(e)} {tb_stack[-1]}')

    if not silent:
        content: str = f'{DISCORD_USER_ROLE} `eid-{id(e)}`'
        content += f'\n`{utils.now(False, False)}`'
        content += f'\n`{tb_stack[-1]}`'
        content += '\n```py'
        content += f'\n{'\n'.join(root_stack)}'
        content += f'\n{'\n'.join(tb_stack[1:-1])}'
        content += '```'

        for frame in exc.stack:
            locals = add_locals(locals, frame)

        webhook = dc.DiscordWebhook(os.environ['DCWH_SITE_BACKEND_ERRORS'], content=content)
        webhook.add_file(json.dumps(locals, indent=4).encode(), 'locals.json')
        time.sleep(DISCORD_WAIT_TIME)
        webhook.execute()


def safelogged(return_type: type = None, silent: bool = False, log: bool = True):
    def inner(func):
        def wrapper(*args, **kwargs):
            if return_type is not None and return_type.__class__ is not type:
                print(f'{return_type.__name__} is not a type')
                return None

            if log and not silent:
                utils.log(f'info: called {func.__name__}({', '.join([f"{type(s).__name__}('{s}')" for s in args])})')

            try:
                return func(*args, **kwargs)
            except Exception as e:
                error(e, silent)
                return return_type() if return_type is not None else None

        return wrapper
    return inner

# c 2025-01-27
# m 2025-02-14

import json
import traceback as tb

from discord_webhook import DiscordWebhook

from utils import *


def error(e: Exception, silent: bool = False):
    def clear_builtins(locals: dict[str, str]):
        if not locals:
            return

        loc = locals.copy()
        if '__builtins__' in loc:
            loc.pop('__builtins__')
        return loc

    locals = []

    root_stack = []
    summary = tb.StackSummary.extract(tb.walk_stack(e.__traceback__.tb_frame), capture_locals=True)
    for frame in reversed(summary):
        if 'e416dev-backend' in frame.filename:
            root_stack.append(f'{os.path.basename(frame.filename)}, line {frame.lineno}, in {frame.name}')
            locals.append(clear_builtins(frame.locals))
    locals.pop()  # duplicate from wrapper

    exc = tb.TracebackException.from_exception(e, capture_locals=True)

    tb_stack = []
    formatted = list(exc.format())
    for line in formatted[1:-1]:
        parts = line.split('\n')[:-1]
        halves = parts[0].split('"')
        parts[0] = f'{os.path.basename(halves[1])}{halves[2]}'
        parts = parts[:3]
        if '=' in parts[-1]:  # no col specifier, start of locals
            parts.pop()
        for i, _ in enumerate(parts):
            if parts[i].startswith('    '):
                parts[i] = parts[i][2:]
        tb_stack.append('\n'.join(parts))
    tb_stack.append(formatted[-1].rstrip('\n'))

    for frame in exc.stack:
        locals.append(clear_builtins(frame.locals))
    local_data = json.dumps(locals, indent=2, sort_keys=False).encode()

    log(f'error: eid-{id(e)} {tb_stack[-1]}')

    if not silent:
        content = f'<@&1205257336252534814> `eid-{id(e)}`\n`{now(False)}`\n```py\n{\
            '\n'.join(root_stack)}\n{'\n'.join(tb_stack[1:-1])}````{tb_stack[-1]}`'

        webhook = DiscordWebhook(
            os.environ['dcwh-site-backend-errors'],
            content=content
        )
        webhook.add_file(local_data, 'locals.json')
        webhook.execute()


def safelogged(return_type: type = None, silent: bool = False, do_log: bool = True):
    def inner(func):
        def wrapper(*args, **kwargs):
            if return_type is not None and return_type.__class__ is not type:
                print(f'{return_type.__name__} is not a type')
                return None

            if do_log and not silent:
                log(f'info: called {func.__name__}({', '.join([f"{type(s).__name__}('{s}')" for s in args])})')

            try:
                return func(*args, **kwargs)
            except Exception as e:
                error(e, silent)
                return return_type() if return_type is not None else None

        return wrapper
    return inner

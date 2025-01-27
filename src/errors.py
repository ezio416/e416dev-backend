# c 2025-01-27
# m 2025-01-27

import traceback

from discord_webhook import DiscordWebhook

from utils import *


def exception_causing_code(e: BaseException) -> traceback.FrameSummary:
    return traceback.TracebackException.from_exception(e).stack[-1]  # doesn't properly work when files are split


def error(e: Exception, silent: bool = False) -> None:
    code: traceback.FrameSummary = exception_causing_code(e)

    loc: str = f'in {os.path.basename(code.filename)}, line {code.lineno}, column {code.colno}, {code.name}()'

    log(f'error: {loc}: {type(e).__name__}: {e} id<{id(e)}>')

    if not silent:
        DiscordWebhook(
            os.environ['dcwh-site-backend-errors'],
            content=f'<@&1205257336252534814> id<`{id(e)}`>\n`{now(False)}`\n`{type(e).__name__}: {e}`\n`{loc}`\n\n`{code.line}`'
        ).execute()


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

        wrapper.__name__ = func.__name__  # feels like a bad idea but it works
        return wrapper
    return inner

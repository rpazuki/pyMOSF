
def int_(value, /, base: int = 10, default: int = 0):
    try:
        return int(value)
    except TypeError:
        return default


def __chain_traceback(tb, message: str = "", counter: int = 1) -> str:
    """A recursive call that extract the exceptions' files.

    Parameters
    ----------
    tb : TracebackType
        exceptions's __traceback__.
    message : str, optional
        The chain of file paths and line numbers, by default ""
    counter : int, optional
        The chain order number, by default 1
    Returns
    -------
    str
       The chain of file paths and line numbers from exceptions's __traceback__.
    """
    if tb is None:
        return message
    #
    if tb.tb_next is not None:
        message += __chain_traceback(tb.tb_next, message, counter+1)
    frame = tb.tb_frame
    message += f'\n{counter}↦ "{frame.f_code.co_filename}", line {frame.f_lineno}'
    return message


def safe_call(log, exceptions={}):
    """A decorator for safely calling a sync function and logging the errors.

    Parameters
    ----------
    log : logging.Logger
        A logger instance to write the errors.
    exceptions : dict, optional
        Dictionary of exceptions and thier corresponding messages to catch and
        log, instead of showing file and line number, by default {}
    """
    def try_call(func):

        def caller(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                if type(e) in exceptions:
                    log.error(f"{exceptions[type(e)]}")
                else:
                    log.error(
                        f"\n{type(e).__name__}:{e}\n{__chain_traceback(e.__traceback__)}\n")
        return caller
    return try_call


def safe_async_call(log, exceptions={}):
    """A decorator for safely calling a async function and logging the errors.

    Parameters
    ----------
    log : logging.Logger
        A logger instance to write the errors.
    exceptions : dict, optional
        Dictionary of exceptions and thier corresponding messages to catch and
        log, instead of showing file and line number, by default {}
    """
    def try_call(func):
        async def caller(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                if type(e) in exceptions:
                    log.error(f"{exceptions[type(e)]}")
                else:
                    log.error(
                        f"\n{type(e).__name__}:{e}\n{__chain_traceback(e.__traceback__)}\n")
        return caller
    return try_call

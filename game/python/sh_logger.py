# ---------------------------------------------------------------------------
#           Name: sh_logger.py
#    Description: universal log templates and settings
# ---------------------------------------------------------------------------


# Savage API
import core

# External modules
import datetime
import sh_custom_utils
import platform
import sh_executor
import inspect
import os
from functools import wraps


class LogContext:
    # Don't pass messages with '%' inside
    is_logging_enabled = True
    MAX_PREFIX_SIZE = 5
    IS_DEBUG_ENABLED = False


class _Colors:
    ANSI_RESET = "\u001B[0m"
    ANSI_BLACK = "\u001B[30m"
    ANSI_RED = "\u001B[31m"
    ANSI_GREEN = "\u001B[32m"
    ANSI_YELLOW = "\u001B[33m"
    ANSI_BLUE = "\u001B[34m"
    ANSI_PURPLE = "\u001B[35m"
    ANSI_CYAN = "\u001B[36m"
    ANSI_WHITE = "\u001B[37m"


def log_debug_info(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if not LogContext.IS_DEBUG_ENABLED:
            return func(*args, **kwargs)

        try:
            module = inspect.getmodule(func).__file__
            head, tail = os.path.split(module)
            tail = tail.split('.py')[0]

            bound = sig.bind(*args, **kwargs)
            bound.apply_defaults()

            values = ', '.join('{}={}'.format(name, repr(value)) for name, value in bound.arguments.items())
            debug(f'{tail} -> {func.__name__}({values})')

            return func(*args, **kwargs)
        except:
            sh_custom_utils.get_and_log_exception_info()

    sig = inspect.signature(func)
    wrapper.__signature__ = inspect.signature(func)
    return wrapper


def info(message, indent=False):
    log_level = "INFO"
    sh_executor.submit_task(_log, log_level, message, indent)


def debug(message, indent=False):
    if LogContext.IS_DEBUG_ENABLED:
        log_level = "DEBUG"
        sh_executor.submit_task(_log, log_level, message, indent, True)


def warn(message, indent=False):
    log_level = "WARN"
    sh_executor.submit_task(_log, log_level, message, indent)


def error(message, indent=False):
    log_level = "ERROR"
    sh_executor.submit_task(_log, log_level, message, indent)


def chat(message, indent=False):
    log_level = "CHAT"
    sh_executor.submit_task(_log, log_level, message, indent, True)


def custom(prefix, message, indent=False):
    sh_executor.submit_task(_log, prefix, message, indent)


def unformatted(message):
    sh_executor.submit_task(core.ConsolePrint, message)


def _log(log_level, message, indent=False, use_colors=False):
    try:
        if LogContext.is_logging_enabled:
            d = datetime.datetime.now()
            date_template = d.strftime("%Y.%m.%d - %H:%M:%S")

            formatted_log_level = "[%s] " % log_level + (LogContext.MAX_PREFIX_SIZE - len(log_level)) * " "
            if indent:
                formatted_log_level = "\n" + formatted_log_level

            message = f"{formatted_log_level}[{date_template}]   {message}\n"
            if use_colors:
                if log_level == 'INFO':
                    message = f'{_Colors.ANSI_GREEN}{message}{_Colors.ANSI_RESET}'
                if log_level == 'DEBUG':
                    message = f'{_Colors.ANSI_YELLOW}{message}{_Colors.ANSI_RESET}'
                if log_level == 'WARN':
                    message = f'{_Colors.ANSI_RED}{message}{_Colors.ANSI_RESET}'
                if log_level == 'CHAT':
                    message = f'{_Colors.ANSI_GREEN}{message}{_Colors.ANSI_RESET}'

            core.ConsolePrint(message)
    except:
        sh_custom_utils.get_and_log_exception_info()


def check_visual_formatting():
    if LogContext.is_logging_enabled:
        unformatted("-----Python loggers------------------------------------------------\n")
        message = "Logger formatting self-check"
        info(message)
        debug(message)
        warn(message)
        error(message)
        chat(message)
        unformatted("-------------------------------------------------------------------\n")
        info("Python version: %s" % platform.python_version())
        unformatted("-------------------------------------------------------------------\n")

# -------------------------------------------------------------------------------------------------------
#          Name: sh_initializer.py
#   Description: Module for single initialization actions on the start of the application
# -------------------------------------------------------------------------------------------------------


# Savage API
import core
import server

import os
import sh_logger as log
import sh_custom_utils
import sh_executor
import configparser
import builtins
import gc
import json

# fix for: 'unknown encoding: idna'
import encodings.idna

CONFIG_FILE_PATH = './..'

PYTHON_CONFIG_NAME = 'config.ini'
PYTHON_CONFIG_DEV_NAME = 'config.dev.ini'
PYTHON_CONFIG_FILE = f'{CONFIG_FILE_PATH}/{PYTHON_CONFIG_NAME}'
PYTHON_CONFIG_DEV_FILE = f'{CONFIG_FILE_PATH}/{PYTHON_CONFIG_DEV_NAME}'


# Called directly from the game engine
def init():
    try:
        gc.disable()
        sh_executor.ExecutorContext.init()
        init_python_config()
        init_paths()
        configure_logging()

        log.info("Initializing basic configuration...")

        import sv_discord

        if sv_discord.DiscordSettings.DISCORD_IS_ENABLED:
            sv_discord.init()

        # Delayed import since python_config is present inside sh_scheduler
        if python_config.getboolean('Python_General', 'SCHEDULER_IS_ENABLED'):
            from sh_scheduler import _Context
            _Context.init()
    except Exception as e:
        print(f'Exception on init: {e}')
        sh_custom_utils.get_and_log_exception_info()


def init_paths():
    if not os.path.exists('python/triggers'):
        os.makedirs('python/triggers')


def init_python_config():
    config = configparser.RawConfigParser(strict=False, allow_no_value=True)
    config.read(PYTHON_CONFIG_FILE)
    log.info(f"Loading config: {PYTHON_CONFIG_NAME}")

    dev_config = configparser.RawConfigParser(strict=False, allow_no_value=True)
    dev_config.read(PYTHON_CONFIG_DEV_FILE)
    is_dev_mode = dev_config.getboolean('Python_Config', 'IS_DEV_MODE', fallback=0)

    # dev-config will overwrite the same values in the base-config
    if is_dev_mode:
        config.read(PYTHON_CONFIG_DEV_FILE)
        log.info(f"Loading DEV config: {PYTHON_CONFIG_DEV_NAME}")

    log.LogContext.IS_DEBUG_ENABLED = bool(dev_config.getboolean('Python_Config', 'IS_DEBUG_ENABLED', fallback=0))

    init_silverback(config)

    # Export
    builtins.python_config = config


def init_silverback(config):
    init_silverback_general(config)
    init_silverback_credentials(config)
    init_silverback_referees(config)
    init_silverback_server_registration(config)


def init_silverback_general(config):
    try:
        silverback_general = dict(config.items('Silverback_General'))
        for key, value in silverback_general.items():
            core.CvarSetString(key, "" if value is None else value)
    except Exception as e:
        print(f'\n\n An error occurred in the CONFIG.INI [Silverback_General]: {e}\n\n')


def init_silverback_credentials(config):
    try:
        # add passwords:
        credentials = 'Credentials'
        core.CvarSetString('svr_password', config.get(credentials, 'svr_password', fallback=''))
        core.CvarSetString('svr_PasswordVIP', config.get(credentials, 'svr_PasswordVIP'))
        core.CvarSetString('sv_refereePassword', config.get(credentials, 'sv_refereePassword'))
        core.CvarSetString('sv_refGodPassword', config.get(credentials, 'sv_refGodPassword'))
        if config.get(credentials, 'svr_apiToken', fallback=''):
            core.CvarSetString('svr_apiToken', config.get(credentials, 'svr_apiToken'))
    except Exception as e:
        print(f'\n\n An error occurred in the CONFIG.INI [Credentials]: {e}\n\n')


def init_silverback_referees(config):
    try:
        # add referees:
        god_refs = list(
            [int(k) for k, v in json.loads(config.get('Silverback_Referees', 'god_refs', fallback=[])).items()])
        normal_refs = list(
            [int(k) for k, v in json.loads(config.get('Silverback_Referees', 'normal_refs', fallback=[])).items()])

        # groups: "none", "guest", "normal", "god"
        for x in god_refs:
            server.AddRefEntry(x, "god")
        for x in normal_refs:
            server.AddRefEntry(x, "normal")
    except Exception as e:
        print(f'\n\n An error occurred in the CONFIG.INI [Silverback_Referees]: {e}\n\n')


def init_silverback_server_registration(config):
    try:
        # register server
        server_registration = dict(config.items('Silverback_Server_Registration'))
        for key, value in server_registration.items():
            core.CvarSetString(key, "" if value is None else value)
    except Exception as e:
        print(f'\n\n An error occurred in the CONFIG.INI [Silverback_Server_Registration]: {e}\n\n')


def configure_logging():
    log.is_logging_enabled = python_config.getboolean('Python_General', 'IS_LOGGING_ENABLED')

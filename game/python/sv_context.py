# ---------------------------------------------------------------------------
#           Name: sv_context
#    Description: Unified storage for server
# ---------------------------------------------------------------------------


import core

import sh_logger as log


class SharedContext:
    CORE_KEY_PREFIX = '_context_key_'
    RETURN_DEFAULT_INT = 0
    RETURN_DEFAULT_STRING = ""
    STORAGE = dict()

    @staticmethod
    def set(key, value, set_cvar=False):
        if key is None:
            return

        if not set_cvar:
            SharedContext.STORAGE[key] = value
            return

        if value is not None:
            SharedContext.STORAGE[key] = value
            # update core values
            if type(value) is str:
                key_with_prefix = f'{SharedContext.CORE_KEY_PREFIX}{key}'
                core.CvarSetString(key_with_prefix, value)
            if type(value) is int:
                key_with_prefix = f'{SharedContext.CORE_KEY_PREFIX}{key}'
                core.CvarSetValue(key_with_prefix, value)

    @staticmethod
    def get(key):
        if key is not None and key in SharedContext.STORAGE:
            return SharedContext.STORAGE[key]
        else:
            return None

    @staticmethod
    def get_int(key):
        if key is not None:
            key_with_prefix = f'{SharedContext.CORE_KEY_PREFIX}{key}'
            if key_with_prefix in SharedContext.STORAGE:
                value = SharedContext.STORAGE[key_with_prefix]
                return int(value)
        return SharedContext.RETURN_DEFAULT_INT

    @staticmethod
    def get_string(key):
        if key is not None:
            key_with_prefix = f'{SharedContext.CORE_KEY_PREFIX}{key}'
            if key_with_prefix in SharedContext.STORAGE:
                value = SharedContext.STORAGE[key_with_prefix]
                return value
        return SharedContext.RETURN_DEFAULT_STRING

    @staticmethod
    def remove(key):
        if key is not None:
            key_with_prefix = f'{SharedContext.CORE_KEY_PREFIX}{key}'
            if key_with_prefix in SharedContext.STORAGE:
                SharedContext.STORAGE.pop(key_with_prefix)
            if key in SharedContext.STORAGE:
                SharedContext.STORAGE.pop(key)

    @staticmethod
    def reset():
        SharedContext.STORAGE.clear()

    # debug info
    @staticmethod
    def log_state():
        for k, v in SharedContext.STORAGE.keys():
            log.info(f'storage: [{k}] -> [{v}]')

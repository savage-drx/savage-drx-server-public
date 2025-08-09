# ---------------------------------------------------------------------------
#           Name: sh_io.py
#    Description: i/o handling (stateful)
# ---------------------------------------------------------------------------

# Savage API
import core

# External modules
import sh_custom_utils
from time import gmtime, strftime
import sh_executor

file_contexts = {}


class IoSettings:
    FILE_BUFFER_SIZE = 1


class FileContext:
    FILE_PATH_TEMPLATE = None

    def __init__(self, file_name, date_prefix):
        FileContext.FILE_PATH_TEMPLATE = f"{core.CvarGetString('homedir')}/logs/python/%s_%s.log"
        self.file_name = file_name
        self.date_prefix = date_prefix
        self.file_path = FileContext.FILE_PATH_TEMPLATE % (self.date_prefix, self.file_name)
        self.file_handler = open(self.file_path, 'a', buffering=IoSettings.FILE_BUFFER_SIZE, encoding='utf-8')

    def re_open(self):
        self.file_path = FileContext.FILE_PATH_TEMPLATE % (self.date_prefix, self.file_name)
        self.file_handler = open(self.file_path, 'a', buffering=IoSettings.FILE_BUFFER_SIZE, encoding='utf-8')

    def close(self):
        self.file_handler.truncate()
        self.file_handler.close()


def save_to_file(file_name, message):
    sh_executor.submit_task(_save_to_file, file_name, message)


def _save_to_file(file_name, message):
    # File should not be closed between messages
    try:
        current_date_prefix = strftime("%Y-%m-%d", gmtime())

        message = "%s\n" % message

        # Find or define a new file handler
        if file_name in file_contexts:
            context = file_contexts[file_name]
        else:
            context = file_contexts[file_name] = FileContext(file_name, current_date_prefix)

        # Check if it's still this day
        if current_date_prefix == context.date_prefix:
            context.file_handler.write(message)
        else:
            # If it is a new day
            context.date_prefix = current_date_prefix
            context.close()

            # Create a new handler
            context.re_open()
            context.file_handler.write(message)
    except:
        sh_custom_utils.get_and_log_exception_info()

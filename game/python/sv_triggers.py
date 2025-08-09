# ---------------------------------------------------------------------------
#           Name: sv_triggers.py
#    Description: Server Admin Triggers
# ---------------------------------------------------------------------------


# External modules
import os
import sys
import imp
import sh_custom_utils
import sh_logger as log

# Global Variables
file_list = None
trigger_list = None


# -------------------------------
def init():
    log.info("Initializing Triggers...")

    # Custom libs path:
    sys.path.append('python/lib/custom')

    # Specify Path to Triggers
    sys.path.append('python/triggers')

    # List all .py modules with prefix 'trigger_'
    global file_list
    global trigger_list
    file_list = [f for f in os.listdir('python/triggers')]
    file_list = [f for f in file_list if os.path.splitext(f)[1] == '.py']
    trigger_list = list(0 for n in range(0, len(file_list)))

    # Try to import each trigger module
    for index in range(0, len(file_list)):
        try:
            trigger_list[index] = __import__(os.path.splitext(file_list[index])[0], globals(), locals(),
                                             ['check', 'execute'], 0)
            log.info("Loading %s" % file_list[index])
        except:
            sh_custom_utils.get_and_log_exception_info()


# -------------------------------
def re_load():
    global file_list
    updated_file_list = [f for f in os.listdir('python/triggers')]
    updated_file_list = [f for f in updated_file_list if os.path.splitext(f)[1] == '.py']
    if len(updated_file_list) is not len(file_list):
        init()
    else:
        # Reload all trigger modules
        for index in range(0, len(trigger_list)):
            try:
                imp.reload(trigger_list[index])
            except:
                sh_custom_utils.get_and_log_exception_info()


# -------------------------------
def frame():
    # Check all trigger modules
    for index in range(0, len(trigger_list)):
        try:
            if trigger_list[index].check():
                trigger_list[index].execute()
        except:
            sh_custom_utils.get_and_log_exception_info()

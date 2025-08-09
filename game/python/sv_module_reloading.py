# ---------------------------------------------------------------------------
#           Name: sv_module_reloading.py
#    Description: Hot-Plug reloading
# ---------------------------------------------------------------------------


import server

# External modules
import sh_custom_utils
import imp
import sh_logger as log


def init():
    pass


# Reloads all modules if param is None; reloads one if param is present
def reload_module(client_index, param):
    if param:
        reload_one(client_index, param)
    else:
        server.Notify(client_index, '^ySet ^yup ^ya ^ymodule ^yname')


# Reloads a module by name
def reload_one(client_index, module_name):
    try:
        log.warn("Trying to reload module '%s'..." % module_name)
        imp.load_module(module_name, *imp.find_module(module_name))
        server.Notify(client_index, '^gModule ^900%s ^gwas ^gsuccessfully ^greloaded' % module_name)
        log.warn("Module '%s' was successfully reloaded" % module_name)
    except:
        server.Notify(client_index, '^gModule ^900%s ^gwas ^900NOT ^greloaded' % module_name)
        log.warn("Module '%s' was NOT reloaded" % module_name)
        sh_custom_utils.get_and_log_exception_info()

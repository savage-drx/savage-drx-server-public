# ---------------------------------------------------------------------------
#           Name: sv_bans.py
#    Description: bans
# ---------------------------------------------------------------------------

# Savage API
import core
import server

# External modules
import os
import shutil
import sh_logger as log
import sh_io
from time import strftime, localtime
import sh_custom_utils
import sv_utils
import ipaddress


class BansSettings:
    # Date format
    DATE_FORMAT = "%Y.%m.%d - %H:%M:%S"
    # IPs
    IS_BAN_ENABLED = python_config.getboolean('Python_Bans', 'IS_BAN_ENABLED', fallback=False)
    BANNED_IPS_FILE_NAME = python_config.get('Python_Bans', 'BANNED_IPS_FILE_NAME')
    BANNED_IPS_INITIAL_FILE_PATH = f'./config/{BANNED_IPS_FILE_NAME}'
    BANNED_IPS_PERSISTENT_FILE_PATH = f"{core.CvarGetString('homedir')}/data/{BANNED_IPS_FILE_NAME}"


class BansContext:
    banned_ips = set()


# Called directly from Silverback
# return: 1 (ip is blacklisted)
# return: 0 (ip is whitelisted)
def ip_check(ipaddr: str) -> int:
    log.info(f'ip_check ip address: {ipaddr}')
    return 0


def check_banned(name, ip, uid):
    # for example: ipaddress.ip_address('192.168.0.1') in ipaddress.ip_network('192.168.0.0/24')
    # => True
    for x in BansContext.banned_ips:
        if ipaddress.ip_address(ip) in ipaddress.ip_network(x):
            client_index = server.GetIndexFromUID(uid)
            ban_client_index(client_index)
            log.warn(f'BANNED: {ip}; {name}; {uid}')
            msg = f'[BANNED] [{strftime(BansSettings.DATE_FORMAT, localtime())}]  {ip}; {name}; {uid}'
            sh_io.save_to_file("banned", msg)


def ban_client_index(client_index):
    # 600.00 x 60 = 3600 000
    # 600.00 x 60 x 12 = 432 000 000
    core.CvarSetValue('svr_defaultBanTime', 432000000)
    core.CommandExec(f'kick {client_index} reason banned')
    # 600.00 x 15 = 900 000 - default
    core.CvarSetValue('svr_defaultBanTime', 900000)


def reload_banned(client_index):
    init_banned()
    server.Notify(client_index, '^900Banned ^greloaded')


def list_banned(client_index):
    server.Notify(client_index, '^900Banned ^gips:')
    for ip in BansContext.banned_ips:
        server.Notify(client_index, f'^c{ip}')


def ban_ip(client_index, ip):
    if update_banned_ips(ip, ban=True):
        core.CommandExec(f'ban {ip} {7200}')
        server.Notify(client_index, f'^900Updated ^gbanned ^gips ^gwith ^900{ip}')
    else:
        server.Notify(client_index, f'^ySomething ^ywent ^ywrong ^yor ^900{ip} ^ywas ^yalready ^900blacklisted')


def unban_ip(client_index, ip):
    core.CommandExec(f'unban {ip}')
    if update_banned_ips(ip, unban=True):
        server.Notify(client_index, f'^900Removed ^gban ^gfor ^gip ^900{ip}')
    else:
        server.Notify(client_index, f'^900{ip} ^ywas ^ynot ^yfound ^yin ^ythe ^ylist')


def init_banned():
    if BansSettings.IS_BAN_ENABLED:
        # check if it's a first run and there is no banned_ip.cfg inside the HOST folder then copy it
        if os.path.isfile(BansSettings.BANNED_IPS_INITIAL_FILE_PATH) \
                and not os.path.isfile(BansSettings.BANNED_IPS_PERSISTENT_FILE_PATH):
            shutil.copyfile(BansSettings.BANNED_IPS_INITIAL_FILE_PATH,
                            os.path.join(BansSettings.BANNED_IPS_PERSISTENT_FILE_PATH))

        BansContext.banned_ips = set()
        try:
            with open(BansSettings.BANNED_IPS_PERSISTENT_FILE_PATH) as f:
                unfiltered = [c.strip() for c in f.readlines()]
            for ip in unfiltered:
                if ip != '' and not ip.startswith(('#', ';')):
                    BansContext.banned_ips.add(ip)
            log.info("Loading banned_ips")
        except:
            log.info("Failed to load banned_ips")
            sh_custom_utils.get_and_log_exception_info()


def update_banned_ips(ip, ban=False, unban=False) -> bool:
    try:
        if ban:
            if ip not in BansContext.banned_ips:
                with open(BansSettings.BANNED_IPS_PERSISTENT_FILE_PATH, 'a') as f:
                    f.write(f'{ip}\n')
                    f.truncate()
                    f.close()
                    BansContext.banned_ips.add(ip)

                for client_index in sv_utils.getActiveIndices():
                    client_index = int(client_index)
                    ip_address = server.GetClientInfo(client_index, INFO_CLIENTIP)
                    for x in BansContext.banned_ips:
                        if ipaddress.ip_address(ip_address) in ipaddress.ip_network(x):
                            ban_client_index(client_index)
                            uid = server.GetClientInfo(client_index, INFO_UID)
                            client_name = server.GetClientInfo(client_index, INFO_NAME)
                            log.warn(f'BANNED: {ip_address}; {client_name}; {uid}')
                            msg = f'[BANNED] [{strftime(BansSettings.DATE_FORMAT, localtime())}]   {ip}; ' \
                                  f'{client_name}; {uid}'
                            sh_io.save_to_file("banned", msg)
                return True
            else:
                return False

        if unban:
            if ip in BansContext.banned_ips:
                with open(BansSettings.BANNED_IPS_PERSISTENT_FILE_PATH, 'r') as f:
                    content = [c.strip() for c in f.readlines()]
                    f.close()

                with open(BansSettings.BANNED_IPS_PERSISTENT_FILE_PATH, 'w') as f:
                    # Save any comments in the header of the file before saving new ip-list
                    for comment in content:
                        if comment == '' or comment.startswith(('#', ';')):
                            f.write(f'{comment}\n')

                    BansContext.banned_ips.remove(ip)
                    for x in sorted(BansContext.banned_ips):
                        f.write(f'{x}\n')

                    f.truncate()
                    f.close()

                return True
            else:
                return False

    except:
        log.info(f"Failed to update {BansSettings.BANNED_IPS_PERSISTENT_FILE_PATH}")
        sh_custom_utils.get_and_log_exception_info()

    return False


def get_default_nick(uid: int) -> str:
    return "UnnamedNewbie"

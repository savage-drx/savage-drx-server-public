#---------------------------------------------------------------------------
#           Name: readme.txt
#         Author: Anthony Beaucamp (aka Mohican)
#  Last Modified: 06/01/2011
#    Description: Silverback Python Triggers Information
#---------------------------------------------------------------------------

Server Admins can use Python Triggers to customize the behaviour of their server.
The scripting engine will automatically load and use triggers placed in this folder.

Popular Triggers are provided in the folder game/python/triggers/library
Simply copy them to the folder game/python/triggers.

More information on triggers is available on the newerth.com website.
URL: http://www.newerth.com/smf/index.php/topic,12591.0.html


A Trigger template is provided below.


#----------------------------------------------------
#           Name: trigger_template.py
#----------------------------------------------------

# Savage API
import core


#-------------------------------
def check():

    # Perform Trigger Test, and return 1 if passed
    if myTest == 1:
        return 1

    # By default, the trigger should return 0
    return 0


#-------------------------------
def execute():

    # Entry executed when check() has returned 1
    core.ConsolePrint('Trigger is executing...\n')
#---------------------------------------------------------------------------
#           Name: readme.txt
#         Author: Anthony Beaucamp (aka Mohican)
#  Last Modified: 06/01/2011
#    Description: Silverback Python Triggers Information
#---------------------------------------------------------------------------

Server Admins can use Python Triggers to customize the behaviour of their server.
The scripting engine will automatically load and use triggers placed in this folder.

Popular Triggers are provided in the folder game/python/triggers/library
Simply copy them to the folder game/python/triggers.

More information on triggers is available on the newerth.com website.
URL: http://www.newerth.com/smf/index.php/topic,12591.0.html


A Trigger template is provided below.


#----------------------------------------------------
#           Name: trigger_template.py
#----------------------------------------------------

# Savage API
import core


#-------------------------------
def check():

    # Perform Trigger Test, and return 1 if passed
    if myTest == 1:
        return 1

    # By default, the trigger should return 0
    return 0


#-------------------------------
def execute():

    # Entry executed when check() has returned 1
    core.ConsolePrint('Trigger is executing...\n')

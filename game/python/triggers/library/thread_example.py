#---------------------------------------------------------------------------
#           Name: thread_example.py
#        Authors: Mohican 
#  Last Modified: 11/02/2012
#    Description: Showing how to thread a trigger.
#---------------------------------------------------------------------------

# Savage API
import core
import server

# Trigger Variables
global doneOnce
doneOnce = 0


#-------------------------------
def check():

    global doneOnce

    # Check that server is in normal "game" mode
    if server.GetGameInfo(GAME_STATE) == 3 and not doneOnce:
        doneOnce = 1
        return 1

    return 0


#-------------------------------
def execute():

    # Spawn Python Thread
    createThread('import thread_example; thread_example.execute_thread()') 
    

#-------------------------------
def execute_thread():

    # IMPORTANT: Do not use CommandExec when running a Thread, as it will 
    #   cause the application to crash. Use CommandBuffer instead!!!
    core.CommandBuffer('echo "Thread example was successfull!"')

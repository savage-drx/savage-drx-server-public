#!/bin/bash

# ----------------------------------------------------------------------------------------------------------------------
DEFAULT_SERVER_PY_CONFIG="config.ini"
SERVER_PY_CONFIG="${1:-$DEFAULT_SERVER_PY_CONFIG}"

# Requires silverback.bin.debug and game64.so.debug to be present in the "bin" directory
DEFAULT_RUN_WITH_DEBUG=0
RUN_WITH_DEBUG="${2:-$DEFAULT_RUN_WITH_DEBUG}"

# fyi: Negative priority requires sudo
NICE_PRIORITY=0

# keep an own SERVER_HOME_DIR for each server on the same host
SERVER_HOME_DIR="/drx/drx-public"
#SERVER_HOME_DIR="/home/igor/drx/drx-public"

SERVER_ROOT_DIR="$(pwd)/game"
BINS_DIR="$(pwd)/bin"
LIBS_DIR="$(pwd)/libs"

# ----------------------------------------------------------------------------------------------------------------------

function run_server() {
  echo "Starting the server..."
  echo "SERVER_HOME_DIR: $SERVER_HOME_DIR"
  echo "SERVER_ROOT_DIR: $SERVER_ROOT_DIR"

  cp -f "$BINS_DIR"/silverback.bin ./silverback.bin
  cp -f "$BINS_DIR"/game64.so ./game/game64.so

  ARGS="set homedir $SERVER_HOME_DIR/;\
        set rootdir $SERVER_ROOT_DIR/;\
        set py_config $SERVER_PY_CONFIG;\
        set sys_allowSymLinks 1"

  # requires sudo to run with negative NICE_PRIORITY: sudo bash -c "..."
  bash -c "LD_LIBRARY_PATH='$LD_LIBRARY_PATH:$LIBS_DIR' \
           nice -n $NICE_PRIORITY \
           expect_unbuffer -p ./silverback.bin '$ARGS'"
}

# ----------------------------------------------------------------------------------------------------------------------

function run_server_with_debug() {
  echo "Starting the server with the DEBUG"
  echo "SERVER_HOME_DIR: $SERVER_HOME_DIR"
  echo "SERVER_ROOT_DIR: $SERVER_ROOT_DIR"

  cp -f "$BINS_DIR"/silverback.bin.debug ./silverback.bin
  cp -f "$BINS_DIR"/game64.so.debug ./game/game64.so

  LOG_FILE="$SERVER_HOME_DIR/logs/gdb/gdb-$(date +%Y.%m.%d-%H:%M:%S).log"

  ARGS="set homedir ${SERVER_HOME_DIR}/;\
        set rootdir ${SERVER_ROOT_DIR}/;\
        set py_config $SERVER_PY_CONFIG;\
        set sys_allowSymLinks 1"

  GDB_COMMAND="gdb ./silverback.bin \
                    -ex 'set args \"$ARGS\"' \
                    -ex 'set confirm off' \
                    -ex 'set pagination off' \
                    -ex 'set style enabled off' \
                    -ex 'set style sources off' \
                    -ex run \
                    -ex bt \
                    -ex quit"

  # requires sudo to run with negative NICE_PRIORITY: sudo bash -c "..."
  bash -c "LD_LIBRARY_PATH='$LD_LIBRARY_PATH:$LIBS_DIR' \
           nice -n $NICE_PRIORITY \
           expect_unbuffer -p $GDB_COMMAND" | tee "$LOG_FILE"
}

# ----------------------------------------------------------------------------------------------------------------------

function create_dirs() {
  if [ ! -d $SERVER_HOME_DIR ]; then
		mkdir -p $SERVER_HOME_DIR
	fi

	if [ ! -d $SERVER_HOME_DIR/logs/gdb ]; then
		mkdir -p $SERVER_HOME_DIR/logs/gdb
	fi

	if [ ! -d $SERVER_HOME_DIR/logs/python ]; then
		mkdir -p $SERVER_HOME_DIR/logs/python
	fi

	if [ ! -d $SERVER_HOME_DIR/data ]; then
  	mkdir -p $SERVER_HOME_DIR/data
  fi
}

# ----------------------------------------------------------------------------------------------------------------------

function rotate_logs() {
  if [ -f $SERVER_HOME_DIR/debug.log ]; then
	  cp $SERVER_HOME_DIR/debug.log $SERVER_HOME_DIR/logs/debug.log."$(date +%Y.%m.%d-%H:%M:%S)"
  fi
}

# ----------------------------------------------------------------------------------------------------------------------


create_dirs
rotate_logs

if [ $RUN_WITH_DEBUG -eq 1 ]; then
  run_server_with_debug
else
  run_server
fi


# todo: nohup, restart-loop
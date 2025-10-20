#!/bin/bash

# ----- CONFIGURATION --------------------------------------------------------------------------------------------------
# Environment variables:
# - SERVER_NAME (keep a unique and simple name without any special symbols for each server on the same host)
# - SERVER_PY_CONFIG_FILE
# - RUN_WITH_DEBUG (requires silverback.bin.debug and game64.so.debug to be present in the "bin" directory)

SERVER_NAME="${SERVER_NAME:-drx-server}"
SERVER_PY_CONFIG_FILE="${SERVER_PY_CONFIG_FILE:-config.ini}"
RUN_WITH_DEBUG="${RUN_WITH_DEBUG:-0}"

# requires sudo to run with negative NICE_PRIORITY: sudo bash -c "..."
NICE_PRIORITY=0

# keep an own SERVER_HOME_DIR for each server on the same host
SERVER_HOME_DIR="/drx/$SERVER_NAME"

SERVER_ROOT_DIR="$(pwd)/game"
BINS_DIR="$(pwd)/bin"
LIBS_DIR="$(pwd)/libs"

# stdbuf:
# -oL = line-buffer stdout
# -eL = line-buffer stderr

# ----------------------------------------------------------------------------------------------------------------------

function run_server() {
  echo "Starting the server..."
  echo "SERVER_HOME_DIR: $SERVER_HOME_DIR"
  echo "SERVER_ROOT_DIR: $SERVER_ROOT_DIR"

  cp -f "$BINS_DIR"/silverback.bin ./silverback.bin
  cp -f "$BINS_DIR"/game64.so ./game/game64.so

  arg_home_dir=";set homedir ${SERVER_HOME_DIR}/"
  arg_root_dir=";set rootdir ${SERVER_ROOT_DIR}/"
  arg_py_config=";set py_config ${SERVER_PY_CONFIG_FILE}"
  arg_server_tag=";set server_tag ${SERVER_NAME}-tag"
  arg_symlinks=";set sys_allowSymLinks 1"

  ARGS="${arg_home_dir} ${arg_root_dir} ${arg_py_config} ${arg_server_tag} ${arg_symlinks}"

  bash -c "LD_LIBRARY_PATH='$LD_LIBRARY_PATH:$LIBS_DIR' \
           nice -n $NICE_PRIORITY \
           stdbuf -oL -eL ./silverback.bin '$ARGS' 2>&1"
}

# ----------------------------------------------------------------------------------------------------------------------

function run_server_with_debug() {
  echo "Starting the server with the DEBUG"
  echo "SERVER_HOME_DIR: $SERVER_HOME_DIR"
  echo "SERVER_ROOT_DIR: $SERVER_ROOT_DIR"

  cp -f "$BINS_DIR"/silverback.bin.debug ./silverback.bin
  cp -f "$BINS_DIR"/game64.so.debug ./game/game64.so

  LOG_FILE="$SERVER_HOME_DIR/logs/gdb/gdb-$(date +%Y.%m.%d-%H:%M:%S).log"

  arg_home_dir=";set homedir ${SERVER_HOME_DIR}/"
  arg_root_dir=";set rootdir ${SERVER_ROOT_DIR}/"
  arg_py_config=";set py_config ${SERVER_PY_CONFIG_FILE}"
  arg_server_tag=";set server_tag ${SERVER_NAME}-tag"
  arg_symlinks=";set sys_allowSymLinks 1"

  ARGS="${arg_home_dir} ${arg_root_dir} ${arg_py_config} ${arg_server_tag} ${arg_symlinks}"

  GDB_COMMAND="gdb ./silverback.bin \
                    -ex 'set args \"$ARGS\"' \
                    -ex 'set confirm off' \
                    -ex 'set pagination off' \
                    -ex 'set style enabled off' \
                    -ex 'set style sources off' \
                    -ex run \
                    -ex bt \
                    -ex quit"


  bash -c "LD_LIBRARY_PATH='$LD_LIBRARY_PATH:$LIBS_DIR' \
           nice -n $NICE_PRIORITY \
           stdbuf -oL -eL $GDB_COMMAND" 2>&1 | tee "$LOG_FILE"
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

# While loop to restart server on crash or exit
while :; do

  rotate_logs

  if [ "$RUN_WITH_DEBUG" -eq 1 ]; then
    run_server_with_debug
  else
    run_server
  fi

	# Wait to restart in case of a fatal restart loop
	echo
	echo "Restarting, Ctrl-C to exit"
	echo
	sleep 5

done

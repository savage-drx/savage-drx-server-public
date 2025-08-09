#!/bin/bash

DEFAULT_SERVER_HOME_DIR="${HOME}/.savagedrx"
DEFAULT_SERVER_ROOT_DIR="$(pwd)/game"

BINS_DIR="$(pwd)/bin"

RUN_WITH_DEBUG="${1:-0}"
SERVER_HOME_DIR="${2:-$DEFAULT_SERVER_HOME_DIR}"
SERVER_ROOT_DIR="${3:-$DEFAULT_SERVER_ROOT_DIR}"

function run_server() {
  echo "Starting the server..."
  echo "SERVER_HOME_DIR: $SERVER_HOME_DIR"
  echo "SERVER_ROOT_DIR: $SERVER_ROOT_DIR"

  cp -f $BINS_DIR/silverback.bin ./silverback.bin
  cp -f $BINS_DIR/game64.so ./game/game64.so

  expect_unbuffer -p ./silverback.bin "set homedir $SERVER_HOME_DIR/;set rootdir $SERVER_ROOT_DIR/;set sys_allowSymLinks 1" 2>&1
}

function run_server_with_debug() {
  echo "Starting the server with the DEBUG"
  echo "SERVER_HOME_DIR: $SERVER_HOME_DIR"
  echo "SERVER_ROOT_DIR: $SERVER_ROOT_DIR"

  cp -f $BINS_DIR/silverback.bin.debug ./silverback.bin
  cp -f $BINS_DIR/game64.so.debug ./game/game64.so

  ARGS="\"set homedir ${SERVER_HOME_DIR}/;set rootdir ${SERVER_ROOT_DIR}/;set sys_allowSymLinks 1\""

	expect_unbuffer -p \
	gdb ./silverback.bin \
	  -ex="set args $ARGS" \
		-ex="set confirm off" \
		-ex="set pagination off" \
		-ex="set style enabled off" \
		-ex="set style sources off" \
		-ex r \
		-ex bt \
		-ex quit \
		2>&1 | tee $SERVER_HOME_DIR/logs/gdb/gdb-"`date +%Y.%m.%d-%H:%M:%S`"
}

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

function rotate_logs() {
  if [ -f $SERVER_HOME_DIR/debug.log ]; then
	  cp $SERVER_HOME_DIR/debug.log $SERVER_HOME_DIR/logs/debug.log."`date +%Y.%m.%d-%H:%M:%S`"
  fi
}


create_dirs
rotate_logs

if [ $RUN_WITH_DEBUG -eq 1 ]; then
  run_server_with_debug
else
  run_server
fi

#!/bin/bash

SERVER_PY_CONFIG_FILE="config_dev.ini"

BINS_DIR="$(pwd)/bin"
SILVERBACK_DEBUG_FILE_NAME="silverback.bin.debug"
GAME_DEBUG_FILE_NAME="game64.so.debug"

if [ ! -f "$BINS_DIR"/"$SILVERBACK_DEBUG_FILE_NAME" ]; then
  echo "Unable to start DEBUG mode without $BINS_DIR/$SILVERBACK_DEBUG_FILE_NAME"
  exit 1
fi

if [ ! -f "$BINS_DIR"/"$GAME_DEBUG_FILE_NAME" ]; then
  echo "Unable to start DEBUG mode without $BINS_DIR/$GAME_DEBUG_FILE_NAME"
  exit 1
fi


SERVER_NAME=drx-server \
SERVER_PY_CONFIG_FILE=$SERVER_PY_CONFIG_FILE \
RUN_WITH_DEBUG=1 \
./start_server.sh
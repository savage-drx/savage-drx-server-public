#!/bin/bash

SERVER_NAME=drx-server

echo "Starting server: $SERVER_NAME"
echo "Logs: /drx/$SERVER_NAME"

SERVICE_TAG=${SERVER_NAME}-tag
SERVER_NAME=$SERVER_NAME nohup ./start_server.sh $SERVICE_TAG > /dev/null &
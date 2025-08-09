#!/bin/bash

DOCKER_SERVER_ROOT_DIR=$1
DOCKER_SERVER_HOST_DIR=$2

echo "Copying files from $DOCKER_SERVER_HOST_DIR to $DOCKER_SERVER_ROOT_DIR ..."

[[ -d $DOCKER_SERVER_ROOT_DIR ]] && rm -r $DOCKER_SERVER_ROOT_DIR/*

cp -ru $DOCKER_SERVER_HOST_DIR/game/ $DOCKER_SERVER_ROOT_DIR
cp -ru $DOCKER_SERVER_HOST_DIR/bin/ $DOCKER_SERVER_ROOT_DIR
cp -ru $DOCKER_SERVER_HOST_DIR/libs/ $DOCKER_SERVER_ROOT_DIR
cp -ru $DOCKER_SERVER_HOST_DIR/config.ini $DOCKER_SERVER_ROOT_DIR
cp -ru $DOCKER_SERVER_HOST_DIR/docker/copy_launcher.sh $DOCKER_SERVER_ROOT_DIR/start_server.sh

[[ -e $DOCKER_SERVER_HOST_DIR/.gdbinit ]] && cp -ru $DOCKER_SERVER_HOST_DIR/.gdbinit $DOCKER_SERVER_ROOT_DIR
[[ -e $DOCKER_SERVER_HOST_DIR/config.dev.ini ]] && cp -ru $DOCKER_SERVER_HOST_DIR/config.dev.ini $DOCKER_SERVER_ROOT_DIR
[[ -d $DOCKER_SERVER_HOST_DIR/tools ]] && cp -ru $DOCKER_SERVER_HOST_DIR/tools/ $DOCKER_SERVER_ROOT_DIR

function create_s2z_archive() {
  cd $DOCKER_SERVER_ROOT_DIR/game
  echo 'Creating savage0.s2z ...'
  zip -0 -r savage0.s2z models script > /dev/null
  echo 'Removing models & scripts ...'
  rm -r models
  rm -r script
}

if ! grep -q "IS_DEV_MODE = 1" $DOCKER_SERVER_HOST_DIR/config.dev.ini; then
  create_s2z_archive
fi

echo
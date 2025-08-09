#!/bin/bash

DOCKER_PATH=./docker

# Main Server
docker compose -f ${DOCKER_PATH}/docker-compose-main.yml --env-file ${DOCKER_PATH}/.env-main up -d

# Duels Server
#docker compose -f ${DOCKER_PATH}/docker-compose-duels.yml --env-file ${DOCKER_PATH}/.env-duels up -d

# Instagib Server
#docker compose -f ${DOCKER_PATH}/docker-compose-instagib.yml --env-file ${DOCKER_PATH}/.env-instagib up -d

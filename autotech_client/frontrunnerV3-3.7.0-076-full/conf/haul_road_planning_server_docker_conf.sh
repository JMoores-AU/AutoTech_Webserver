#
# User setting for haul road planning docker image and container
#
# === User setting ====
# * docker basic setting
TAG_NAME=frontrunner/haul_road_planning_server
VERSION=v1.0.0
PORT=8800
CONTAINER_NAME=haul_road_planning_server

# * Logger setting
# Logger file setting
MAX_LOG_SIZE=10m
MAX_LOG_FILE=3

# LOGGER Level setting
LOGGER_DEBUG_MODULE="" #Info
#LOGGER_DEBUG_MODULE="all" #Debug

# get image version
IMAGE_VERSION="$(docker inspect --format '{{ index .Config.Labels "IMAGE_VERSION"}}' ${TAG_NAME}:${VERSION})"

DOCKER_RUN_OPTIONS="-e JULIA_DEBUG=${LOGGER_DEBUG_MODULE} \
                    -e SERVER_NAME=${CONTAINER_NAME} \
                    -e SERVER_VERSION=${VERSION} \
                    -e IMAGE_VERSION=${IMAGE_VERSION} \
                    --name ${CONTAINER_NAME} \
                    -p $PORT:$PORT \
                    --log-driver=json-file \
                    --log-opt max-size=${MAX_LOG_SIZE} \
                    --log-opt max-file=${MAX_LOG_FILE} \
                   "

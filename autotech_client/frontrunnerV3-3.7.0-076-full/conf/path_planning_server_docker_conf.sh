#!/bin/bash
#
# User setting for path planning docker image and container
#

# === User setting ====
# * docker basic setting
TAG_NAME=frontrunner/path_planning_server
VERSION=v1.0.0
PORT=8801
APP_PORT=8801
CONTAINER_NAME=path_planning_server

# * Logger setting
# Logger file setting
MAX_LOG_SIZE=10m
MAX_LOG_FILE=3

# LOGGER Level setting
LOGGER_DEBUG_MODULE="" #Info
#LOGGER_DEBUG_MODULE="all" #Debug

# * Health check
# This health check system uses docker health check system 
# see: https://docs.docker.com/engine/reference/run/#healthcheck
HEALTH_INTERVAL=30s #[sec] Time between running the check
HEALTH_RETRIES=4 # Consecutive failures needed to report unhealthy
HEALTH_TIMEOUT=10s # Maximum time to allow one check to run
HEALTH_START_PERIOD=60s #Start period for the container to initialize before starting health-retries countdown

# get image version
IMAGE_VERSION="$(docker inspect --format '{{ index .Config.Labels "IMAGE_VERSION"}}' ${TAG_NAME}:${VERSION})"

# total thread number. API service uses 1 thread, so worker thread number is NUM_THREADS-1.
NUM_THREADS="8" 

# =====================

DOCKER_FILE_NAME=${CONTAINER_NAME}.Dockerfile

DOCKER_RUN_OPTIONS="-e JULIA_DEBUG=${LOGGER_DEBUG_MODULE} \
          -e SERVER_NAME=${CONTAINER_NAME} \
          -e SERVER_VERSION=${VERSION} \
          -e IMAGE_VERSION=${IMAGE_VERSION} \
          -e JULIA_NUM_THREADS=${NUM_THREADS},1 \
          --name ${CONTAINER_NAME} \
          -p $PORT:$APP_PORT \
          --log-driver=json-file \
          --log-opt max-size=${MAX_LOG_SIZE} \
          --log-opt max-file=${MAX_LOG_FILE} \
          "

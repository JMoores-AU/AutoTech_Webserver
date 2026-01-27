#!/bin/bash

# Within MONITOR_TIME in seconds, do not restart more than MAX_AUTO_RESTART times.
# In case exceeding MAX_AUTO_RESTART, suspend auto restart feature for the process.
# If not defined, the default is as follows.
# MONITOR_TIME=600
# MAX_AUTO_RESTART=3

PROCESS[0]="frontrunner start server"
PROCESS[1]="frdocker run ${CONF_DIR_PATH}/haul_road_planning_server_docker_conf.sh"
PROCESS[2]="frdocker run ${CONF_DIR_PATH}/path_planning_server_docker_conf.sh"

P_NAME[0]="FrontRunner Server"
P_NAME[1]="haul road planning server"
P_NAME[2]="path planning server"

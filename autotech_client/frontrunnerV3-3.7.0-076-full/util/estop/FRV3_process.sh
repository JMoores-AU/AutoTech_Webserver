#!/bin/bash

# Within MONITOR_TIME in seconds, do not restart more than MAX_AUTO_RESTART times.
# In case exceeding MAX_AUTO_RESTART, suspend auto restart feature for the process.
# If not defined, the default is as follows.
# MONITOR_TIME=600
# MAX_AUTO_RESTART=3

PROCESS[0]="frontrunner start emergency"

P_NAME[0]="FrontRunner E-STOP System"

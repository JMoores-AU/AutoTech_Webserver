#!/bin/bash -l

groups | grep -q sudo
if [ $? -ne 0 ]; then
  if [ ! "$USER" = "root" ]; then
    if [ ! "$USER" = "komatsu" ]; then
      if [ ! "$USER" = "mms" ]; then
        if [ ! "$USER" = "dlog" ]; then
          sudo -l -U $USER | grep -q "(ALL : ALL) ALL"
          if [ $? -ne 0 ]; then
            echo "This command may only be run by a user in the super user group"
            exit
          fi
        fi
      fi
    fi
  fi
fi


# Move current directory to this directory.
cd $(dirname "$0")

# HOST TYPE
FRV3_HOST_TYPE=$1

# set conf dir path
CONF_DIR_PATH=${PWD}/../conf

# Include the functions.
# And load the definition file for the process to handle.
. ./FR_process_util.sh

log_FR_process_event
log_FR_process_event "LAUNCHER[$$](${FRV3_HOST_TYPE}): Starting launcher...."

# Create lock.
LOCK_OBTAINED=""
createLock ${FRV3_HOST_TYPE} "$(basename $0) $*"
if [ $? -ne 0 ] ; then
    LOCK_OBTAINED=0
    log_FR_process_event "LAUNCHER[$$](${FRV3_HOST_TYPE}): Failed to get lock."
else
    LOCK_OBTAINED=1
    log_FR_process_event "LAUNCHER[$$](${FRV3_HOST_TYPE}): Successfully obtained lock!"
fi

# Launch each process.
# Since potential race condition between 2 process, auto restart and restart by operator,
# launch each process with lock.
function launch() {
    local JOB_DESCRIPTION="$1"
    local NAME="$2"

    shift 2
    local COMMAND_LINE=$*

    local LOCKTAG
    LOCKTAG=$(echo "${NAME}" | sed -e "s%\s%_%g")
    createLock "${LOCKTAG}" "${COMMAND_LINE}"

    log_FR_process_event "LAUNCHER[$$](${FRV3_HOST_TYPE}): ${JOB_DESCRIPTION} ${NAME}...."
    if [ $? -ne 0 ] ; then
        log_FR_process_event "LAUNCHER[$$](${FRV3_HOST_TYPE}): Failed to get launch lock for <${NAME}>.  Skip!"
    else
        log_FR_process_event "LAUNCHER[$$](${FRV3_HOST_TYPE}): Successfully obtained launch lock for <${NAME}>!"

        # Double check if the process really is not running.
        # Since the check before invoking this function is outside of lock,
        # there is potential race condition.
        findFRV3Pid "${COMMAND_LINE}"
        FIND_FAILED=$?
        if [ ${FIND_FAILED} -eq 0 ] ; then
            # Running process is found.
            log_FR_process_event "LAUNCHER[$$](${FRV3_HOST_TYPE}): Race condition is detected.   <${NAME}> is already running and skip launching."
        else
            # Confirmed that the process is not running.
            log_FR_process_event "LAUNCHER[$$](${FRV3_HOST_TYPE}): Confirmed with lock that <${NAME}> is not running and start launching..."
            create_log_file

            # launch the process
            nohup ${COMMAND_LINE} >> ${LOGFILE} 2>&1 &

        fi
        log_FR_process_event "LAUNCHER[$$](${FRV3_HOST_TYPE}): Releasing lock for <${NAME}>!"
        rm -f ${MY_LOCKFILE}
    fi
}


# Check processes status ------------------
# Initialize FrontRunner if necessary -----
# Do this even if lock is not obtained.
echo "-------------------------------------"
echo "Starting the FrontRunner ${FRV3_HOST_TYPE} services..."

MAX_AUTO_RESTART=${MAX_AUTO_RESTART}
if [[ -z ${MAX_AUTO_RESTART} ]] ; then
    MAX_AUTO_RESTART=3
    log_FR_process_event "LAUNCHER[$$](${FRV3_HOST_TYPE}): MAX_AUTO_RESTART is not exported.  Applying default: ${MAX_AUTO_RESTART}"
else
    # Error handling.
    if [[ ${MAX_AUTO_RESTART} -lt 0 ]] ; then
        MAX_AUTO_RESTART=0
        log_FR_process_event "LAUNCHER[$$](${FRV3_HOST_TYPE}): ERROR: MAX_AUTO_RESTART is negative value!!!!  Disabling auto restart."
    elif [[ ${MAX_AUTO_RESTART} -eq 0 ]] ; then
        log_FR_process_event "LAUNCHER[$$](${FRV3_HOST_TYPE}): MAX_AUTO_RESTART is exported as zero.  Auto restart is disabled."
    else
        log_FR_process_event "LAUNCHER[$$](${FRV3_HOST_TYPE}): MAX_AUTO_RESTART is exported as ${MAX_AUTO_RESTART}"
    fi
fi

MONITOR_TIME=${MONITOR_TIME}
if [[ -z ${MONITOR_TIME} ]] ; then
    MONITOR_TIME=600
    log_FR_process_event "LAUNCHER[$$](${FRV3_HOST_TYPE}): MONITOR_TIME is not exported.  Applying default: ${MONITOR_TIME}"
else
    # Error handling.
    if [[ ${MONITOR_TIME} -le 0 ]] ; then
        MAX_AUTO_RESTART=0
        MONITOR_TIME=1
        log_FR_process_event "LAUNCHER[$$](${FRV3_HOST_TYPE}): ERROR: MONITOR_TIME is not positive value!!!!  Disabling auto restart."
    else
        log_FR_process_event "LAUNCHER[$$](${FRV3_HOST_TYPE}): MONITOR_TIME is exported as ${MONITOR_TIME} [seconds]"
    fi
fi


STAT_RUNNING=0
STAT_NOT_RUNNING=1
STAT_SUSPENDED=2

# These are just for readability.
PID_ARRAY=()
STAT_ARRAY=()

##############################################
# Crash time information monitoring (BEGIN)
##############################################
# CRASH_TIMES_${proc_num}_${index}
#    FIFO buffer of crash time.
# CRASH_TIMESTAMP_${proc_num}_${index}
#    Human readable style of CRASH_TIMES_${proc_num}_${index}
#    This is to create log.
# CRASH_TIMES_${proc_num}
#    The size of crash time arrays.
#
# The oldest crash time is stored at index = 0.
# This buffer size is controlled to be up to (${MAX_AUTO_RESTART}+1).
# The buffer is controlled like FIFO.
#
# When adding the (${MAX_AUTO_RESTART}+2)th crash time,
# push all CRASH_XXXX_${proc_num}_${index+1} to CRASH_XXXX_${proc_num}_${index},
# then register the latest data at CRASH_XXXX_${proc_num}_${MAX_AUTO_RESTART}.
#
# That means,
#     - 0 <= CRASH_TIMES_${proc_num} <= ${MAX_AUTO_RESTART}+1
#     - If CRASH_TIMES_${proc_num} <= ${MAX_AUTO_RESTART}, no need to suspend yet.
#     - If CRASH_TIMES_${proc_num} > ${MAX_AUTO_RESTART},
#         - The most recent (${MAX_AUTO_RESTART}+1) crashes occurred within:
#               elapsedTime = (CRASH_TIMES_${proc_num}_0 - CRASH_TIMES_${proc_num}_${MAX_AUTO_RESTART})
#         - That means, if the calculated elapsedTime is less than ${MONITOR_TIME},
#           auto-restart functionality shall be suspended.
#

##############################################
# Crash time information monitoring (PREPARATION)
##############################################
# To make sure to have global scope.
# It appears no need to have this, but just leave it.
COUNT=0
for i in "${PROCESS[@]}"; do
    # Initialize the detected size of crashes.
    eval CRASH_TIMES_${COUNT}=0

    # Allocate arrays to have global reference.
    INDEX=0
    while [[ ${INDEX} -le ${MAX_AUTO_RESTART} ]] ; do
        # Any value can be set here.
        # It won't be used without BUG.
        eval CRASH_TIMES_${COUNT}_${INDEX}=0
        eval CRASH_TIMESTAMP_${COUNT}_${INDEX}=0

        let INDEX=${INDEX}+1
    done
    let COUNT=${COUNT}+1
done

##############################################
# Crash time information monitoring (FUNCTIONS)
##############################################
function isAutoRestartAllowed() {
    # Special case to disable auto-restart feature.
    # If ${MAX_AUTO_RESTART} is zero or less, suspend immediately.
    #(Actually, it won't become below zero.  But anyway....)
    if [[ ${MAX_AUTO_RESTART} -le 0 ]] ; then
        log_FR_process_event "LAUNCHER[$$](${FRV3_HOST_TYPE}): Auto-restart feature is not enabled.  Not allowed to restart."
        return 0
    fi

    local PROC_NUM=$1
    local SIZE
    eval SIZE=\$CRASH_TIMES_${PROC_NUM}
    if [[ -z ${SIZE} ]] ; then
        SIZE=0
    fi

    if [[ ${SIZE} -le ${MAX_AUTO_RESTART} ]] ; then
        # Number of the detected crashes are still not exceeding the ${MAX_AUTO_RESTART}.
        # So, auto-restart is still allowed.
        log_FR_process_event "LAUNCHER[$$](${FRV3_HOST_TYPE}): SIZE(${SIZE}) <= MAX_AUTO_RESTART(${MAX_AUTO_RESTART}): Restart allowed."
        return 1
    else
        # Number of the detected crashes exceeds the ${MAX_AUTO_RESTART}.
        # Then, check the elapsed time between the oldest and the latest crashes in this buffer.
        local OLDEST
        eval OLDEST=\$CRASH_TIMES_${PROC_NUM}_0

        local NEWEST
        eval NEWEST=\$CRASH_TIMES_${PROC_NUM}_${MAX_AUTO_RESTART}

        local ELAPSED_TIME
        let ELAPSED_TIME=${NEWEST}-${OLDEST}

        log_FR_process_event "LAUNCHER[$$](${FRV3_HOST_TYPE}): SIZE(${SIZE}) > MAX_AUTO_RESTART(${MAX_AUTO_RESTART}): NEW(${NEWEST}) - OLD(${OLDEST}) = ELAPSED(${ELAPSED_TIME})"

        if [[ ${ELAPSED_TIME} -lt ${MONITOR_TIME} ]] ; then
            log_FR_process_event "LAUNCHER[$$](${FRV3_HOST_TYPE}): ELAPSED(${ELAPSED_TIME}) < MONITOR_TIME(${MONITOR_TIME}): Too frequent crashes are detected."

            # Too frequent crashes are detected.
            local INDEX=0
            local CRASH_HIST=""
            while [[ ${INDEX} -le ${MAX_AUTO_RESTART} ]] ; do
                eval TIMESTAMP=\$CRASH_TIMESTAMP_${PROC_NUM}_${INDEX}
                let INDEX=${INDEX}+1

                if [[ ! -z ${CRASH_HIST} ]] ; then
                    # Put 2 white spaces for readability of log between timestamps....
                    CRASH_HIST="${CRASH_HIST}  "
                fi
                CRASH_HIST="${CRASH_HIST}CRASH[${INDEX}]:<${TIMESTAMP}>"
            done

            log_FR_process_event "LAUNCHER[$$](${FRV3_HOST_TYPE}): More then ${MAX_AUTO_RESTART} crashes are detected within ${MONITOR_TIME} seconds."
            log_FR_process_event "LAUNCHER[$$](${FRV3_HOST_TYPE}): Detected crashes: ${CRASH_HIST}"
            return 0
        else
            log_FR_process_event "LAUNCHER[$$](${FRV3_HOST_TYPE}): ELAPSED(${ELAPSED_TIME}) >= MONITOR_TIME(${MONITOR_TIME}): Not so frequent crashes."

            # Not too frequent crashes.
            # Auto-restart is allowed.
            return 1
        fi
    fi
}
function crashDetectedNow() {
    local PROC_NUM=$1
    local SIZE
    eval SIZE=\$CRASH_TIMES_${PROC_NUM}
    if [[ -z ${SIZE} ]] ; then
        SIZE=0
        eval CRASH_TIMES_${PROC_NUM}=0
    fi

    # The timestamp as the total seconds from 1970/01/01.
    local CURRENT_TIME=$(date +%s)

    # Convert CURRENT_TIME into the human readable timestamp.
    local TIMESTAMP=$(date -d "@${CURRENT_TIME}" "+%Y/%m/%d %H:%M:%S")

    log_FR_process_event "LAUNCHER[$$](${FRV3_HOST_TYPE}): Registering crash time: ${TIMESTAMP} (${CURRENT_TIME}), SIZE(${SIZE}), MAX_AUTO_RESTART(${MAX_AUTO_RESTART})."

    if [[ ${SIZE} -le ${MAX_AUTO_RESTART} ]] ; then
        # Just putting the latest crash time information at the tail of the array.
        eval CRASH_TIMES_${PROC_NUM}_${SIZE}=\${CURRENT_TIME}
        eval CRASH_TIMESTAMP_${PROC_NUM}_${SIZE}=\${TIMESTAMP}

        # Increment array size.
        let SIZE=${SIZE}+1
        eval CRASH_TIMES_${PROC_NUM}=\${SIZE}
    else
        # No need to keep too old crash time information.
        # Push the oldest data away from the FIFO buffer,
        # and store the latest crash time information at the index of ${SIZE}.
        local INDEX1=0
        local INDEX2
        #local OLD1
        #local OLD2
        #local NEW1
        #local NEW2
        while [[ ${INDEX1} -lt ${MAX_AUTO_RESTART} ]] ; do
            let INDEX2=${INDEX1}+1

            # Pushing FIFO buffer.
            #eval OLD1=\$CRASH_TIMESTAMP_${PROC_NUM}_${INDEX1}
            #eval OLD2=\$CRASH_TIMES_${PROC_NUM}_${INDEX1}
            #eval NEW1=\$CRASH_TIMESTAMP_${PROC_NUM}_${INDEX2}
            #eval NEW2=\$CRASH_TIMES_${PROC_NUM}_${INDEX2}
            #log_FR_process_event "LAUNCHER[$$](${FRV3_HOST_TYPE}):\tPushing buffer: INDEX[${INDEX1}]: ${OLD1}(${OLD2}) -->> ${NEW1}(${NEW2})"
            eval CRASH_TIMES_${PROC_NUM}_${INDEX1}=\$CRASH_TIMES_${PROC_NUM}_${INDEX2}
            eval CRASH_TIMESTAMP_${PROC_NUM}_${INDEX1}=\$CRASH_TIMESTAMP_${PROC_NUM}_${INDEX2}

            # Go to next index.
            INDEX1=${INDEX2}
        done

        # Saving the latest crash time information at the index of ${MAX_AUTO_RESTART}.
        #eval OLD1=\$CRASH_TIMESTAMP_${PROC_NUM}_${MAX_AUTO_RESTART}
        #eval OLD2=\$CRASH_TIMES_${PROC_NUM}_${MAX_AUTO_RESTART}
        #NEW1=${TIMESTAMP}
        #NEW2=${CURRENT_TIME}
        #log_FR_process_event "LAUNCHER[$$](${FRV3_HOST_TYPE}):\tPushing buffer: INDEX[${MAX_AUTO_RESTART}]: ${OLD1}(${OLD2}) -->> ${NEW1}(${NEW2})"
        eval CRASH_TIMES_${PROC_NUM}_${MAX_AUTO_RESTART}=\${CURRENT_TIME}
        eval CRASH_TIMESTAMP_${PROC_NUM}_${MAX_AUTO_RESTART}=\${TIMESTAMP}
    fi
}
##############################################
# Crash time information monitoring (END)
##############################################


SUM=0
COUNT=0
for i in "${PROCESS[@]}"; do
    COMMAND_LINE="$i"
    NAME="${P_NAME[${COUNT}]}"

    findFRV3Pid "${COMMAND_LINE}"

    FIND_FAILED=$?
    if [ ${FIND_FAILED} -eq 0 ] ; then
        # Running process is found.
        echo "Running process found: ${NAME}[PID:${FRV3_COMMAND_PID}]"
        PID_ARRAY[${COUNT}]="${FRV3_COMMAND_PID}"
        STAT_ARRAY[${COUNT}]="${STAT_RUNNING}"

        log_FR_process_event "LAUNCHER[$$](${FRV3_HOST_TYPE}): Running process found: ${NAME}[PID:${FRV3_COMMAND_PID}]"
        let SUM=${SUM}+1
    else
        # Launch required process...
        echo "Launching: ${NAME}"
        # invalid process ID for application.
        PID_ARRAY[${COUNT}]=0
        STAT_ARRAY[${COUNT}]="${STAT_NOT_RUNNING}"
        launch "Launching" "${NAME}" "${COMMAND_LINE}"
    fi

    let COUNT=${COUNT}+1
done

##############################################
# Docker health health check function
#
# This function check the docker container health via docker ps command result
# see: https://docs.docker.com/engine/reference/builder/#healthcheck
##############################################
function check_docker_health(){

    local CONTAINER_NAME=$(echo ${COMMAND_LINE} | awk '{print $2}'| sed 's/\.[^\.]*$//')
    local PS_LINE=$(docker ps | grep "${CONTAINER_NAME}")

    if [[ -z "$PS_LINE" ]]; then
        log_FR_process_event "docker container: ${CONTAINER_NAME} is not starting"
        # do nothing, because this launcher is trying to launch it
        :
    elif [[ "`echo ${PS_LINE} | grep 'starting'`" ]]; then
        log_FR_process_event "docker container: ${CONTAINER_NAME} is starting"
        # do nothing
        :
    elif [[ "`echo ${PS_LINE} | grep 'unhealthy'`" ]]; then
        log_FR_process_event "docker container: ${CONTAINER_NAME} is unhealthy. try to stop it."
        # kill the container, then this launcher try to relaunch it.
        $(docker kill ${CONTAINER_NAME})
    else
        # docker container is healthy.
        # do nothing
        :
    fi
}

#------------------------------------------
# Check processes status loop -------------
function monitor_frontrunner_process() {
    while true; do
        sleep 7
        clear
        SUM=0
        COUNT=0
        for i in "${PROCESS[@]}"; do
            COMMAND_LINE="$i"
            NAME="${P_NAME[${COUNT}]}"

            findFRV3Pid "${COMMAND_LINE}"
            FIND_FAILED=$?

            if [ ${FIND_FAILED} -eq 0 ]; then 
                # Running process is found.
                let SUM=${SUM}+1
                echo -e "\E[32m [  Running  ] \E[33m ${NAME}"

                case "${STAT_ARRAY[${COUNT}]}" in
                    "${STAT_RUNNING}")
                        if [[ "${PID_ARRAY[${COUNT}]}" -ne "${FRV3_COMMAND_PID}" ]] ; then
                            # process ID is changed.
                            # must be crashed now.
                            log_FR_process_event "LAUNCHER[$$](${FRV3_HOST_TYPE}): ${NAME} (${COMMAND_LINE}): restarted manually while sleeping."
                            crashDetectedNow ${COUNT}
                            RESTARTED=1
                        fi
                        ;;

                    "${STAT_NOT_RUNNING}")
                        log_FR_process_event "LAUNCHER[$$](${FRV3_HOST_TYPE}): ${NAME} (${COMMAND_LINE}): started."

                        # Must be added at launching.
                        #crashDetectedNow ${COUNT}
                        ;;

                    "${STAT_SUSPENDED}")
                        log_FR_process_event "LAUNCHER[$$](${FRV3_HOST_TYPE}): ${NAME} (${COMMAND_LINE}): started manually."
                        ;;
                esac

                # Even if it has been suspended, reset status as "running"
                # to resume "auto-restart" functionality.
                STAT_ARRAY[${COUNT}]=${STAT_RUNNING}
                PID_ARRAY[${COUNT}]=${FRV3_COMMAND_PID}
            else
                if [[ ${STAT_ARRAY[${COUNT}]} -ne ${STAT_SUSPENDED} ]] ; then
                    log_FR_process_event "LAUNCHER[$$](${FRV3_HOST_TYPE}): ${NAME} (${COMMAND_LINE}): stopped running!"

                    # Crash time....
                    crashDetectedNow ${COUNT}
                    isAutoRestartAllowed ${COUNT}
                    if [[ $? -eq 0 ]] ; then
                        # Not allowed to restart.
                        log_FR_process_event "LAUNCHER[$$](${FRV3_HOST_TYPE}): ${NAME} (${COMMAND_LINE}): suspending auto-restart."
                        STAT_ARRAY[${COUNT}]=${STAT_SUSPENDED}
                    else
                        # Still allowed to restart.
                        STAT_ARRAY[${COUNT}]=${STAT_NOT_RUNNING}
                    fi
                fi

                if [[ ${STAT_ARRAY[${COUNT}]} -eq ${STAT_SUSPENDED} ]] ; then
                    echo -e "\E[31m [Suspended] \E[33m ${NAME}"
                else
                    echo -e "\E[31m [Not Running] \E[33m ${NAME}"

                    # Automatically restart the process.
                    launch "Restarting" "${NAME}" "${COMMAND_LINE}"
                fi
            fi

            # check this process is docker process
            if [[ "$(echo ${COMMAND_LINE} | grep docker_run)" ]]; then
                # if so, check docker health
                check_docker_health
            fi

            let COUNT+=1
        done

        echo "-------------------------------------"
        echo "Number of processes running: ${SUM} out of ${COUNT}"
        echo

        if [ ${SUM} -lt ${COUNT} ]; then
            echo -e "\033[1m \E[31m One or more process stopped running !!! \E[33m \033[0m"
        else
            echo -e "\033[1m \E[32m All processes running \E[33m \033[0m"
        fi
    done
}


#------------------------------------------
# Start monitoring if lock is obtained.
# Otherwise, it must be restarting the suspended process (or unexpected operation).
# Program cannot know which, and terminate this launcher program.
if [[ ${LOCK_OBTAINED} -ne 0 ]] ; then
    log_FR_process_event "LAUNCHER[$$](${FRV3_HOST_TYPE}): Lock obtained.  Keep monitoring..."

    echo "-------------------------------------"
    echo

    echo "Starting FrontRunner Please stand-by..."

    echo

    monitor_frontrunner_process
fi
#------------------------------------------

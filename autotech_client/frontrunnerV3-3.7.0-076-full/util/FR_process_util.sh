#!/bin/bash

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


export FRV3_COMMAND_PID

# Load the default process definition file.
DEFAULT_PROCESS_FILE="./${FRV3_HOST_TYPE}/FRV3_process.sh"
. "${DEFAULT_PROCESS_FILE}"

# Load the definition file for customization.
USER_PROCESS_FILE="/etc/opt/frontrunner/user_conf/${FRV3_HOST_TYPE}/FRV3_process.sh"
if [[ -f ${USER_PROCESS_FILE} ]] ; then
    echo -e "Loading customized process definition file: <${USER_PROCESS_FILE}>"
    . "${USER_PROCESS_FILE}"

    COUNT=0
    for i in "${PROCESS[@]}"; do
        p="${P_NAME[$COUNT]}"
        echo -e "PROCESS:<$p>\tCOMMAND:<$i>"
        let COUNT+=1
    done
fi


function findFRV3Pid() {
    local COMMAND_LINE="$1"
    local PROC=$(ps --no-heading w -C "${COMMAND_LINE}" | grep -e "${COMMAND_LINE}$" | grep -v -e "grep.*${COMMAND_LINE}")

    FRV3_COMMAND_PID=
    if [ ! -z "${PROC}" ] ; then
        for f in ${PROC} ; do
            #echo -e "RET: $f"

            # The range of exit code is 0-255.
            # So, PID cannot be returned.
            FRV3_COMMAND_PID=$f
            return 0
        done
    fi

    # If not running, ${PROC} becomes empty string, and come here.
    return 1
}
function isFRV3ProcessRunning() {
    findFRV3Pid "$1"

    # If process is running, 0 will be returned.
    # Otherwise (not running), 1 will be returned.
    local RET=$?
    if [ ${RET} -eq 0 ] ; then
        # Process is running.
        #echo -e "\"$1\" is running: $(ps --no-heading w -p ${FRV3_COMMAND_PID})"
        #read
        return 1
    else
        # Process is not running.
        #echo -e "\"$1\" is not running"
        #read
        return 0
    fi
}
function isFRV3Worker() {
    case "X$*" in
        Xadmin)
            ;;
        Xcontroller)
            ;;
        Xembedded)
            ;;
        Xemergency)
            ;;
        Xgnssgs)
            ;;
        Xserver)
            ;;
        Xgnssgm)
            ;;
        *)
            # Not a worker name of FrontRunner.
            return 0
    esac

    return 1
}
function killFRV3Process() {
    if [ $# -eq 1 ] ; then
        if [ `echo "$1" | grep -c "\s"` -ne 0 ] ; then
            killFRV3Process $*
            return $?
        else
            # Not a command line to launch frontrunner application.
            # exit with error.
            return 2
        fi
    else
        local WORKER
        isFRV3Worker $3
        if [ $? -eq 1 ] ; then
            WORKER=$3
        else
            isFRV3Worker $2
            if [ $? -eq 1 ] ; then
                WORKER=$2
            else
                # Not a command line to launch frontrunner application.
                # exit with error.
                return 3
            fi
        fi

        local WORKER_PROCESS="java.*../work/${WORKER}"
        local PROC=$(ps --no-heading axw -o pid,command | grep -e "${WORKER_PROCESS}" | grep -v -e "grep.*${WORKER_PROCESS}")
        if [ ! -z "${PROC}" ] ; then
            for f in ${PROC} ; do
                local THE_COMMAND_LINE=$(ps --no-heading w -p $f)
                echo -e "KILLING: ${THE_COMMAND_LINE}"

                local MAX_LOOP=300  # in seconds = 5 minutes.
                local LOOP_COUNTER=0
                local PID=$f
                local FIRST_SIGKILL=true
                local FOUND=false
                while( true ); do
                    PID=$(ps --no-heading -o pid -p ${PID})
                    if [ $? -ne 0 ] ; then
                        # Process not found.
                        break
                    fi

                    FOUND=true
                    if [ ${LOOP_COUNTER} -lt ${MAX_LOOP} ] ; then
                        #log_FR_process_event "\tSIGTERM : $(expr ${LOOP_COUNTER} + 1)"
                        kill -SIGTERM ${PID}
                    else
                        # In case shutdown process of FrontRunner hung up,
                        # SIGTERM will never be able to kill the FrontRunner process.
                        # Then, it will be a side effect by the modification to use SIGTERM.
                        # Wait until timeout, then kill by SIGKILL if still not terminated.
                        if ( ${FIRST_SIGKILL} ) ; then
                            log_FR_process_event "\tSIGTERM timeout.  Sending SIGQUIT to [${PID}] before SIGKILL"

                            # Send SIGQUIT for full thread dumo, and wait for logging full-thread-dump.
                            kill -SIGQUIT ${PID}
                            sleep 5
                        fi

                        log_FR_process_event "\tSIGTERM timeout.  Killing process [${PID}] by SIGKILL"
                        FIRST_SIGKILL=false
                        kill -SIGKILL ${PID}
                    fi

                    # Check after 1 second.
                    # And send SIGTERM signal again until terminated.
                    sleep 1
                    LOOP_COUNTER=$(expr ${LOOP_COUNTER} + 1)
                done

                # ${PID} is always empty string here since the process is already killed.
                # Use ${f} to print the process ID.
                if ( ${FOUND} ) ; then
                    log_FR_process_event "\tKilled process[$f]: ${THE_COMMAND_LINE}"
                    return 0
                else
                    # Very likely, terminated by other process before sending kill signal.
                    log_FR_process_event "\tProcess[$f] to kill not found: ${THE_COMMAND_LINE}"
                    echo -e "Failed to kill process: [PID:$f]"
                    return 4
                fi
            done
        fi

        # If not running, ${PROC} becomes empty string, and come here.
        return 1
    fi
}
function killFRV3ProcessAll() {
    local COUNT=0
    local COMMAND_LINE="$1"

    # killing all docker processes
    for CONTAINER_ID in $(docker ps -q); do
        docker kill ${CONTAINER_ID}
        let COUNT=${COUNT}+1
        log_FR_process_event "Killing docker process:${CONTAINER_ID}"
    done

    log_FR_process_event "Killing all process: ${COMMAND_LINE}"
    while( true ); do
        killFRV3Process ${COMMAND_LINE}
        if [ $? -ne 0 ] ; then
            # No such process.
            echo -e "${COUNT} processes killed: ${COMMAND_LINE}"
            log_FR_process_event "${COUNT} processes killed: ${COMMAND_LINE}"
            return
        fi
        let COUNT=${COUNT}+1
    done
}

MY_LOCKFILE=
function createLock() {
    local LOCKFILE=/tmp/.lock.$1
    local COMMAND_LINE=$2

    # process ID of this script.
    local PROC_ID=$$
    #echo -e "process id=${PROC_ID}"

    # create unique lock ID, since process ID is unique.
    MY_LOCKFILE=${LOCKFILE}.pid${PROC_ID}

    # Temporarily create lock file.
    touch ${MY_LOCKFILE}

    # Check if there are active lock file.
    for f in ${LOCKFILE}.pid*; do
        #echo -e "checking $f"
        if [ "${MY_LOCKFILE}" != "$f" ] ; then
            if [ -e $f ] ; then
                echo -e "lockfile: $f"
                local LOCK_PROC_ID=`echo "$f" | sed -e "s:${LOCKFILE}.pid::g"`
                if [[ ! -z ${LOCK_PROC_ID} ]] ; then
                    echo -e "PROC_ID: <${LOCK_PROC_ID}>"
                    LOCK_PROCESS=`ps --no-heading w -p ${LOCK_PROC_ID}`
                fi

# Remove the lock file if the PID of the lock file is not running.
                if [[ -z ${LOCK_PROCESS} ]] ; then
                    echo -e "no such process: ${LOCK_PROC_ID}"
                    echo -e "removing lock: $f"
                    rm -f $f

# This is clean up unremoved lock for same PID.
# Launcher script obtains lock to start each FrontRunner application.
# The PID is for this launcher script but not for the application to launch.
# So, the process for PID of the lock file does not contain ${COMMAND_LINE},
# and the lock will be removed by this code even if it is necessary.
#
# Remove this code since most of unnecessary lock files will be removed by the code above.
# This is only for a special case as follows.
#   1. Script terminates without removing lock.
#   2. Restart computer.
#   3. When starting script, some other process has had same PID.
# Such case is very rare case, and removing this code will not cause to have too many unnecessary lock files.

#                elif [[ -z `echo "${LOCK_PROCESS}" | grep -F "${COMMAND_LINE}"` ]] ; then
#                    echo -e "The process ID<${LOCK_PROC_ID}> does not match PATTERN<${COMMAND_LINE}>.  PROC=<${LOCK_PROCESS}>"
#                    echo -e "removing lock: $f"
#                    rm -f $f

                else
                    echo -e "\n"
                    echo -e "PATTERN<${COMMAND_LINE}>: Active process is found: ${LOCK_PROC_ID}"
                    echo -e "FOUND PROCESS: <${LOCK_PROCESS}>"

                    # Failed to get lock.
                    # Remove the temporarily created lock.
                    rm -f ${MY_LOCKFILE}
                    return 1
                fi
            fi
        fi
    done

    #echo -e "LOCK<${MY_LOCKFILE}> is obtained successfully."
    return 0
}

LOGFILE=
function create_log_file() {
    local LOGDIR="../logs"
    if [ -L "$LOGDIR" ]
    then
        LOGDIR=$(readlink -f $LOGDIR)
    fi

    # To make sure that the log file can be created.
    # create directory if not exist.
    mkdir -p ${LOGDIR}
    find "${LOGDIR}" -print0 -exec chmod -f 766 {} + > /dev/null 2>&1
    chmod -f 776 ${LOGDIR}
    LOGFILE="${LOGDIR}/FR_process_event.log"
}

function log_FR_process_event() {
    create_log_file

    local TIMESTAMP
    if [ -z "$*" ]; then
      TIMESTAMP=$(date "+%Y/%m/%d %H:%M:%S.%N%tTimeZone: %Z")
    else
      TIMESTAMP=$(date "+%Y/%m/%d %H:%M:%S.%N")
    fi
    echo -e "${TIMESTAMP}\t$*" >> ${LOGFILE}
}

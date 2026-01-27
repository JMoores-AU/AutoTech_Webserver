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


# Move current directory to this directory.
cd $(dirname "$0")

# HOST TYPE
FRV3_HOST_TYPE=$1

# Include the functions.
# And load the definition file for the process to handle.
. ./FR_process_util.sh

# Functions
function kill_frontrunner_launcher() {
    log_FR_process_event "TERMINATOR(${FRV3_HOST_TYPE}): Killing launcher process...."

    LAUNCHER="FrontRunnerV3_launcher.sh"
    PROC=$(ps --no-heading -o pid -C ${LAUNCHER})

    local LAUNCHER_FOUND=0
    for p in ${PROC}; do
        COMMAND_LINE=$(ps --no-heading w -o command -p $p)
        if [ ! -z "$(echo "${COMMAND_LINE}" | grep "${LAUNCHER} ${FRV3_HOST_TYPE}$")" ] ; then
            echo -e "KILLING LAUNCHER PROCESS: ${COMMAND_LINE}"
            kill -9 $p
            local RET=$?
            if [ ${RET} -ne 0 ] ; then
                log_FR_process_event "\tFailed[${RET}] to kill launcher[$p]"
            else
                log_FR_process_event "\tKilled launcher process[$p]"
            fi
            LAUNCHER_FOUND=1
        fi
    done

    if [[ ${LAUNCHER_FOUND} -eq 0 ]] ; then
        log_FR_process_event "\tNo launcher processes found."
    fi
}
function kill_frontrunner_process() {
    for i in "${PROCESS[@]}" ; do
        COMMAND_LINE="$i"
        killFRV3ProcessAll "${COMMAND_LINE}"
    done
}

# Kill frontrunner launcher before killing frontrunner processes
# not to restart the killed processes.
case "X$2" in
    Xfalse|XFalse|XFALSE|Xno|XNo|XNO)
        # Don't kill launcher.
        log_FR_process_event "TERMINATOR(${FRV3_HOST_TYPE}): Restarting process...."
        ;;
    *)
        # Default: Kill launcher to avoid auto-restart.
        log_FR_process_event "TERMINATOR(${FRV3_HOST_TYPE}): Terminating launcher and all processes...."
        kill_frontrunner_launcher
        ;;
esac

# Kill all frontrunner processes
kill_frontrunner_process

exit

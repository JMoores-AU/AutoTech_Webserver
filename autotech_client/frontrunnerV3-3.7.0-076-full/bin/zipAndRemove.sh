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


###############################################################################
# redirect
###############################################################################
redirect() {
    if [ ! -z "${REDIRECT_FILE}" ]; then
        echo -e "$*" >> "${REDIRECT_FILE}"
    else
        echo -e "$*"
    fi
}

###############################################################################
# zipAndRemove (log filename) (pid)
###############################################################################
zipAndRemove() {
    local LOG_FILENAME="$1"
    if [ ! -f "${LOG_FILENAME}" ] ; then
        # if no log to match the search pattern,
        # ${LOG_FILENAME} will be the pattern here.
        return
    fi

    local PID="$2"
    if [ -z "${PID}" ] ; then
        # PID is between the last '_' and '.dbg'
        local PID=${LOG_FILENAME##*_}
        PID=${PID%%.dbg}
    fi

    # Check if this is really PID.
    # frontrunner_pos*.dbg is created without PID.
    # If apply same rule to them, the filename format will be broken.
    if [ -z $(echo ${PID} | sed -e "s:[0-9]::g") ] && [ "${PID#0}" == "${PID}" ] ; then
        # All numeric and no begin with "0".
        # Maybe PID.
        # Confirm if this is not PID of running process
        ps -p${PID} > /dev/null
        if [ $? -eq 0 ] ; then
            # Program for ${PID} is running.
            # This log shall not be archived.
            return
        fi
    else
        # ${PID} is not PID.
        # Skip.
        return
    fi

    # Double check
    if [ $(echo ${LOG_FILENAME} | sed -e "s:_${PID}.dbg$::g") == ${LOG_FILENAME} ] ; then
        # ${LOG_FILENAME} doesn't end with "_${PID}.dbg".
        # Something wrong....
        return
    fi

    # timestamp by stat command: yyyy-mm-dd hh:MM:SS.xxxxxx +/-XXXX
    local FILE_TIMESTAMP=$(stat --printf=%y "${LOG_FILENAME}")

    # Double check
    if [ -z "${FILE_TIMESTAMP}" ] ; then
        redirect "<${LOG_FILENAME}> is removed before zip and move!"
    fi

    # yyyymmdd
    local FILE_DATE=$(echo "${FILE_TIMESTAMP}" | cut --delimiter=" " -f1 | sed -e "s:-::g")

    # yyyymm
    local FILE_MONTH="${FILE_DATE:0:-2}"

    # log storage directory
    mkdir -p "${FILE_MONTH}"

    # convert to "yyyy-mm-dd_hh-MM-SS_p/nXXXX".  (p for +, n for -)
    local FOMATTED_TIMESTAMP=$(echo "${FILE_TIMESTAMP}" | sed -e "s:\.[0-9]*\s: :g" -e "s:\s-: n:g" -e "s:\s+: p:g" -e "s/:/-/g" -e "s:\s\s*:_:g")
    local ZIP_FILENAME="$(echo "${LOG_FILENAME}" | sed s:_${PID}.dbg$:-END_${FOMATTED_TIMESTAMP}_${PID}.dbg:g).zip"

    # Just in case, if conflict by daylight saving....
    local CONFLICT_COUNT=0
    while [ -f "${FILE_MONTH}/${ZIP_FILENAME}" ] ; do
        let CONFLICT_COUNT=CONFLICT_COUNT+1
        ZIP_FILENAME="$(echo "${LOG_FILENAME}" | sed s:_${PID}.dbg$:-END${CONFLICT_COUNT}_${FOMATTED_TIMESTAMP}_${PID}.dbg:g).zip"
    done

    # Insert current timestamp to log file name
    local LOG_FILENAME_TIMESTAMP=$(echo "${LOG_FILENAME}" | sed s:_${PID}.dbg:_${FOMATTED_TIMESTAMP}_${PID}.dbg:g)

    # Double check
    mv -f --backup=numbered ${LOG_FILENAME} ${LOG_FILENAME_TIMESTAMP}
    local RESULT=$?
    if [ ${RESULT} -ne 0 ] ; then
        redirect "Failed to rename <${LOG_FILENAME}> to <${LOG_FILENAME_TIMESTAMP}>"
        return
    fi

    # Create archive & move to minimize the risk to lose log.
    zip -9 -u "${ZIP_FILENAME}" "${LOG_FILENAME_TIMESTAMP}" > /dev/null
    RESULT=$?
    if [ ${RESULT} -ne 0 ] ; then
        redirect "Failed to zip <${LOG_FILENAME_TIMESTAMP}> into <${ZIP_FILENAME}>: ERR(${RESULT})"
        return
    fi

    # It won't occur, but just in case same file is created before move.
    mv -f --backup=numbered "${ZIP_FILENAME}" "${FILE_MONTH}/"
    RESULT=$?
    if [ ${RESULT} -eq 0 ] ; then
        redirect "<${LOG_FILENAME_TIMESTAMP}> -->> <${FILE_MONTH}/${ZIP_FILENAME}>"
        rm -f ${LOG_FILENAME_TIMESTAMP}
    else
        redirect "Failed to move <${ZIP_FILENAME}> into <${FILE_MONTH}> directory"
    fi
}

if [ ! -z "$*" ] ; then
    zipAndRemove "$@"
fi


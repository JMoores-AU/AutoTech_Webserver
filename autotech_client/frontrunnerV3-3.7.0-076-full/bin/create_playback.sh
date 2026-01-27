#!/bin/sh

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


PREFIX_INDEX_FILE="AHS_INDEX_"
PREFIX_CACHE_FILE="AHS_CACHE_"
PREFIX_EVENT_FILE="AHS_EVENTS_"
SUFFIX_LOG_FILES=".log"

DEFAULT_CUSTOM_PREFIX="tmp_"
CUSTOM_PREFIX="${DEFAULT_CUSTOM_PREFIX}"
PREFIX_PLAYBACK_FILE="AHS_LOG_"
SUFFIX_PLAYBACK_FILE=".dat"

DEFAULT_PLAYBACK_DIR="/var/log/frontrunner/frontrunnerV3/playback"

function create_playback_local() {
    local FILENAME="$*"
    # echo "create_playback_local <${INDEX_FILENAME}> @ <$(pwd)>"
    if [ ! -f "${FILENAME}" ] ; then
        echo "Log file <${FILENAME}> is not a regular file."
        return 1
    elif [ "${FILENAME:$((${#FILENAME}-${#SUFFIX_LOG_FILES}))}" != "${SUFFIX_LOG_FILES}" ] ; then
        echo "<${FILENAME}> is not a log file : Suffix is not <${SUFFIX_LOG_FILES}>"
        return 2
    else
        local PREFIX=""
        local SUFFIX="${SUFFIX_LOG_FILES}"
        case "${FILENAME}" in
            ${PREFIX_INDEX_FILE}*)
                PREFIX="${PREFIX_INDEX_FILE}"
                ;;
            ${PREFIX_CACHE_FILE}*)
                PREFIX="${PREFIX_CACHE_FILE}"
                ;;
            ${PREFIX_EVENT_FILE}*)
                PREFIX="${PREFIX_EVENT_FILE}"
                ;;
            *)
                echo "<${FILENAME}> is not a log file : Prefix doesn't match any patterns"
                return 3
                ;;
        esac

        local TIMESTAMP="$(echo "${FILENAME}" | sed -e "s:${PREFIX}::g" -e "s:${SUFFIX}::g")"
        #echo "FILENAME=<${FILENAME}> PREFIX=<${PREFIX}> TIMESTAMP=<${TIMESTAMP}> SUFFIX=<${SUFFIX}>"
        local PLAYBACK_LOG_FILE="${CUSTOM_PREFIX}${PREFIX_PLAYBACK_FILE}${TIMESTAMP}${SUFFIX_PLAYBACK_FILE}"
        echo -e "\nCreating playback log file: ${PLAYBACK_LOG_FILE}"
        zip "${PLAYBACK_LOG_FILE}" *${TIMESTAMP}${SUFFIX_LOG_FILES}
    fi
}

function create_playback_in_dir() {
    local LOG_DIR="$*"
    if [ ! -d "${LOG_DIR}" ] ; then
        echo "<${LOG_DIR}> is not a directory!"
        return 1
    else
        pushd "${LOG_DIR}" > /dev/null
        for f in ${PREFIX_INDEX_FILE}*${SUFFIX_LOG_FILES}; do
            create_playback_local $f
        done
        popd  > /dev/null
        return 0
    fi
}

function create_playback() {
    local LOG_FILEPATH="$*"
    if [ -d "${LOG_FILEPATH}" ] ; then
        create_playback_in_dir "${LOG_FILEPATH}"
        return $?
    elif [ ! -f "${LOG_FILEPATH}" ] ; then
        echo "<${LOG_FILEPATH}> is not a directory or a regular file!"
        return 1
    else
        pushd "$(dirname "${LOG_FILEPATH}")" > /dev/null
        create_playback_local "$(basename "${LOG_FILEPATH}")"
        popd > /dev/null
        return 0
    fi
}

function usage() {
    echo -e ""
    echo -e ""
    echo "USAGE:"
    echo "    $0 (option)"
    echo "        Create playback log in ${DEFAULT_PLAYBACK_DIR}"
    echo -e ""
    echo "    $0 (option) arg1 arg2 ..."
    echo "        Create playback log according to arg1, arg2, ..."
    echo -e ""
    echo -e "OPTION"
    echo "    --prefix=your-prefix, -pyour-prefix"
    echo "        Set custom prefix."
    echo "        If specified multiple times, use the last one."
    echo "        If not specified or empty string is specified, use \"tmp_\" as default."
    echo "    -h|--help"
    echo "        Print this usage."
    echo -e ""
    echo -e "ARGUMENTS"
    echo "    directory-name"
    echo "        Create playback log in the specified directory"
    echo -e ""
    echo "    index-file-name"
    echo "        Create playback log for the specified index file"
}

NEXT_CUSTOM_PREFIX=false
HELP_REQUESTED=false
INDEX=0
declare -a ARGS
for f in "$@"; do
    if [ ${NEXT_CUSTOM_PREFIX} == true ] ; then
        BEFORE="${CUSTOM_PREFIX}"
        CUSTOM_PREFIX="$f"
        echo "Custom prefix changed: \"${BEFORE}\" => \"${CUSTOM_PREFIX}\""

        NEXT_CUSTOM_PREFIX=false
    else
        case "X$f" in
            X-h|X--help)
                HELP_REQUESTED=true
                ;;
            X-p)
                NEXT_CUSTOM_PREFIX=true
                ;;
            X--prefix=*)
                BEFORE="${CUSTOM_PREFIX}"
                CUSTOM_PREFIX="${f#--prefix=}"
                echo "Custom prefix changed: \"${BEFORE}\" => \"${CUSTOM_PREFIX}\""
                ;;
            X-p*)
                BEFORE="${CUSTOM_PREFIX}"
                CUSTOM_PREFIX="${f#-p}"
                echo "Custom prefix changed: \"${BEFORE}\" => \"${CUSTOM_PREFIX}\""
                ;;
            *)
                ARGS[${INDEX}]="$f"
                INDEX=$(expr ${INDEX} + 1)
                ;;
        esac
    fi
done

if [ "${HELP_REQUESTED}" == true ] ; then
    usage
else
    if [ -z "${CUSTOM_PREFIX}" ] ; then
        echo "Custom prefix is empty.  Using default: \"${DEFAULT_CUSTOM_PREFIX}\""
        CUSTOM_PREFIX="${DEFAULT_CUSTOM_PREFIX}"
    fi

    # Ensure to have "_" or "-" at the tail of custom prefix.
    case "${CUSTOM_PREFIX}" in
        *_|*-)
            ;;
        *)
            CUSTOM_PREFIX="${CUSTOM_PREFIX}_"
            ;;
    esac

    echo "Start creating playback file with custom prefix \"${CUSTOM_PREFIX}\"...."
    if [ ${INDEX} -eq 0 ] ; then
        create_playback_in_dir "${DEFAULT_PLAYBACK_DIR}"
    else
        ERROR_DETECTED=0
        for ((i=0; i<${INDEX}; i++)); do
            create_playback "${ARGS[i]}"
            if [ $? -ne 0 ] ; then
                ERROR_DETECTED=1
            fi
        done
        if [ "${ERROR_DETECTED}" -ne 0 ] ; then
            usage
        fi
    fi
fi

echo -e "\nDone."

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


. "$(dirname "$0")/db_utils.sh"

function log_result() {
    local RESULT=$1
    local COMMAND="$2"
    if [ ${RESULT} -eq 0 ] ; then
        echo_and_redirect "SUCCESS: ${COMMAND}"
    else
        echo_and_redirect "FAIL(${RESULT}): ${COMMAND}"
    fi
    return ${RESULT}
}

function usage() {
    echo -e ""
    echo -e ""
    echo "USAGE:"
    echo "    $0 [OPTIONS]"
    echo "OPTIONS:"
    echo "    -r|--reset"
    echo "        Reset database signature for minemobile systems to enforce"
    echo "        re-synchronize all locally cached data with server."
    echo "    -e (SQL command)"
    echo "        Execute SQL command."
    echo "        EXAMPLE: $0 -e \"SELECT * from cfg_deployment;\""
    echo "    -n (SQL command)"
    echo "        Similar to -e option, but result of SELECT command will be"
    echo "        printed without headers."
    echo "    -i|--info"
    echo "        Print mine name and version name of the database."
    echo "    -h|--help"
    echo "        Print this usage."
}

case "X$*" in
    X|X-h|X--help)
        usage
        exit 0
        ;;
    *)
        ;;
esac

set_working_dir $0
popd > /dev/null

set_log_file "$REALDIR/../logs/fr_database_util.log"
init_database_access_info "$REALDIR/../conf/frontrunner.properties"

SHOW_USAGE=0
EXEC=0
EXEC_NOHEADER=0
for f in "$@"; do
    COMMAND="$f"
    if [ ${EXEC} -ne 0 ] ; then
        EXEC=0
        call_database_query "${DB_USER}" "${DB_PASSWORD}" "${DB_SCHEMA}" "${COMMAND}"
        log_result $? "${COMMAND}"
    elif [ ${EXEC_NOHEADER} -ne 0 ] ; then
        EXEC_NOHEADER=0
        call_database_query "${DB_USER}" "${DB_PASSWORD}" "${DB_SCHEMA}" "${COMMAND}" -s -N
        log_result $? "${COMMAND} -s -N"
    else
        case "${COMMAND}" in
            -h|--help)
                SHOW_USAGE=1
                ;;
            -i|--info)
        MINE_NAME=$(echo_mine_name "${DB_USER}" "${DB_PASSWORD}" "${DB_SCHEMA}")
        SYS_VER=$(echo_system_version "${DB_USER}" "${DB_PASSWORD}" "${DB_SCHEMA}")
        echo ""
        echo "DATABASE INFORMATION:"
        echo "    MINE NAME: ${MINE_NAME}"
        echo "      VERSION: ${SYS_VER}"
        ;;
            -r|--reset)
                reset_database_signature "${DB_USER}" "${DB_PASSWORD}" "${DB_SCHEMA}"
                if [ $? -ne 0 ] ; then
                    echo_and_redirect "Failed resetting database signature."
                    echo_and_redirect "Probably, database upgrade patch is not applied properly."
                    echo_and_redirect "Fix up problem and reset again."
                else
                    echo_and_redirect "Succeed resetting database signature."
                fi
                ;;
            -e)
                EXEC=1
                ;;
            -e*)
                COMMAND="${COMMAND:2}"
                call_database_query "${DB_USER}" "${DB_PASSWORD}" "${DB_SCHEMA}" "${COMMAND}"
                log_result $? "${COMMAND}"
                ;;
            -n)
                EXEC_NOHEADER=1
                ;;
            -n*)
                COMMAND="${COMMAND:2}"
                call_database_query "${DB_USER}" "${DB_PASSWORD}" "${DB_SCHEMA}" "${COMMAND}" -s -N
                log_result $? "${COMMAND} -s -N"
                ;;
            *)
                echo_and_redirect "Unknown option: ${COMMAND}"
                echo_and_redirect "Applying as SQL command....."
                SHOW_USAGE=1

                # Should it be confirmed to execute?
                call_database_query "${DB_USER}" "${DB_PASSWORD}" "${DB_SCHEMA}" "${COMMAND}"
                log_result $? "${COMMAND}"
                ;;
        esac
    fi
done

if [ ${SHOW_USAGE} -ne 0 ] ; then
    usage
fi

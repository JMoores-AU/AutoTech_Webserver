#!/bin/bash

export LOG_FILE=""
export DB_USER="root"
export DB_SCHEMA="frontrunnerV3"
export DB_PASSWORD=""


###############################################################################
# Set REALPATH as the path to given file and REALDIR as the directory.
###############################################################################
export REALPATH
export REALDIR
function set_working_dir() {

    # Get the fully qualified path to the script
    local SCRIPT
    local PWD
    case $0 in
        /*)
            SCRIPT="$0"
            ;;
        *)
            PWD=`pwd`
            SCRIPT="$PWD/$0"
            ;;
    esac

    # Resolve the true real path without any sym links.
    local CHANGED
    local TOKENS
    CHANGED=true
    while [ "X$CHANGED" != "X" ]
    do
        # Change spaces to ":" so the tokens can be parsed.
        SCRIPT=`echo $SCRIPT | sed -e 's; ;:;g'`
        # Get the real path to this script, resolving any symbolic links
        TOKENS=`echo $SCRIPT | sed -e 's;/; ;g'`
        REALPATH=
        for C in $TOKENS; do
            REALPATH="$REALPATH/$C"
            while [ -h "$REALPATH" ] ; do
                LS="`ls -ld "$REALPATH"`"
                LINK="`expr "$LS" : '.*-> \(.*\)$'`"
                if expr "$LINK" : '/.*' > /dev/null; then
                    REALPATH="$LINK"
                else
                    REALPATH="`dirname "$REALPATH"`""/$LINK"
                fi
            done
        done
        # Change ":" chars back to spaces.
        REALPATH=`echo $REALPATH | sed -e 's;:; ;g'`

        if [ "$REALPATH" = "$SCRIPT" ]
        then
            CHANGED=""
        else
            SCRIPT="$REALPATH"
        fi
    done

    # Change the current directory to the location of the script
    pushd "`dirname "$REALPATH"`" > /dev/null
    REALDIR=`pwd`
}


###############################################################################
# Log file to use
###############################################################################
function set_log_file() {
    LOG_FILE="$1"
}


###############################################################################
# echo_and_redirect
###############################################################################
function echo_and_redirect() {
    local now="$(date +'%D %T')"
    echo -e "$now> $*"

    if [ ! -z "$LOG_FILE" ] 
    then
        # Make sure that the directory exists.
        # If no permission to make the directory, this fails.
        # If it fails, redirect the echo into the log file fails, too.
        LOG_DIR=$(readlink $(dirname $LOG_FILE))
        mkdir -p $LOG_DIR
        find "$LOG_DIR" -print0 -exec chmod -f 766 {} + > /dev/null 2>&1
        chmod -f 776 $LOG_DIR
        chown -f komatsu:komatsu /var/log/frontrunner/frontrunnerV3/logs/
        find /var/log/frontrunner/frontrunnerV3/logs -print0 -exec chown -f komatsu:komatsu {} + > /dev/null 2>&1
        echo -e "$now> $*" >> "$LOG_FILE"
        return $?
    else
        return 0
    fi
}


###############################################################################
# Let operator enter yes or no.
###############################################################################
function yes_or_no() {
    local VAL
    while ( true ) ; do
        if [ -z "$*" ] ; then
            read VAL
        else
            read -p "$* " VAL
        fi
        case ${VAL} in
            YES|yes|Yes|y|Y)
                return 1
                ;;
            NO|no|No|n|N)
                return 0
                ;;
            *)
                echo "Enter yes or no."
        esac
    done
}


###############################################################################
# load_property : load frontrunner property for the property name.
###############################################################################
export LOADED_PROPERTY
function load_property() {
    local PROPERTY_FILE="$1"
    local PROPERTY_NAME="$2"
    local PARAM_NAME="LOADED_PROPERTY"
    if [ ! -z "$3" ] ; then
        PARAM_NAME="$3"
    fi

    if [ ! -f "${PROPERTY_FILE}" ] ; then
        eval ${PARAM_NAME}=""
    else
        local LINE=$(grep -e "^\s*${PROPERTY_NAME}\s*=" "${PROPERTY_FILE}")
        #echo -e "LINE=$LINE"
        eval ${PARAM_NAME}=$(echo "${LINE}" | sed -e "s:^\s*${PROPERTY_NAME}\s*=\s*::g")
    fi
}


###############################################################################
# Call database query.
###############################################################################
function call_database_query() { 
    local USER="$1"
    local PASSWORD="$2"
    local SCHEMA="$3"
    local CMD="$4"

    shift 4
    local OPTIONS=$*
    if [ -z "${PASSWORD}" ] ; then
        #echo mysql -u "${USER}" "${SCHEMA}" -e "${CMD}" ${OPTIONS}
        mysql -u "${USER}" "${SCHEMA}" -e "${CMD}" ${OPTIONS}
    else
        #echo mysql -u "${USER}" -p"${PASSWORD}" "${SCHEMA}" -e "${CMD}" ${OPTIONS}
        mysql -u "${USER}" -p"${PASSWORD}" "${SCHEMA}" -e "${CMD}" ${OPTIONS}
    fi
    return $?
}


###############################################################################
# Check if database schema exists.
#        0 : exist.
#  non-zero: not exist.
###############################################################################
function is_dbschema_exists() {
    local USER="$1"
    local PASSWORD="$2"
    local SCHEMA="$3"

    echo_and_redirect "Checking if database ${SCHEMA} exists..."
    call_database_query "${USER}" "${PASSWORD}" "" "SHOW DATABASES LIKE '"${SCHEMA}"';" | grep "${SCHEMA}" > /dev/null
    return $?
}


###############################################################################
# Initialize user, password and database schama to access.
###############################################################################
function init_database_access_info() {
    local PROPERTY_FILE="$1"

    load_property "${PROPERTY_FILE}" "frontrunner.database.realtime.user.name"
    local FR_USER="${LOADED_PROPERTY}"
    if [ -z "${FR_USER}" ] ; then
        FR_USER="${DB_USER}"
    fi
    read -p "Enter user name to connect database server (default:${FR_USER}): " DB_USER
    if [ -z "${DB_USER}" ] ; then
        DB_USER="${FR_USER}"
    fi

    load_property "${PROPERTY_FILE}" "frontrunner.database.realtime.db.name"
    if [ ! -z "${LOADED_PROPERTY}" ] && [ "${DB_SCHEMA}" != "${LOADED_PROPERTY}" ]; then
        echo ""
        echo_and_redirect "Selecting database schema: ${LOADED_PROPERTY}"
        DB_SCHEMA="${LOADED_PROPERTY}"
    fi

    # Let the operator input the password for "${DB_USER}".
    read -s -p "Enter MySQL ${DB_USER} password: " DB_PASSWORD

    # Specify empty string as database schema name.
    # If specified, it fails even if user/password is correct in case the specified database schema does not exist.
    local DB_ACCESS_SUCCEED=0
    while [ ${DB_ACCESS_SUCCEED} -eq 0 ] ; do
        echo -e ""
        call_database_query "${DB_USER}" "${DB_PASSWORD}" "" ";"
        if [ $? -eq 0 ] ; then
            echo_and_redirect "DB access password for user<${DB_USER}> is confirmed."
            DB_ACCESS_SUCCEED=1
        else
            read -s -p "Can't connect, please enter correct password for ${DB_USER}: " DB_PASSWORD
        fi
    done
}


###############################################################################
# Get mine name.
###############################################################################
function echo_mine_name() { 
    local USER="$1"
    local PASSWORD="$2"
    local SCHEMA="$3"

    local RESULT
    local MINE_NAME
    MINE_NAME="$(call_database_query "${USER}" "${PASSWORD}" "${SCHEMA}" "SELECT \`mine_name\` from \`cfg_deployment\`" -s -N)"
    RESULT=$?
    if [[ ! -z "${MINE_NAME}" && ${RESULT} -eq 0 ]] ; then
        echo "${MINE_NAME}" | sed -e "s:\s\s*:_:g"
        return 0
    else
        echo "unknown_mine"
        return 1
    fi
}


###############################################################################
# Get System Version of last successfully launched FrontRunner Server.
###############################################################################
function echo_system_version() { 
    local USER="$1"
    local PASSWORD="$2"
    local SCHEMA="$3"

    local RESULT
    local SYS_VER
    SYS_VER="$(call_database_query "${USER}" "${PASSWORD}" "${SCHEMA}" "SELECT \`VERSION\` from \`_dbinfo\`" -s -N)"
    RESULT=$?
    if [[ ! -z "${SYS_VER}" && ${RESULT} -eq 0 ]] ; then
        echo "${SYS_VER}" | sed -e "s:\s\s*:_:g"
        return 0
    else
        echo "unknown_ver"
        return 1
    fi
}


###############################################################################
# Get Database Signature
###############################################################################
function echo_system_signature() { 
    local USER="$1"
    local PASSWORD="$2"
    local SCHEMA="$3"

    local RESULT
    local DB_SIG
    DB_SIG="$(call_database_query "${USER}" "${PASSWORD}" "${SCHEMA}" "SELECT \`SIGNATURE\` from \`_dbinfo\`" -s -N)"
    RESULT=$?
    if [ ${RESULT} -eq 0 ] ; then
        echo "${DB_SIG}"
        return 0
    else
        echo "(no-signature)"
        return 1
    fi
}


###############################################################################
# Reset database signature to enforce minemobile system to re-synchronize cache.
###############################################################################
function reset_database_signature() { 
    local USER="$1"
    local PASSWORD="$2"
    local SCHEMA="$3"

    echo_and_redirect "Resetting database signature..."
    local BEFORE
    local AFTER
    local RESULT
    BEFORE="$(echo_system_signature "${USER}" "${PASSWORD}" "${SCHEMA}")"
    call_database_query "${USER}" "${PASSWORD}" "${SCHEMA}" "UPDATE \`_dbinfo\` SET \`SIGNATURE\` = unix_timestamp(now(3))*1000"
    RESULT=$?
    if [ ${RESULT} -eq 0 ] ; then
    AFTER="$(echo_system_signature "${USER}" "${PASSWORD}" "${SCHEMA}")"
    echo_and_redirect "Database signature was reset: ${BEFORE} -> ${AFTER}"
    fi
    return ${RESULT}
}

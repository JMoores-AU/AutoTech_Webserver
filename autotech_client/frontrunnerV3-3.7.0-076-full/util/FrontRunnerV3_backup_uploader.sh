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
SCRIPT_DIR=$(dirname "$0")
pushd "${SCRIPT_DIR}" > /dev/null

TIMESTAMP=

# HOST TYPE
FRV3_HOST_TYPE=$1

CONFIG_FILE="FRV3_backup.config"

# Load the default config files.
if [ -f "./${FRV3_HOST_TYPE}/${CONFIG_FILE}" ] ; then
    echo -e "Loading default config file: <${SCRIPT_DIR}/${FRV3_HOST_TYPE}/${CONFIG_FILE}>"
    . "${SCRIPT_DIR}/${FRV3_HOST_TYPE}/${CONFIG_FILE}"
fi

# Load the definition file for customization.
# Expand the environment parameters.
if [ -z ${TIMESTAMP_FORMAT} ] ; then
    TIMESTAMP_FORMAT='+%Y%m%d.%H%M%S'
fi
TIMESTAMP=`date ${TIMESTAMP_FORMAT}`

fatal_error() {
    echo -e "$*"
    echo -e "Hit enter key to close this terminal."
    read
}

BACKUP_DEST_DIR=`eval echo ${BACKUP_DEST_DIR}`
if [ -z "$BACKUP_DEST_DIR" ]; then
    fatal_error "\"BACKUP_DEST_DIR\" (THE DIRECTORY TO UPLOAD BACKUP) SHALL BE DEFINED."
    exit 1
elif [ ! -d "$BACKUP_DEST_DIR" ]; then
    fatal_error "CAN'T FIND DIRECTORY TO UPLOAD BACKUP: \"${BACKUP_DEST_DIR}\""
    exit 2
fi

BACKUP_FILE=`eval echo ${BACKUP_FILE_BASE}.tgz`
FRV3_BACKUP_TMP=`eval echo ${FRV3_BACKUP_TMP}`
FRV3_BACKUP_ROOT=`eval echo ${FRV3_BACKUP_ROOT}`
FRV3_DIR=`eval echo ${FRV3_DIR}`

echo BACKUP_FILE=${BACKUP_FILE}
echo FRV3_BACKUP_TMP=${FRV3_BACKUP_TMP}
echo FRV3_BACKUP_ROOT=${FRV3_BACKUP_ROOT}
echo FRV3_DIR=${FRV3_DIR}

export LOADED_PROPERTY=
load_property() {
    local PROPERTY_FILE="$1"
    local PROPERTY_NAME="$2"
    local PARAM_NAME="LOADED_PROPERTY"
    if [ ! -z "$3" ] ; then
        PARAM_NAME="$3"
    fi

    local LINE=$(grep -e "^\s*${PROPERTY_NAME}\s*=" "${PROPERTY_FILE}")
    #echo -e "LINE=$LINE"
    eval ${PARAM_NAME}=$(echo "${LINE}" | sed -e "s:^\s*${PROPERTY_NAME}\s*=\s*::g")
}
create_database_backup() {
    local PROPERTY_FILE="$1"
    local SCHEMA_PROPERTY="$2"
    local USER_PROPERTY="$3"

    load_property "${PROPERTY_FILE}" "${SCHEMA_PROPERTY}"
    if [ $? -ne 0 ] ; then
        echo -e "${SCHEMA_PROPERTY} is not declared."

        # Fatal error.
        return 127
    fi
    local SCHEMA="${LOADED_PROPERTY}"

    load_property "${PROPERTY_FILE}" "${USER_PROPERTY}"
    if [ $? -ne 0 ] ; then
        echo -e "${USER_PROPERTY} is not declared."
        return 1
    fi
    local SQL_USER="${LOADED_PROPERTY}"

    local BACKUP_FILE="$(eval echo ${FRV3_BACKUP_ROOT}/${FRV3_DATABASE_BACKUP_FORMAT})"
    touch "${BACKUP_FILE}"
    if [ $? -ne 0 ] ; then
        echo -e "Can't create database backup file: ${BACKUP_FILE}"

        # Fatal error.
        return 126
    fi
    
    read -s -p "Enter password to connect to database with USER<${SQL_USER}>: " SQL_PASSWORD

    local COMMAND
    if [ -z "${SQL_PASSWORD}" ] ; then
        COMMAND="$(eval echo ${SQLDB_DUMP_CMD_NO_PASSWD})"
    else
        COMMAND="$(eval echo ${SQLDB_DUMP_CMD})"
    fi

    #echo ${COMMAND}
    ${COMMAND} > "${BACKUP_FILE}"
    if [ $? -ne 0 ] ; then
        echo -e "Failed to create database backup for SCHEMA<${SCHEMA}> as USER<${USER}>."
        return 3
    fi
    return 0
}
is_critical_database_backup_error() {
    if [ $1 -lt 100 ] ; then
        return 0
    else
        return 1
    fi
}
isTrue() {
    case "X$*" in
        Xtrue|XTrue|XTRUE|Xyes|XYes|XYES)
            return 1
            ;;
        *)
            return 0
    esac
}

create_backup() {
    local BACKUP_EXISTS=0

    isTrue ${BACKUP_DATABASE}
    if [ $? -ne 0 ] ; then
        BACKUP_EXISTS=1

        echo "############ Creating Database Backup ...."
        create_database_backup "${FRV3_DIR}/conf/frontrunner.properties" "frontrunner.database.realtime.db.name" "frontrunner.database.realtime.user.name"
        RESULT=$?
        if [ ${RESULT} -ne 0 ] ; then
            # Failed.
            is_critical_database_backup_error ${RESULT}
            if [ $? -ne 0 ] ; then
                echo "Fatal error to create database backup."
                echo "Abort".
                return 1
            else
                # Retry as super user.
                create_database_backup "${FRV3_DIR}/conf/frontrunner.properties" "frontrunner.database.realtime.db.name" "frontrunner.database.realtime.superuser.name"
                RESULT=$?
                if [ ${RESULT} -ne 0 ] ; then
                    echo "Failed to create database backup."
                    return 2
                fi
            fi
        fi
    fi

    isTrue ${BACKUP_PROPERTIES}
    if [ $? -ne 0 ] ; then
        BACKUP_EXISTS=1

        echo "############ Creating backup of configuration files ...."
        tar cf - -C "${FRV3_DIR}" conf | tar xf - -C "${FRV3_BACKUP_ROOT}"
        if [ $? -ne 0 ] ; then
            echo -e "Failed to create backup of properties."
            return 3
        fi
    fi

    local RETURN_CODE=100
    if [ ${BACKUP_EXISTS} -eq 0 ] ; then
        echo -e "WARNING: Nothnig to backup."
        RETURN_CODE=6
    else
        echo "############ Compressing Backup ...." 
        tar zcf "${BACKUP_FILE}" "${FRV3_BACKUP_ROOT}"
        if [ $? -ne 0 ] ; then
            echo -e "Failed to create archive of backup files: ${BACKUP_FILE}"
            RETURN_CODE=7
        else
            RETURN_CODE=0
        fi
    fi

    return ${RETURN_CODE}
}
upload_backup() {
    echo "############ Uploading backup to backup directory \"${BACKUP_DEST_DIR}\"...." 

    local COMMAND
    #echo BACKUP_CMD=${BACKUP_CMD}
    COMMAND="$(eval echo ${BACKUP_CMD})"
    echo ${COMMAND}
    ${COMMAND}
    if [ $? -ne 0 ] ; then
        echo -e "Failed to upload the archive of backup files \"${BACKUP_FILE}\" to \"${BACKUP_DEST_DIR}\""
        return 1
    else
        chmod 666 ${BACKUP_DEST_DIR}/${BACKUP_FILE}
        echo "############ DONE ...."
        return 0
    fi
}


################### Moving into the temporary directory, and create backup there ###################

mkdir -p "${FRV3_BACKUP_TMP}" > /dev/null
if [ $? -ne 0 ] ; then
    fatal_error "Can't create temporary directory: ${FRV3_BACKUP_TMP}"
    exit 3
fi

pushd "${FRV3_BACKUP_TMP}" > /dev/null

mkdir -p "${FRV3_BACKUP_ROOT}" > /dev/null
if [ $? -ne 0 ] ; then
    fatal_error "Can't create backup-root directory: ${FRV3_BACKUP_TMP}/${FRV3_BACKUP_ROOT}"
    exit 4
fi

FAILED=0
create_backup
FAILED=$?
if [ $FAILED -eq 0 ] ; then
    upload_backup
    FAILED=$?
fi

rm -rf "${FRV3_BACKUP_ROOT}" "${BACKUP_FILE}" > /dev/null

popd > /dev/null

# If empty, remove this directory as well.
rmdir "${FRV3_BACKUP_TMP}" > /dev/null

if [ $FAILED -ne 0 ] ; then
    fatal_error "\nBackup was not uploaded.\nPlease fix up the problem, and try again."
    exit 4
else
    echo -e "\nBackup \"${BACKUP_FILE}\" was successfully uploaded to \"${BACKUP_DEST_DIR}\"."
    echo -e "Hit enter key to close this terminal."
    read
    exit 0
fi

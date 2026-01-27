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

CURRENT_DIR=`pwd`

SERVER_RUNNING_ERROR_CODE=220
FILE_NOT_FOUND_ERROR_CODE=221
DBEXISTS_ERROR_CODE=222
DBCREATE_ERROR_CODE=223
DBRESTORE_ERROR_CODE=224
DBRESET_ERROR_CODE=225

sudo chown -f komatsu:komatsu /var/log/frontrunner/frontrunnerV3/logs/
sudo find /var/log/frontrunner/frontrunnerV3/logs -print0 -exec chown -f komatsu:komatsu {} + > /dev/null 2>&1
sudo find /var/log/frontrunner/frontrunnerV3/logs/ -print0 -exec chmod 777 {} + > /dev/null 2>&1

###############################################################################
# setPath : create path name from directory name + file name, and set to the specified parameter.
###############################################################################
function setPath() {
    local PARAM_NAME="$1"
    local DIR_NAME="$2"
    local FILE_NAME="$3"

    if [ -z "${FILE_NAME}" ] ; then
        return 1
    else
        case "${FILE_NAME}" in
            /*|~*)
                echo "File name <${FILE_NAME}> is absolute path."
                echo "Cannot create path name in directory <${DIR_NAME}>"
                return 2
                ;;
            *)
                ;;
        esac
    fi

    # Create path name.
    local VAL
    case "${DIR_NAME}" in
        */)
            VAL="${DIR_NAME}${FILE_NAME}"
            ;;
        *)
            VAL="${DIR_NAME}/${FILE_NAME}"
            ;;
    esac

    eval ${PARAM_NAME}=${VAL}
    return 0
}

###############################################################################
# expand_filename : Expand only '~' to ${HOME} instead of using 'eval'.
###############################################################################
export EXPANDED_FILE_NAME
function expand_filename() {

    local FILE_NAME=$(echo "$*" | sed -e "s:^~/:${HOME}/:g")
    case "X${FILE_NAME}" in
        X)
            # The file name is empty.
            EXPANDED_FILE_NAME=
            ;;
        X/*)
            # The file name is specified as absolute path.
            EXPANDED_FILE_NAME=${FILE_NAME}
            ;;
        *)
            setPath EXPANDED_FILE_NAME "${CURRENT_DIR}" "${FILE_NAME}"
            if [ ! -f "${EXPANDED_FILE_NAME}" ] ; then
                setPath EXPANDED_FILE_NAME "`pwd`" "${FILE_NAME}"
                if [ ! -f "${EXPANDED_FILE_NAME}" ] ; then
                    # As it is to show error message correctly.
                    EXPANDED_FILE_NAME=${FILE_NAME}
                fi
            fi
            ;;
    esac
}

###############################################################################
# update_frdb : apply database patch.
###############################################################################
function update_frdb() {
    expect -c "
        set timeout 30
        spawn frontrunner admin 
        expect {
            \"Waiting SshCommand to be available to start ssh daemon...\" {sleep 2; send \"\n\"}
        }
        expect {
            \"osgi>\" {send \"frdb patch\n\";sleep 1;exp_continue}
            \"Enter frontrunnerV3 mysql port\" {send \"\n\"}
        }
        expect \"Enter frontrunnerV3 database name\"
        send \"${DB_SCHEMA}\n\"
        expect \"Enter frontrunnerV3 user name\"
        send \"${DB_USER}\n\"
        expect \"Enter frontrunnerV3 user password:\"
        send \"${DB_PASSWORD}\n\"
        expect \"Please hit any key to continue...\"
        send \"\n\"
        set timeout 10
        expect {
            timeout {send \"\n\"; sleep 1; exp_continue}
            \"DONE\" {send \"exit\n\"}
        }
        expect \"osgi>\"
        send \"exit\n\"
        expect \" default=y)\"
        send \"\n\"
    "

    return $?
}

###############################################################################
# backup_DB : Create DB backup.
###############################################################################
function backup_DB() {
    local FR_DBSCHEMA="$1"
    local BACKUP_FILE="$2"
    local SQLDB_USER="$3"
    local SQLDB_PASSWORD="$4"

    echo -e "DB BACKUP DB as user ${SQLDB_USER}"
    if [[ ! -z ${SQLDB_PASSWORD} ]] ; then
        mysqldump -u ${SQLDB_USER} -E -R --password=${SQLDB_PASSWORD} ${FR_DBSCHEMA} > "${BACKUP_FILE}" 2> /dev/null
        return $?
    else
        mysqldump -u ${SQLDB_USER} -E -R ${FR_DBSCHEMA} > "${BACKUP_FILE}" 2> /dev/null
        return $?
    fi
}


###############################################################################
# restore.sh
###############################################################################
set_working_dir "$0"
set_log_file "$REALDIR/../logs/restoreDB.log"

IS_SERVER_RUNNING=`ps -ef | grep -v grep | grep -o "DAPP_NAME=_server"`
if [ "$IS_SERVER_RUNNING" != "" ]; 
then
    echo_and_redirect "Please STOP FrontRunner Server before restoring the database!"
    exit $SERVER_RUNNING_ERROR_CODE
fi

# Have it possible to specify the database file to restore as command line argument for easy operation.
if [ ! -z "$1" ] ; then
    expand_filename "$1"

    # Handle relative path, and so on.
    FILE_NAME="${EXPANDED_FILE_NAME}"
fi

if [ ! -z "${FILE_NAME}" ] && [ -f "${FILE_NAME}" ] ; then
    echo_and_redirect "Restoring with file <${FILE_NAME}>"
else
    if [ ! -z "${FILE_NAME}" ] ; then
        echo "ERROR : <${FILE_NAME}> does not exist or is not a regular file."
    fi
    echo -n "Enter backup file name: "
    read INPUT_FILE_NAME

    # Handle relative path, and so on.
    expand_filename "${INPUT_FILE_NAME}"
    FILE_NAME="${EXPANDED_FILE_NAME}"
    if [ "${FILE_NAME}" != "${INPUT_FILE_NAME}" ] ; then
        echo_and_redirect "File name <${INPUT_FILE_NAME}> was expanded to <${FILE_NAME}>"
    fi
fi

if [ -f "${FILE_NAME}" ] && [ "${FILE_NAME}" != "" ];
then
    echo_and_redirect "File $FILE_NAME was found..."
else
    echo_and_redirect "Could not find file '$FILE_NAME'"
    echo_and_redirect "Restore operation was aborted."
    echo_and_redirect ""
    exit $FILE_NOT_FOUND_ERROR_CODE
fi

# HANDLE GZIP FILE
DB_FILETYPE=
case "${FILE_NAME}" in
    *\.sql|*\.SQL)
        DB_FILETYPE=SQL
        ;;
    *\.gz|*\.gz)
        DB_FILETYPE=GZIP
        ;;
    *)
        DB_FILETYPE=SQL
        echo "Maybe unsupported file type: <${FILE_NAME}>"
        echo "This script handles <*.sql> or <*.sql.gz>."
        echo "Trying to restore as an SQL text file."
        ;;
esac
echo ""

# Expand if necessary.
echo DB_FILETYPE=${DB_FILETYPE}
ORG_FILE_NAME="${FILE_NAME}"
case "${DB_FILETYPE}" in
    SQL)
        # Apply as it is.
        ;;
    GZIP)
        # Unzip.
        # ".gz" (3 letters) at tail will be removed.
        FILE_NAME=${ORG_FILE_NAME:0:-3}
        gzip -d "${ORG_FILE_NAME}"

        # Ensure to gzip on exit.
        trap "gzip ${FILE_NAME}" 0
        ;;
esac

# Enter DB Schema name, password and so on.
expand_filename "$REALDIR/../conf/frontrunner.properties"
init_database_access_info "${EXPANDED_FILE_NAME}"

# Restore database....
echo -e ""
echo -e ""
echo -e "Start restoring <${DB_SCHEMA}> database with backup file <${FILE_NAME}>."
yes_or_no "Are you ready? (Y/N)"
if [ $? -eq 0 ];
then
    echo_and_redirect "Restore operation was aborted."
    echo_and_redirect ""
    exit 0
fi
echo ""

# "true" is "0" for this function.
is_dbschema_exists "${DB_USER}" "${DB_PASSWORD}" "${DB_SCHEMA}"
DBEXISTS=$?
if [ $DBEXISTS -eq 0 ];then
    echo_and_redirect "A database with the name <${DB_SCHEMA}> already exists."
    echo -e "Script will restore the given database after backup and drop the current database."
    yes_or_no "Are you ready? (Y/N)"
    if [ $? -ne 0 ]; then

        # Create back up.
        echo ""
        TIMESTAMP=`date '+%Y%m%d.%H%M%S'`
        MINE_NAME=$(echo_mine_name "${DB_USER}" "${DB_PASSWORD}" "${DB_SCHEMA}")
        SYS_VER=$(echo_system_version "${DB_USER}" "${DB_PASSWORD}" "${DB_SCHEMA}")
        BACKUP_FILE="/var/log/frontrunner/backup/RESTORE-BACKUP-${TIMESTAMP}-${MINE_NAME}-${SYS_VER}.sql"
        echo_and_redirect "Creating backup : ${BACKUP_FILE}"
        backup_DB "${DB_SCHEMA}" "${BACKUP_FILE}" "${DB_USER}" "${DB_PASSWORD}"
        if [ $? -ne 0 ] ; then
            echo ""
            echo_and_redirect "Creating database backup failed."
            echo_and_redirect "Please, drop ${DB_SCHEMA} manually, before restoring ${FILE_NAME}"
            exit $DBEXISTS_ERROR_CODE
        fi

        # Drop database.
        echo ""
        echo_and_redirect "Dropping database : ${DB_SCHEMA}"
        call_database_query "${DB_USER}" "${DB_PASSWORD}" "" "DROP DATABASE ${DB_SCHEMA};"
        if [ $? -ne 0 ] ; then
            echo_and_redirect "Dropping database failed."
            echo_and_redirect "Please, drop ${DB_SCHEMA} manually, before restoring ${FILE_NAME}"
            exit $DBEXISTS_ERROR_CODE
        fi
    else
        echo_and_redirect "Please, drop ${DB_SCHEMA} manually, before restoring ${FILE_NAME}"
        exit $DBEXISTS_ERROR_CODE
    fi
fi

echo ""
echo_and_redirect "Creating database ${DB_SCHEMA}..."
call_database_query "${DB_USER}" "${DB_PASSWORD}" "" "create database ${DB_SCHEMA}"
if [ $? -ne 0 ] ; then
    echo_and_redirect "Creating database schema <${DB_SCHEMA}> failed."
    echo_and_redirect "Probably, the privileges of user <${DB_USER}> is not properly configured."
    echo_and_redirect "Please fix problem and retry."
    exit ${DBCREATE_ERROR_CODE}
else
    echo_and_redirect "[OK]"
fi

echo ""
echo_and_redirect "Restoring database ${FILE_NAME}. Please wait(this may take up to 1 minute for large databases)..."
call_database_query "${DB_USER}" "${DB_PASSWORD}" "${DB_SCHEMA}" "source ${FILE_NAME};"
if [ $? -ne 0 ] ; then
    echo_and_redirect "Restoring database failed."
    echo_and_redirect "Please fix problem and retry."
    exit ${DBRESTORE_ERROR_CODE}
else
    echo_and_redirect "[OK]"
fi

echo ""
echo_and_redirect "${FILE_NAME} was restored"

echo ""

PATCH_ERROR=
PATH_EXPECT=$(which expect)
if [ $? -ne 0 ] ; then
    echo_and_redirect "Skip applying DB patch.  (\"expect\" is not installed.)"
    echo -e "Please apply patch manually if necessary."
    echo -e "\t$ fr_admin"
    echo -e "\tosgi> frdb patch"
else
    echo -e "Start applying DB patch."
    yes_or_no "Are you ready? (Y/N)"
    if [ $? -eq 0 ];
    then
        echo ""
        echo_and_redirect "Skip applying DB patch."
        echo -e "Please apply patch manually if necessary."
        echo -e "\t$ fr_admin"
        echo -e "\tosgi> frdb patch"
    else
        echo ""
        echo_and_redirect "Applying DB patch ....."
        update_frdb

        if [ $? -eq 0 ] ; then
            echo_and_redirect "DB patch is applied successfully."
        else
            echo_and_redirect "!!!! Applying DB patch failed.   !!!!"
            echo_and_redirect "!!!! Please apply patch manually !!!!"
            echo           -e "!!!!    $ fr_admin               !!!!"
            echo           -e "!!!!    osgi> frdb patch         !!!!"
        fi
    fi
fi

sudo rm -rf /opt/frontrunner/frontrunnerV3/work/admin/org.eclipse.osgi/

# This will force embedded equipment to download FULL caches upon startup which is a required action after database restores
echo ""
reset_database_signature "${DB_USER}" "${DB_PASSWORD}" "${DB_SCHEMA}"
if [ $? -ne 0 ] ; then
    echo_and_redirect "[FAIL]"

    echo_and_redirect ""
    echo_and_redirect "Resetting database signature failed."
    echo_and_redirect "To avoid mismatch between minemobile system, do"
    echo_and_redirect "    $ ${REALDIR}/fr_database_util.sh --reset"
    echo_and_redirect ""
    exit ${DBRESET_ERROR_CODE}
else
    echo_and_redirect "[OK]"

    echo_and_redirect ""
    echo_and_redirect "Done."
    echo_and_redirect ""
fi

sudo chown -f komatsu:komatsu /var/log/frontrunner/frontrunnerV3/logs/
sudo find /var/log/frontrunner/frontrunnerV3/logs -print0 -exec chown -f komatsu:komatsu {} + > /dev/null 2>&1
sudo find /var/log/frontrunner/frontrunnerV3/logs/ -print0 -exec chmod 777 {} + > /dev/null 2>&1

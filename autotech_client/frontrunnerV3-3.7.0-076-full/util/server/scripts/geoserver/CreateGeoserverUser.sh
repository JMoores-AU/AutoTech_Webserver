#!/bin/bash

DATABASE_NAME=$1
ROOT_USER=$2
ROOT_PASSWORD=$3
FRONTRUNNER_USER=$4
FRONTRUNNER_PASSWORD=$5
GEOSERVER_USER=$6
GEOSERVER_PASSWORD=$7
GEOSERVER_ADDRESS=$8
LOCALHOST="%"

USER_COUNT_SQL_STATEMENT="select count(user) from mysql.user where user='%s'and host='%s'"
SQL_SCRIPT_TO_CREATE_FRONTRUNNER_USER=$(<./create_frontrunner_user.sql)
SQL_SCRIPT_TO_CREATE_GEOSERVER_USER=$(<./create_geoserver_user.sql)
USER_COUNT=0
FAILED="false"

count_user(){
    local user=$1
    local host=$2
    local stmt=$(printf "$USER_COUNT_SQL_STATEMENT" "$user" "$host")

    USER_COUNT=$(mysql -s -s -u $ROOT_USER -p$ROOT_PASSWORD -e "$stmt" 2> /dev/null)

    if [[ $? -ne 0 ]] ; then
            FAILED="true"
    fi
}

execute_SQL_statement(){
    local stmt=$1
    mysql -f -u $ROOT_USER -p$ROOT_PASSWORD -e "$stmt" 2> /dev/null

    if [[ $? -ne 0 ]] ; then
            FAILED="true"
    fi
}

create_frontrunner_user(){
    local stmt=$(printf "$SQL_SCRIPT_TO_CREATE_FRONTRUNNER_USER" "$DATABASE_NAME" "$FRONTRUNNER_USER" "$FRONTRUNNER_PASSWORD" "$LOCALHOST")
    execute_SQL_statement "$stmt"
}

create_geoserver_user(){
    local stmt=$(printf "$SQL_SCRIPT_TO_CREATE_GEOSERVER_USER" "$DATABASE_NAME" "$GEOSERVER_USER" "$GEOSERVER_PASSWORD" "$GEOSERVER_ADDRESS")
    execute_SQL_statement "$stmt"
}

show_error_on_checking_user_exists(){
  echo "An error ocurred checking if the user exists."
  show_error_mitigation_advice
}

show_error_creating_new_user(){
  echo "An error ocurred creating new user."
  show_error_mitigation_advice
}

show_error_mitigation_advice(){
  echo -e "You can verify the following and try again:"
  echo -e "\t1. Check if your database user/password is correct."
  echo -e "\t2. None of the input parameters is empty."
  echo -e "\t3. The order of the input parameters is correct."
  echo -e "\nScript usage:"
  echo -e "./CreateGeoserverUser.sh <database name> <MySQL root user> <MySQLroot password> <fr user> <fr password> <geoserver user> <geoserver password> <geoserver IP adress>"
}


count_user $FRONTRUNNER_USER $LOCALHOST

if [ "$FAILED" == "true" ]; then
    show_error_on_checking_user_exists
    exit 1
fi

if [ $USER_COUNT -eq 0 ]; then
    create_frontrunner_user
    if [ "$FAILED" == "true" ]; then
      show_error_creating_new_user
      exit 2
    fi

    echo "FrontRunner user created"
else
    echo "FrontRunner user already exists. Skipped"
fi

count_user $GEOSERVER_USER $GEOSERVER_ADDRESS

if [ "$FAILED" == "true" ]; then
    show_error_on_checking_user_exists
    exit 1
fi

if [ $USER_COUNT -eq 0 ]; then
    create_geoserver_user
    if [ "$FAILED" == "true" ]; then
      show_error_creating_new_user
      exit 2
    fi

    echo "Geoserver user created"
else
    echo "Geoserver user already exists. Skipped"
fi

#!/bin/bash
user=$1
password=$2

#Extract the database file from mms-frontrunner-database jar and saves it into temp folder db/frontrunner/frontrunnerv3_geoserver.sql
  unzip -d . $(ls -t /opt/frontrunner/frontrunnerV3/bundles/mms-frontrunner-database-?.*.jar | head -n 1) db/frontrunner/frontrunnerv3_geoserver.sql

#Import geoserver database from file
mysql -u $user -p$password < db/frontrunner/frontrunnerv3_geoserver.sql

#Remove temporary folder
rm -rf ./db


#!/bin/bash

my_dir="$(dirname "$0")"

. "$my_dir/../util/FrontRunnerSettingsUtil.sh"

properties_names=(
"frontrunner.database.realtime.geoserver.db.name"
"frontrunner.database.realtime.geoserver.user.name"
"frontrunner.database.realtime.geoserver.user.pwd"
)

properties_values=($1 $2 $3)

patch_frontrunner_properties_file properties_names properties_values

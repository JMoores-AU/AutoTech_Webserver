#!/bin/bash

my_dir="$(dirname "$0")"

. "$my_dir/../util/FrontRunnerSettingsUtil.sh"

properties_names=(
"security.authorization.server.address"
"security.authentication.server.address"
"security.jwks.url"
"security.permissions.url"
)

properties_values=($1 $2 $3 $4)

patch_frontrunner_properties_file properties_names properties_values

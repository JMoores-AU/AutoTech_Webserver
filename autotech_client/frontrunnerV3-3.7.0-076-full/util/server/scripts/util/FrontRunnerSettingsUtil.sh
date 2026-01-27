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


file_name="frontrunner.properties"
conf_path="/etc/opt/frontrunner/frontrunnerV3/conf";
file_path="$conf_path/$file_name"

function patch_frontrunner_properties_file(){
  local name=$1[@]
  local properties_names=("${!name}")

  name=$2[@]
  local properties_values=("${!name}")

  length=${#properties_names[@]}

  pushd $conf_path &>/dev/null
    for (( index=0; index<$length; index++ ))
    do
      property_name=${properties_names[$index]}
      property_value=${properties_values[$index]}
      new_property_string="${property_name}=${property_value}"

      regex_pattern="^\s*${property_name}\s*=.*"
      test_string=$(grep -e "${regex_pattern}" "${file_path}")
      if [ ! -z "$test_string" ]; then
          sed "s|"${regex_pattern}"|"${new_property_string}"|g" -i $file_path
      else
          echo -e "${new_property_string}" >> $file_path
      fi
    done
  popd &>/dev/null
}

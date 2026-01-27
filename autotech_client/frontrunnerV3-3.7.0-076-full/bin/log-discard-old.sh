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


########################################################
# This is a house cleaning script for log and tcpdump
# files. It will delete any files on the specified 
# folder that match the pattern and are older than the
# number of days defined on the following section
#
# usage: log-discard-old.sh folder "pat1:pat2:...:patn"
# example: log-discard-old.sh /home/mms "*.dbg:*.log"
#
# The script should be called periodically from crontab
# This is an example crontab entry for AHX10
# 0 0 * * * root /media/realroot/home/dlog/frontrunnerV3/bin/log-discard-old.sh /media/realroot/home/dlog "*.dbg:*.log:*.dbg.zip:*.txt"
########################################################

########################################################
# TIME TO CONSIDER FILE TOO OLD AND DELETE IT
# DEFAULT VALUE
discard="+180" # NUMBER OF DAYS - ALWAYS use + before
########################################################

if [ ! "$#" -ge 2 ];then
  echo "BAD Parameters"
  echo "Inform folder and match pattern separated by :"
  echo "Example: $0 /home/mms \"*.log:*.zip\" days-until-delete" 
  echo "last parameter is optional"
  exit 1
fi

if [ "$#" -eq 3 ]; then
    discard="+$3"
    echo "DISCARD =$discard"
fi

folder=$1

if [ ! -d "$1" ]; then
  echo "ERROR!!!!"
  echo "Folder $1 does not exist"
  exit 1
fi


result=`awk -v string="$2" -v disc="$discard"  -v fold="$folder" 'BEGIN{  
    search=":";

    n=split(string,array,search);
    for (i=1;i<=n;i++) {
#####################################################################################
# IF you want to move the files instead of deleting them, modify the following line
#####################################################################################
        printf("nice -n 19 ionice -c 3 find %s -mtime %s -name \"%s\" -print -exec sleep 0.1 \\\; -delete;",fold, disc, array[i]);
    } 

}'`


set -x
eval $result
set +x

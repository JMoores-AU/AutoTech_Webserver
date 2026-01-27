#!/bin/sh

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


date=`date +%Y%m%d%H%M%S`
directory="/var/log/frontrunner/logs"

if [ ! -d "$directory" ]; then
    mkdir -p "$directory"
    find "$directory" -print0 -exec chmod -f 766 {} + > /dev/null 2>&1
    chmod -f 776 "$directory"
fi
cd $directory
date="${directory}/iostat_$date.txt"
echo "Filename=$date"
#Sample every 5 seconds. 720 samples = 1 hour
nohup iostat 5 720 -k -t > $date



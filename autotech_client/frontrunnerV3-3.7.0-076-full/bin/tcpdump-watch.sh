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


if [ $# != 2 ]
then
        echo "Wrong Parameters"
        echo "usage: tcpdump.sh interface folder"
        exit
fi

EXEC="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

interface=$1
dir=$2

if [ -f /var/run/tcpdump.pid ]
then
    echo PID file exists
    process=`cat /var/run/tcpdump.pid| sed 's/^ *//g'`
    echo process=$process
    ps=`ps -o pid -p $process  --no-headers| sed 's/^ *//g' ` 
    echo PS=$ps
    echo size=${#ps}
    if [  ${#ps} == ${#process} ] &&  [ $process -eq $ps ]
    then
       echo PID is running
    else
       echo PID not running
       $EXEC/tcpdump.sh $interface $dir
    fi
else
       echo PID not running
       $EXEC/tcpdump.sh $interface $dir
fi

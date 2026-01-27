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


if [ $# != 2 ]
then
    echo "Wrong Parameters"
    echo "usage: tcpdump.sh interface folder"
    exit
fi

interface=$1
dir=$2
nice -n 10 ionice -c2 -n7 /usr/sbin/tcpdump  -z gzip -Z tcpdump -s2048 -nnn -i $interface not tcp -G 600 -W 1000  -w $dir/tcpdump_%Y-%m-%d_%H%M%S.pcap &
echo $! >/var/run/tcpdump.pid


#! /bin/sh
# mkcard.sh v0.5
# (c) Copyright 2009 Graeme Gregory <dp@xora.org.uk>
# Licensed under terms of GPLv2
#
# Parts of the procudure base on the work of Denys Dmytriyenko
# http://wiki.omap.com/index.php/MMC_Boot_Format

export LC_ALL=C

if [ $# -ne 2 ]; then
    echo "Usage: $0 <drive> <image>"
    echo example: "$0 /dev/sdb mmsi-debian-image-2012-10.2.tar.xz"
    exit 1;
fi
DRIVE=$1
IMGFILE=$2

if [ ! -f "$IMGFILE" ];
then
    echo "$IMGFILE: FILE does not Exist"
    exit 1;
fi

if [ ! -b "$DRIVE" ];
then
    echo "$DRIVE: Not a block device"
    exit 1;
fi

umount `echo $DRIVE`1
umount `echo $DRIVE`2
umount `echo $DRIVE`3
umount `echo $DRIVE`4
umount `echo $DRIVE`5

dd if=/dev/zero of=$DRIVE bs=1024 count=1024

SIZE=`fdisk -l $DRIVE | grep Disk | grep bytes | awk '{print $5}'`

echo DISK SIZE - $SIZE bytes

{
echo 20,,,*
} | sfdisk  $DRIVE

sleep 1

mkdir /mnt

mkfs.ext2 -j `echo $DRIVE`1
if [ $? -eq 0 ]; then
    echo Format Success!
    mount `echo $DRIVE`1 /mnt
    if [ $? -ne 0 ]; then
          echo ERROR MOUNT
      exit 1
    fi
    echo Copying Image Files
    DIR=`pwd`
    cd /mnt
    tar xvf $DIR/$IMGFILE 
    echo Prepare for CHROOT
    mount -t proc none /mnt/proc
    mount -o bind /dev /mnt/dev/
    echo Execute CHROOT
    chroot /mnt /usr/sbin/grub-install --recheck --no-floppy /dev/sdb
    cd -
    sleep 5
    umount /mnt/dev
    umount /mnt/proc
    umount /mnt
    echo SUCCESS! IMAGE SAVED
fi


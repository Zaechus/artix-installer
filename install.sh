#!/bin/sh

# preinstall
yes | sudo pacman -Sy --needed python

# install
while :
do
    sudo fdisk -l
    printf '\nDisk to install to (e.g. /dev/sda): ' && read MY_DISK
    if test -b "$MY_DISK"; then
        echo $MY_DISK
        break
    fi
done

sudo python src/install.py $MY_DISK
sudo cp src/iamchroot.py /mnt/root/

# chroot
sudo artix-chroot /mnt /bin/bash -c "python /root/iamchroot.py $MY_DISK && exit"

printf '\n`sudo artix-chroot /mnt /bin/bash` back into the system to make any final changes.\n\nYou may now poweroff.\n'

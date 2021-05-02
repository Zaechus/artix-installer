#!/bin/sh

# preinstall
sudo rfkill unblock wifi
sudo ip link set wlan0 up
printf "\n> scan wifi\n> services\n> agent on\n> connect wifi_NAME\n> quit\n"
sudo connmanctl
yes | sudo pacman -Sy --needed python

# install
sudo sfdisk -l
printf "\nDisk to install to (e.g. /dev/sda): " && read MY_DISK && echo $MY_DISK
sudo python src/install.py $MY_DISK
sudo cp src/iamchroot.py /mnt/root/

# chroot
sudo artix-chroot /mnt /bin/bash -c "python /root/iamchroot.py $MY_DISK && exit"

# clean up
sudo umount -R /mnt
sudo cryptsetup close /dev/mapper/cryptroot
sudo cryptsetup close /dev/mapper/cryptswap
printf "\nYou may now poweroff.\n"

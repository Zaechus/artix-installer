#!/bin/sh

# preinstall
rfkill unblock wifi
ip link set wlan0 up
echo "\n> scan wifi\n> services\n> agent on\n> connect wifi_NAME\n> quit"
connmanctl
yes | pacman -Sy --needed python

# install
python src/install.py
cp src/iamchroot.py /mnt/root/

# chroot
artix-chroot /mnt /bin/bash -c "python /root/iamchroot.py && exit"

# clean up
umount -R /mnt
cryptsetup close /dev/mapper/cryptroot
cryptsetup close /dev/mapper/ctyptswap
echo "You may now poweroff."

#!/bin/sh

# preinstall
sudo rfkill unblock wifi
sudo ip link set wlan0 up
echo "\n> scan wifi\n> services\n> agent on\n> connect wifi_NAME\n> quit"
sudo connmanctl
yes | sudo pacman -Sy --needed python

# install
sudo python src/install.py
sudo cp src/iamchroot.py /mnt/root/

# chroot
sudo artix-chroot /mnt /bin/bash -c "python /root/iamchroot.py && exit"

# clean up
sudo umount -R /mnt
sudo cryptsetup close /dev/mapper/cryptroot
sudo cryptsetup close /dev/mapper/ctyptswap
echo "You may now poweroff."

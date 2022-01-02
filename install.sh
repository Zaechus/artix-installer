#!/bin/sh
#
# A simple installer for Artix Linux
#
# Copyright (c) 2022 Maxwell Anderson
#
# This file is part of artix-installer.
#
# artix-installer is free software: you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# artix-installer is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with artix-installer. If not, see <https://www.gnu.org/licenses/>.

confirm_password () {
    local pass1="a"
    local pass2="b"
    until [[ $pass1 == $pass2 && $pass2 ]]; do
        printf "$1: " >&2 && read -rs pass1
        printf "\n" >&2
        printf "confirm $1: " >&2 && read -rs pass2
        printf "\n" >&2
    done
    echo $pass2
}

confirm_name () {
    local name1="a"
    local name2="b"
    until [[ $name1 == $name2 && $name2 ]]; do
        printf "$1: " >&2 && read name1
        printf "confirm $1: " >&2 && read name2
    done
    echo $name2
}

# Load keymap
sudo loadkeys us

# Check boot mode
[[ ! -d /sys/firmware/efi ]] && printf "Not booted in UEFI mode. Aborting..." && exit 1

# Choose disk
while :
do
    sudo fdisk -l
    printf "\nDisk to install to (e.g. /dev/sda): " && read my_disk
    [[ -b $my_disk ]] && break
done

part1="$my_disk"1
part2="$my_disk"2
part3="$my_disk"3
if [[ $my_disk == *"nvme"* ]]; then
    part1="$my_disk"p1
    part2="$my_disk"p2
    part3="$my_disk"p3
fi

# Swap size
until [[ $swap_size =~ ^[0-9]+$ && (($swap_size -gt 0)) && (($swap_size -lt 97)) ]]; do
    printf "Size of swap partition in GiB (4): " && read swap_size
    [[ ! $swap_size ]] && swap_size=4
done

# Choose filesystem
until [[ $my_fs == "btrfs" || $my_fs == "ext4" ]]; do
    printf "Filesystem (btrfs/ext4): " && read my_fs
    [[ ! $my_fs ]] && my_fs="btrfs"
done

root_part=$part3
[[ $my_fs == "ext4" ]] && root_part=$part2

# Encrypt or not
printf "Encrypt? (Y/n): " && read encrypted
[[ ! $encrypted ]] && encrypted="y"

my_root="/dev/mapper/root"
my_swap="/dev/mapper/swap"
if [[ $encrypted == "n" ]]; then
    my_root=$part3
    my_swap=$part2
    [[ $my_fs == "ext4" ]] && my_root=$part2 && my_swap="/dev/MyVolGrp/swap"
else
    cryptpass=$(confirm_password "encryption password")
fi

# Timezone
until [[ -f /usr/share/zoneinfo/$region_city ]]; do
    printf "Region/City (e.g. 'America/Denver'): " && read region_city
    [[ ! $region_city ]] && region_city="America/Denver"
done

# Host
my_hostname=$(confirm_name "hostname")

# Users
root_password=$(confirm_password "root password")

my_username=$(confirm_name "username")
user_password=$(confirm_password "user password")

installvars () {
    echo my_disk=$my_disk part1=$part1 part2=$part2 part3=$part3 \
        swap_size=$swap_size my_fs=$my_fs root_part=$root_part encrypted=$encrypted my_root=$my_root my_swap=$my_swap \
        region_city=$region_city my_hostname=$my_hostname my_username=$my_username \
        cryptpass=$cryptpass root_password=$root_password user_password=$user_password
}

printf "\nDone with configuration. Installing...\n\n"

# Install
sudo $(installvars) sh src/installer.sh

# Chroot
sudo cp src/iamchroot.sh /mnt/root/ && \
    sudo $(installvars) artix-chroot /mnt /bin/bash -c 'sh /root/iamchroot.sh; rm /root/iamchroot.sh; exit' && \
    printf '\n`sudo artix-chroot /mnt /bin/bash` back into the system to make any final changes.\n\nYou may now poweroff.\n'

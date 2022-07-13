#!/bin/sh -e
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

# Partition disk
if [[ $my_fs == "ext4" ]]; then
    layout=",,V"
    fs_pkgs="lvm2 lvm2-$my_init"
elif [[ $my_fs == "btrfs" ]]; then
    layout=",$(echo $swap_size)G,S\n,,"
    fs_pkgs="btrfs-progs"
fi
[[ $encrypted == "y" ]] && fs_pkgs+=" cryptsetup cryptsetup-$my_init"

printf "label: gpt\n,550M,U\n$layout\n" | sfdisk $my_disk

# Format and mount partitions
if [[ $encrypted == "y" ]]; then
    yes $cryptpass | cryptsetup -q luksFormat $root_part
    yes $cryptpass | cryptsetup open $root_part root

    if [[ $my_fs == "btrfs" ]]; then
        yes $cryptpass | cryptsetup -q luksFormat $part2
        yes $cryptpass | cryptsetup open $part2 swap
    fi
fi

mkfs.fat -F 32 $part1

if [[ $my_fs == "ext4" ]]; then
    # Setup LVM
    pvcreate $my_root
    vgcreate MyVolGrp $my_root
    lvcreate -L $(echo $swap_size)G MyVolGrp -n swap
    lvcreate -l 100%FREE MyVolGrp -n root

    mkfs.ext4 /dev/MyVolGrp/root

    mount /dev/MyVolGrp/root /mnt
elif [[ $my_fs == "btrfs" ]]; then
    mkfs.btrfs $my_root

    # Create subvolumes
    mount $my_root /mnt
    btrfs subvolume create /mnt/root
    btrfs subvolume create /mnt/home
    umount -R /mnt

    # Mount subvolumes
    mount -t btrfs -o compress=zstd,subvol=root $my_root /mnt
    mkdir /mnt/home
    mount -t btrfs -o compress=zstd,subvol=home $my_root /mnt/home
fi

mkswap $my_swap
mkdir /mnt/boot
mount $part1 /mnt/boot

[[ $(grep 'vendor' /proc/cpuinfo) == *"Intel"* ]] && ucode="intel-ucode"
[[ $(grep 'vendor' /proc/cpuinfo) == *"Amd"* ]] && ucode="amd-ucode"

# Install base system and kernel
basestrap /mnt base base-devel $my_init elogind-$my_init $fs_pkgs efibootmgr grub $ucode dhcpcd wpa_supplicant connman-$my_init
basestrap /mnt linux linux-firmware linux-headers mkinitcpio
fstabgen -U /mnt > /mnt/etc/fstab

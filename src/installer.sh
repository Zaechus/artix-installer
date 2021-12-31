#!/bin/sh

source installvars

# Partition disk
yes | pacman -Sy --needed parted

fs_pkgs="cryptsetup btrfs-progs"
[[ $my_fs == "ext4" ]] && fs_pkgs="cryptsetup lvm2 lvm2-openrc"

parted -s $my_disk mklabel gpt \
    mkpart fat32 0% 550MiB \
    set 1 esp on

if [[ $my_fs == "ext4" ]]; then
    parted -s $my_disk \
        mkpart ext4 550MiB 100% \
        set 2 lvm on
else if [[ $my_fs == "btrfs" ]]; then
    parted -s $my_disk \
        mkpart linux-swap 550MiB $((1+$swap_size*1024))MiB \
        mkpart btrfs $((1+$swap_size*1024))MiB 100% \
        set 2 swap on
fi

# Format and mount partitions
if [[ $encrypted != "n" ]]; then
    printf $cryptpass | cryptsetup -q luksFormat --type luks1 $root_part
    printf $cryptpass | cryptsetup open $root_part root

    if [[ $my_fs == "btrfs" ]]; then
        printf $cryptpass | cryptsetup -q luksFormat $part2
        printf $cryptpass | cryptsetup open $part2 swap
    fi
fi

mkfs.fat -F 32 $part1

if [[ $my_fs == "ext4" ]]; then
    # Setup LVM
    pvcreate $my_root
    vgcreate MyVolGrp $my_root
    lvcreate -L $swap_sizeG MyVolGrp -n swap
    lvcreate -l 100%FREE MyVolGrp -n root

    mkfs.ext4 /dev/MyVolGrp/root

    mount /dev/MyVolGrp/root /mnt
else if [[ $my_fs == "btrfs" ]]; then
    mkfs.btrfs $my_root

    # Create subvolumes
    mount $my_root /mnt
    btrfs subvolume create /mnt/root
    btrfs subvolume create /mnt/snapshots
    btrfs subvolume create /mnt/home
    umount -R /mnt

    # Mount subvolumes
    mount -t btrfs -o compress=zstd,subvol=root $my_root /mnt
    mkdir /mnt/.snapshots
    mkdir /mnt/home
    mount -t btrfs -o compress=zstd,subvol=snapshots $my_root /mnt/.snapshots
    mount -t btrfs -o compress=zstd,subvol=home $my_root /mnt/home
fi

mkswap $my_swap
mkdir /mnt/boot
mount $part1 /mnt/boot

# Install base system and kernel
basestrap /mnt base base-devel openrc elogind-openrc $fs_pkgs efibootmgr grub $ucode zsh dhcpcd wpa_supplicant connman-openrc
basestrap /mnt linux linux-firmware linux-headers mkinitcpio
fstabgen -U /mnt >> /mnt/etc/fstab

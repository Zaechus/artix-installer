#!/bin/sh

confirm_password () {
    local pass1="a"
    local pass2="b"
    until [[ $pass1 == $pass2 ]]; do
        printf "$1: " >&2 && read -rs pass1
        printf "\n" >&2
        printf "confirm $1: " >&2 && read -rs pass2
        printf "\n" >&2
    done
    echo $pass2
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
if [[ "nvme" == *"$my_disk"* ]]; then
    part1="$my_disk"p1
    part2="$my_disk"p2
    part3="$my_disk"p3
fi

# Swap size
printf "Size of swap partition in GiB (4): " && read swap_size
[[ ! -z swap_size ]] && swap_size=4

# Choose filesystem
until [[ $my_fs == "btrfs" || $my_fs == "ext4" ]]; do
    printf "Filesystem (btrfs/ext4): " && read my_fs
    [[ ! -z my_fs ]] && my_fs="btrfs"
done

root_part=$part3
[[ $my_fs == "ext4" ]] && root_part=$part2

# Encrypt or not
printf "Encrypt? (Y/n): " && read encrypted
[[ ! -z encrypted ]] && encrypted="y"

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
printf "Region/City (e.g. 'America/Denver'): " && read region_city
[[ ! -z region_city ]] && region_city="America/Denver"

# Host
my_hostname=$(confirm_password "hostname")

# Microcode
printf "Microcode (intel/amd/both):" && read ucode
case ucode in
    intel)
        ucode="intel-ucode"
        ;;
    amd)
        ucode="amd-ucode"
        ;;
    *)
        ucode="intel-ucode amd-ucode"
        ;;
esac

# Users
root_password=$(confirm_password "root password")

my_username=$(confirm_password "username")
user_password=$(confirm_password "user password")

# Install
sudo sh src/installer.sh

# Chroot
sudo cp src/iamchroot.sh /mnt/root/
sudo artix-chroot /mnt /bin/bash -c 'sh /root/iamchroot.sh; rm /root/iamchroot.sh; exit'

printf '\n`sudo artix-chroot /mnt /bin/bash` back into the system to make any final changes.\n\nYou may now poweroff.\n'

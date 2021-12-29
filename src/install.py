#!/usr/bin/env python

import sys

from subprocess import run, check_output

def make_password(s):
    print("\nPasswords should not contain ' or \"\n")
    print(s, end="")

    while True:
        password = input("Password: ").strip()
        second = input("Repeat password: ").strip()

        if password == second and len(password) > 1:
            return password

print("\nInstalling Artix Linux...\n")

# Check boot mode
if len(check_output("ls /sys/firmware/efi/efivars", shell=True)) < 8:
    print("\nNot booted in UEFI mode. Aborting...")
    sys.exit()

# Load keymap
run(f"loadkeys us", shell=True)

# Partition disk
disk = sys.argv[1]
part1 = f"{disk}1"
part2 = f"{disk}2"
part3 = f"{disk}3"
if "nvme" in disk:
    part1 = f"{disk}p1"
    part2 = f"{disk}p2"
    part3 = f"{disk}p3"
run("yes | pacman -S --needed parted", shell=True)

swap_size = input("\nSize of swap partition (4GiB): ").strip()
swap_size = "".join([x for x in swap_size if x.isdigit()])
if swap_size == "":
    swap_size = "4"
swap_size = int(swap_size)

fs_type = input(
    "\nFilesystem:"
    "\n(1)  ext4"
    "\n(2+) Btrfs\n: "
).strip()
root_part = part2
fs_pkgs = ""
if fs_type == "1":
    fs_type = "ext4"
    fs_pkgs = "cryptsetup lvm2 lvm2-openrc"
else:
    fs_type = "btrfs"
    root_part = part3
    fs_pkgs = "cryptsetup btrfs-progs"

run(f"""parted -s {disk} mklabel gpt \\
mkpart fat32 0% 550MiB \\
set 1 esp on""", shell=True)

if fs_type == "ext4":
    run(f"""parted -s {disk} \\
mkpart ext4 550MiB 100%""", shell=True)
elif fs_type == "btrfs":
    run(f"""parted -s {disk} \\
mkpart linux-swap 550MiB {1+swap_size*1024}MiB \\
mkpart btrfs {1+swap_size*1024}MiB 100% \\
set 2 swap on""", shell=True)

# Setup encrypted partitions
cryptpass = ""

if fs_type == "ext4" or fs_type == "btrfs":
    cryptpass = make_password("\nSetting encryption password...\n")

    run(f"echo '{cryptpass}' | cryptsetup -q luksFormat --type luks1 {root_part}", shell=True)
    run(f"yes '{cryptpass}' | cryptsetup open {root_part} cryptroot", shell=True)

if fs_type == "btrfs":
    run(f"echo '{cryptpass}' | cryptsetup -q luksFormat {part2}", shell=True)
    run(f"yes '{cryptpass}' | cryptsetup open {part2} cryptswap", shell=True)

# Format partitions and mount
run(f"mkfs.fat -F 32 {part1}", shell=True)

if fs_type == "ext4":
    # Setup LVM
    run("pvcreate /dev/mapper/cryptroot", shell=True)
    run("vgcreate MyVolGrp /dev/mapper/cryptroot", shell=True)
    run(f"lvcreate -L {swap_size}G MyVolGrp -n swap", shell=True)
    run("lvcreate -l 100%FREE MyVolGrp -n root", shell=True)

    run("mkswap /dev/MyVolGrp/swap", shell=True)
    run("mkfs.ext4 /dev/MyVolGrp/root", shell=True)

    run("mount /dev/MyVolGrp/root /mnt", shell=True)
elif fs_type == "btrfs":
    run("mkswap /dev/mapper/cryptswap", shell=True)
    run("mkfs.btrfs /dev/mapper/cryptroot", shell=True)

    # Create subvolumes
    run("mount /dev/mapper/cryptroot /mnt", shell=True)
    run("btrfs subvolume create /mnt/root", shell=True)
    run("btrfs subvolume create /mnt/snapshots", shell=True)
    run("btrfs subvolume create /mnt/home", shell=True)
    run("umount -R /mnt", shell=True)

    # Mount subvolumes
    run("mount -t btrfs -o compress=zstd,subvol=root /dev/mapper/cryptroot /mnt", shell=True)
    run("mkdir /mnt/.snapshots", shell=True)
    run("mkdir /mnt/home", shell=True)
    run("mount -t btrfs -o compress=zstd,subvol=snapshots /dev/mapper/cryptroot /mnt/.snapshots", shell=True)
    run("mount -t btrfs -o compress=zstd,subvol=home /dev/mapper/cryptroot /mnt/home", shell=True)

run("mkdir /mnt/boot", shell=True)
run(f"mount {part1} /mnt/boot", shell=True)

# Install base system and kernel
run(f"basestrap /mnt base base-devel openrc elogind-openrc {fs_pkgs} zsh python dhcpcd wpa_supplicant connman-openrc", shell=True)
run("basestrap /mnt linux linux-firmware linux-headers mkinitcpio", shell=True)
run("fstabgen -U /mnt >> /mnt/etc/fstab", shell=True)

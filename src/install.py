#!/usr/bin/env python

import sys

from subprocess import run, check_output

def make_password(s):
    print(s, end="")

    while True:
        password = input("Password: ").strip()
        second = input("Repeat password: ").strip()

        if password == second and len(password) > 1:
            return password

print("Installing Artix Linux...\n")

# Check boot mode
if len(check_output("ls /sys/firmware/efi/efivars", shell=True)) < 8:
    print("\nNot booted in UEFI mode. Aborting...")
    sys.exit()

# Load keymap
keymap = input("\nKeymap (us): ").strip()
if len(keymap) < 2:
    keymap = "us"
run(f"loadkeys {keymap}", shell=True)

# Partition disk
disk = ""
run("yes | pacman -Sy --needed parted", shell=True)
while True:
    while True:
        run("sfdisk -l", shell=True)
        disk = input("\nDisk to install to (e.g. `/dev/sda`): ").strip()
        if len(disk) > 0:
            break

    erase = input("Would you like to erase the contents of the disk? (y/N): ").strip()
    if erase == "y":
        run(f"dd bs=4096 if=/dev/zero iflag=nocache of={disk} oflag=direct status=progress", shell=True)

    swap_size = input("Size of swap partition (4GiB): ").strip()
    swap_size = int("".join([x for x in swap_size if x.isdigit()]))
    if swap_size == "":
        swap_size = 4

    run(f"""parted -s {disk} mktable gpt \\
mkpart primary boot fat32 0% 1GiB \\
mkpart primary swap linux-swap 1GiB {1+swap_size}GiB \\
mkpart primary root btrfs {1+swap_size}GiB 100% \\
align-check optimal 1 \\
align-check optimal 2 \\
align-check optimal 3""", shell=True)

    choice = input("Would you like to manually edit partitions? (y/N): ").strip()
    if choice == "y":
        run(f"cfdisk {disk}", shell=True)

    run(f"sfdisk -l {disk}", shell=True)
    choice = input(f"\nInstall on {disk}? (y/N): ").strip()
    if choice == "y":
        break

# Setup encrypted partitions
run("cryptsetup close /dev/mapper/cryptroot", shell=True),
run("cryptsetup close /dev/mapper/cryptswap", shell=True),

luks_options = input("Additional cryptsetup options (e.g. `--type luks1`): ").strip()

cryptpass = make_password("\nSetting encryption password...\n")

run(f"echo '{cryptpass}' | cryptsetup -q luksFormat {luks_options} {disk}3", shell=True)
run(f"echo '{cryptpass}' | cryptsetup -q luksFormat {disk}2", shell=True)

run(f"yes '{cryptpass}' | cryptsetup open {disk}3 cryptroot", shell=True)
run(f"yes '{cryptpass}' | cryptsetup open {disk}2 cryptswap", shell=True)

# Format partitions
run("mkswap /dev/mapper/cryptswap", shell=True)
run(f"mkfs.fat -F 32 {disk}1", shell=True)
run("mkfs.btrfs /dev/mapper/cryptroot", shell=True)

# Create subvolumes
run("umount -R /mnt/boot/efi", shell=True)
run("umount -R /mnt", shell=True)
run("rm -rf /mnt", shell=True)
run("mkdir /mnt", shell=True)
run("mount /dev/mapper/cryptroot /mnt", shell=True)
run("btrfs subvolume create /mnt/@", shell=True)
run("btrfs subvolume create /mnt/@snapshots", shell=True)
run("btrfs subvolume create /mnt/@home", shell=True)
run("umount -R /mnt", shell=True)

# Mount subvolumes and boot
run("mount -o compress=zstd,subvol=@ /dev/mapper/cryptroot /mnt", shell=True)
run("mkdir /mnt/.snapshots", shell=True)
run("mkdir /mnt/home", shell=True)
run("mount -o compress=zstd,subvol=@snapshots /dev/mapper/cryptroot /mnt/.snapshots", shell=True)
run("mount -o compress=zstd,subvol=@home /dev/mapper/cryptroot /mnt/home", shell=True)
run("mkdir -p /mnt/boot/efi", shell=True)
run(f"mount {disk}1 /mnt/boot/efi", shell=True)

# Install base system and kernel
run("basestrap /mnt base base-devel openrc cryptsetup btrfs-progs python neovim parted", shell=True)
run("basestrap /mnt linux linux-firmware linux-headers", shell=True)
run("fstabgen -U /mnt >> /mnt/etc/fstab", shell=True)

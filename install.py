#!/usr/bin/env python

import sys

from subprocess import run, check_output

def make_password(s):
    print(s, end="")

    while True:
        password = input("Password: ").strip()
        second = input("Repeat password: ").strip()

        if password == second and len(password) > 1:
            break

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
while True:
    while True:
        run("fdisk -l", shell=True)
        disk = input("\nDisk to install to (e.g. `/dev/sda`): ").strip()
        if len(disk) > 0:
            break
    input('''Partitioning:
    gpt
    1 New 1G    'EFI System'
    2 New 4G    'Linux swap'
    3 New *FREE 'Linux filesystem'
    Write yes Quit
    [ENTER] ''')
    run(f"cfdisk {disk}", shell=True)
    
    choice = input(f"\nInstall on '{disk}'? (y/N): ").strip()
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
run("basestrap /mnt base base-devel openrc cryptsetup btrfs-progs python neovim", shell=True)
run("basestrap /mnt linux linux-firmware linux-headers", shell=True)
run("fstabgen -U /mnt >> /mnt/etc/fstab", shell=True)

# Finish
run("cp install.py /mnt/root/", shell=True)
run("cp iamchroot.py /mnt/root/", shell=True)
print("\nRun `artix-chroot /mnt /bin/bash`")
print("\nRun `python /root/iamchroot.py` once you are in the new system.")

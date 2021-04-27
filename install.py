#!/usr/bin/env python

import sys

from subprocess import run, check_output

print("Installing Artix Linux with LUKS and Btrfs...\n")

# Check boot mode
if len(check_output("ls /sys/firmware/efi/efivars", shell=True)) < 8:
    print("\nNot booted in UEFI mode, aborting...")
    sys.exit()

# Load keymap
print("\nKeymap", end=" (us): ")
keymap = input().strip()
if len(keymap) < 2:
    keymap = "us"
run(f"loadkeys {keymap}", shell=True)

# Partition disk
disk = ""
while True:
    while True:
        run("fdisk -l", shell=True)
        print("\nDisk to install to", end=": ")
        disk = input().strip()
        if len(disk) > 0:
            break
    print('''Partition scheme:
        gpt
        1 New 1G 'EFI System'
        2 New 4G 'Linux swap'
        3 New *FREE 'Linux filesystem'
        Write yes Quit
    ''')
    input()
    run(f"cfdisk {disk}", shell=True)
    
    print(f"\nInstall on '{disk}'?", end=" (y/N): ")
    choice = input().strip()
    if len(choice) > 0 and choice[0] == "y":
        break

# Setup encrypted partitions
cryptpass = ""
while True:
    print("Encryption password", end=": ")
    cryptpass = input().strip()
    print("Repeat password", end=": ")
    second = input().strip()

    if cryptpass == second and len(cryptpass) > 1:
        break
run(f"printf '{cryptpass}' > /cryptpass.txt", shell=True)
run("cryptsetup close /dev/mapper/cryptroot", shell=True),
run("cryptsetup close /dev/mapper/cryptswap", shell=True),
   
run(f"yes YES | cryptsetup luksFormat {disk}3 /cryptpass.txt", shell=True)
run(f"yes YES | cryptsetup luksFormat {disk}2 /cryptpass.txt", shell=True)

run("rm /cryptpass.txt", shell=True)

run(f"yes '{cryptpass}' | cryptsetup open {disk}3 cryptroot", shell=True)
run(f"yes '{cryptpass}' | cryptsetup open {disk}2 cryptswap", shell=True)

# Format partitions
run("mkswap /dev/mapper/cryptswap", shell=True)
run(f"mkfs.fat -F 32 {disk}1", shell=True)
run("mkfs.btrfs /dev/mapper/cryptroot", shell=True)

# Create subvolumes
run("umount -R /mnt/boot", shell=True)
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
run("mkdir /mnt/boot", shell=True)
run(f"mount {disk}1 /mnt/boot", shell=True)

# Install base system and kernel
run("basestrap /mnt base base-devel openrc cryptsetup btrfs-progs python neovim", shell=True)
run("basestrap /mnt linux linux-firmware linux-headers", shell=True)
run("fstabgen -U /mnt >> /mnt/etc/fstab", shell=True)

# Finish
run("cp preinstall.sh /mnt/root/", shell=True)
run("cp install.py /mnt/root/", shell=True)
run("cp iamchroot.py /mnt/root/", shell=True)
print("\nRun `artix-chroot /mnt /bin/bash`")
print("\nRun `python /root/iamchroot.py` once you are in the new system.")

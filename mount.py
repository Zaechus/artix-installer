#!/usr/bin/env python

import sys

from subprocess import run, check_output

disk = ""
while True:
    while True:
        run("fdisk -l", shell=True)
        print("\nDisk to mount", end=": ")
        disk = input().strip()
        if len(disk) > 0:
            break
    break

# Setup encrypted partitions
print("Encryption password", end=": ")
cryptpass = input().strip()

run(f"yes '{cryptpass}' | cryptsetup open {disk}3 cryptroot", shell=True)
run(f"yes '{cryptpass}' | cryptsetup open {disk}2 cryptswap", shell=True)

# Mount subvolumes and boot
run("mount -o compress=zstd,subvol=@ /dev/mapper/cryptroot /mnt", shell=True)
run("mount -o compress=zstd,subvol=@snapshots /dev/mapper/cryptroot /mnt/.snapshots", shell=True)
run("mount -o compress=zstd,subvol=@home /dev/mapper/cryptroot /mnt/home", shell=True)
run(f"mount {disk}1 /mnt/boot/efi", shell=True)

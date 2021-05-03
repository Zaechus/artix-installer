#!/usr/bin/env python

import sys

from subprocess import run

disk = sys.argv[1]

run("sudo umount -Rq /mnt/boot/efi", shell=True)
run("sudo umount -Rq /mnt", shell=True)
run("sudo lvchange -an /dev/MyVolGrp/swap", shell=True)
run("sudo lvchange -an /dev/MyVolGrp/root", shell=True)
run("sudo lvremove /dev/MyVolGrp/swap", shell=True)
run("sudo lvremove /dev/MyVolGrp/root", shell=True)
run("sudo vgremove MyVolGrp", shell=True)
run("sudo cryptsetup -q close /dev/mapper/cryptroot", shell=True),
run("sudo cryptsetup -q close /dev/mapper/cryptswap", shell=True),
run("sudo rm -rf /mnt", shell=True)
run("sudo mkdir /mnt", shell=True)

cryptpass = input("Encryption password: ").strip()

run(f"yes '{cryptpass}' | sudo cryptsetup open {disk}3 cryptroot", shell=True)
run(f"yes '{cryptpass}' | sudo cryptsetup open {disk}2 cryptswap", shell=True)

run("sudo mount -o compress=zstd,subvol=@ /dev/mapper/cryptroot /mnt", shell=True)
run("sudo mount -o compress=zstd,subvol=@snapshots /dev/mapper/cryptroot /mnt/.snapshots", shell=True)
run("sudo mount -o compress=zstd,subvol=@home /dev/mapper/cryptroot /mnt/home", shell=True)
run(f"sudo mount {disk}1 /mnt/boot/efi", shell=True)

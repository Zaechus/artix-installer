#!/bin/sh

umount -Rq /mnt/boot/efi
umount -Rq /mnt
lvchange -an /dev/MyVolGrp/swap
lvchange -an /dev/MyVolGrp/root
lvremove /dev/MyVolGrp/swap
lvremove /dev/MyVolGrp/root
vgremove MyVolGrp
cryptsetup -q close /dev/mapper/cryptroot
cryptsetup -q close /dev/mapper/cryptswap
rm -rf /mnt
mkdir /mnt

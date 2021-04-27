#!/usr/bin/env python

import sys

from signal import signal, SIGINT
from subprocess import run, check_output

def handler(recv, frame):
    sys.exit()

signal(SIGINT, handler)

# Input vars
print("Region", end=": ")
region = input().strip()
print("City", end=": ")
city = input().strip()

disk = ""
while True:
    run("fdisk -l", shell=True)
    print("\nDisk to install to", end=": ")
    disk = input().strip()
    if len(disk) > 0:
        break

# Boring stuff you should probably do
run(f"ln -sf /usr/share/zoneinfo/{region}/{city} /etc/localtime", shell=True)
run("hwclock --systohc", shell=True)

# Configure pacman
run("nvim /etc/pacman.conf", shell=True)
run("printf '\nkeyserver hkp://keyserver.ubuntu.com\n' >> /etc/pacman.d/gnupg/gpg.conf", shell=True)
run("pacman-key --populate artix", shell=True)

run("yes | pacman -Syu neofetch", shell=True)

# Localization
print("Uncomment locales. [ENTER]", end=" ")
input()
run("nvim /etc/locale.gen", shell=True)
run("locale-gen", shell=True)
print("LANG", end="=")
lang = input().strip()
if len(lang) < 2:
    lang = "en_US.UTF-8"

print("KEYMAP", end="=")
keymap = input().strip()
if len(keymap) < 2:
    keymap = "us"

run(f"printf 'LANG={lang}\n' > /etc/locale.conf", shell=True)
run(f"printf 'KEYMAP={keymap}\n' > /etc/vconsole.conf", shell=True)

# Host stuff
hostname = ""
while True:
    print("Hostname", end=": ")
    hostname = input().strip()
    if len(hostname) > 1:
        break
run(f"printf '{hostname}\n' > /etc/hostname", shell=True)
run(f"printf '\n127.0.0.1\tlocalhost\n::1\t\tlocalhost\n127.0.1.1\t{hostname}.localdomain\t{hostname}\n' > /etc/hosts", shell=True)

# Install boot loader
run("yes | pacman -S efibootmgr grub amd-ucode intel-ucode", shell=True)

disk3uuid = str(check_output(f"sudo blkid {disk}3 -o value -s UUID", shell=True).strip())[1:]

run(f"printf '\n#cryptdevice=UUID={disk3uuid}:cryptroot root=/dev/mapper/cryptroot rootflags=subvol=@ rw initrd=amd-ucode.img initrd=intel-ucode.img initrd=initramfs-linux.img' >> /etc/default/grub", shell=True)
run("nvim /etc/default/grub", shell=True)
run("grub-install --target=x86_64-efi --efi-directory=/boot/efi --bootloader-id=GRUB --removable --recheck", shell=True)
run("grub-mkconfig -o /boot/grub/grub.cfg", shell=True)

# Local.start
run(f"printf 'rfkill unblock wifi\nneofetch >| /etc/issue\n' > /etc/local.d/local.start", shell=True)
run("chmod +x /etc/local.d/local.start", shell=True)

# Add default user
run("yes | pacman -S zsh", shell=True)
run("chsh -s /bin/zsh", shell=True)

print("\nChanging root password...")
password = ""
while True:
    print("Password", end=": ")
    password = input().strip()
    print("Repeat password", end=": ")
    second = input().strip()
    
    if password == second and len(password) > 1:
        break
run(f"yes '{password}' | passwd", shell=True)

run("rm /etc/skel/.bash*", shell=True)
run("useradd -D -s /bin/zsh", shell=True)

username = ""
while True:
    print("Username", end=": ")
    username = input().strip()
    if len(username) > 1:
        break
run(f"useradd -m {username}", shell=True)

password = ""
while True:
    print("Password", end=": ")
    password = input().strip()
    print("Repeat password", end=": ")
    second = input().strip()
    
    if password == second and len(password) > 1:
        break
run(f"yes '{password}' | passwd {username}", shell=True)
run(f"usermod -a -G wheel {username}", shell=True)
run(f"usermod -a -G video {username}", shell=True)
run(f"usermod -a -G games {username}", shell=True)
run(f"usermod -a -G lp {username}", shell=True)
run(f"usermod -a -G audio {username}", shell=True)

print("Allow wheel users to use sudo. [ENTER]", end="")
input()
run("EDITOR=nvim visudo", shell=True)

# Other stuff you should do or you'll be sad
run("yes | pacman -S dhcpcd wpa_supplicant connman-openrc", shell=True)
run("rc-update add connmand", shell=True)
print("MOTD", end=": ")
motd = input().strip()
run(f"printf '\n{motd}\n\n' > /etc/motd", shell=True)

run("printf '/dev/mapper/cryptswap\t\tswap\t\tswap\t\tdefaults\t0 0' >> /etc/fstab", shell=True)

# Finally fix swap
swapuuid = str(check_output(f"sudo blkid {disk}2 -o value -s UUID", shell=True).strip())[1:]
run("printf 'run_hook() {\n\tcryptsetup open /dev/disk/by-uuid/" + str(swapuuid) + " cryptswap\n}\n' > /etc/initcpio/hooks/openswap", shell=True)
run("printf 'build() {\n\tadd_runscript\n}\n' > /etc/initcpio/install/openswap", shell=True)
print("Add '/usr/bin/btrfs' to BINARIES")
print("Use these hooks and binaries:")
hooks_comment = "#HOOKS=(... autodetect keyboard keymap modconf block encrypt openswap filesystems ...)"
bins_comment = "#BINARIES=(/usr/bin/btrfs)"
print(hooks_comment)
print(bins_comment)
run(f"printf '\n{hooks_comment}' >> /etc/mkinitcpio.conf", shell=True)
run(f"printf '\n{bins_comment}' >> /etc/mkinitcpio.conf", shell=True)
print("[ENTER]", end=" ")
input()
run("nvim /etc/mkinitcpio.conf", shell=True)
run("mkinitcpio -P", shell=True)

print("\nTasks completed. You should exit and reboot.")

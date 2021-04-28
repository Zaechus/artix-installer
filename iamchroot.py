#!/usr/bin/env python

import sys

from signal import signal, SIGINT
from subprocess import run, check_output

def handler(recv, frame):
    sys.exit()

signal(SIGINT, handler)

def make_password(s):
    print(s, end="")

    while True:
        password = input("Password: ").strip()
        second = input("Repeat password: ").strip()

        if password == second and len(password) > 1:
            break

def confirm_name(s):
    while True:
        name = input(f"{s.capitalize()}: ").strip()

        if len(name) > 1:
            choice = input(f"Is '{name}' a good {s.lower()}? (y/N): ").strip()
            if choice == "y":
                break

disk = ""
while True:
    run("fdisk -l", shell=True)
    disk = input("\nDisk to install to (e.g. `/dev/sda`): ").strip()
    if len(disk) > 0:
        break

# Boring stuff you should probably do
region_city = input("Region/City (e.g. `America/Denver`): ").strip()
if len(region_city) < 3:
    region_city = "America/Denver"

run(f"ln -sf /usr/share/zoneinfo/{region_city} /etc/localtime", shell=True)
run("hwclock --systohc", shell=True)

# Configure pacman
input("Configure pacman (color, multilib, etc.). [ENTER] ")
run("nvim /etc/pacman.conf", shell=True)
run("printf '\nkeyserver hkp://keyserver.ubuntu.com\n' >> /etc/pacman.d/gnupg/gpg.conf", shell=True)
run("pacman-key --populate artix", shell=True)

run("yes | pacman -Syu neofetch", shell=True)

# Localization
input("Uncomment locales (en_US.UTF-8). [ENTER] ")
run("nvim /etc/locale.gen", shell=True)
run("locale-gen", shell=True)
lang = input("LANG (en_US.UTF-8): ").strip()
if len(lang) < 2:
    lang = "en_US.UTF-8"

keymap = input("KEYMAP (us): ").strip()
if len(keymap) < 2:
    keymap = "us"

run(f"printf 'LANG={lang}\n' > /etc/locale.conf", shell=True)
run(f"printf 'KEYMAP={keymap}\n' > /etc/vconsole.conf", shell=True)

# Host stuff
hostname = confirm_name("hostname")
run(f"printf '{hostname}\n' > /etc/hostname", shell=True)
run(f"printf '\n127.0.0.1\tlocalhost\n::1\t\tlocalhost\n127.0.1.1\t{hostname}.localdomain\t{hostname}\n' > /etc/hosts", shell=True)

# Install boot loader
ucode = input(
    "\nDesired microcode packages:"
    "\n(1)  Intel"
    "\n(2)  AMD"
    "\n(3+) Both\n: "
).strip()
if ucode == "1":
    ucode = "intel-ucode"
elif ucode == "2":
    ucode = "amd-ucode"
else:
    ucode = "amd-ucode intel-ucode"

run(f"yes | pacman -S efibootmgr grub {ucode}", shell=True)

disk3uuid = str(check_output(f"sudo blkid {disk}3 -o value -s UUID", shell=True).strip())[1:]
run(f"printf '\n#cryptdevice=UUID={disk3uuid}:cryptroot root=/dev/mapper/cryptroot rootflags=subvol=@' >> /etc/default/grub", shell=True)

input("Configure GRUB (boot options, encryption, console, etc.). [ENTER] ")

run("nvim /etc/default/grub", shell=True)
run("grub-install --target=x86_64-efi --efi-directory=/boot/efi --bootloader-id=GRUB --removable --recheck", shell=True)
run("grub-mkconfig -o /boot/grub/grub.cfg", shell=True)

# Local.start
run(f"printf 'rfkill unblock wifi\nneofetch >| /etc/issue\n' > /etc/local.d/local.start", shell=True)
run("chmod +x /etc/local.d/local.start", shell=True)

# Add default user
run("yes | pacman -S zsh", shell=True)
run("chsh -s /bin/zsh", shell=True)

root_password = make_password("\nChanging root password...\n")
run(f"yes '{root_password}' | passwd", shell=True)

run("rm /etc/skel/.bash*", shell=True)
run("useradd -D -s /bin/zsh", shell=True)

username = confirm_name("username")
run(f"useradd -m {username}", shell=True)

user_password = make_password("")
run(f"yes '{user_password}' | passwd {username}", shell=True)
run(f"usermod -a -G wheel {username}", shell=True)
run(f"usermod -a -G video {username}", shell=True)
run(f"usermod -a -G games {username}", shell=True)
run(f"usermod -a -G lp {username}", shell=True)
run(f"usermod -a -G audio {username}", shell=True)

input("Allow wheel users to use sudo. [ENTER] ")
run("EDITOR=nvim visudo", shell=True)

# Other stuff you should do or you'll be sad
run("yes | pacman -S dhcpcd wpa_supplicant connman-openrc", shell=True)
run("rc-update add connmand", shell=True)
motd = confirm_name("motd")
run(f"printf '\n{motd}\n\n' > /etc/motd", shell=True)

run("printf '/dev/mapper/cryptswap\t\tswap\t\tswap\t\tdefaults\t0 0' >> /etc/fstab", shell=True)

# Finally fix swap
swapuuid = str(check_output(f"sudo blkid {disk}2 -o value -s UUID", shell=True).strip())[1:]
run("printf 'run_hook() {\n\tcryptsetup open /dev/disk/by-uuid/" + str(swapuuid) + " cryptswap\n}\n' > /etc/initcpio/hooks/openswap", shell=True)
run("printf 'build() {\n\tadd_runscript\n}\n' > /etc/initcpio/install/openswap", shell=True)
print("Use these hooks and binaries:")
hooks_comment = "#HOOKS=(... autodetect keyboard keymap modconf block encrypt openswap filesystems ...)"
bins_comment = "#BINARIES=(/usr/bin/btrfs)"
print(hooks_comment)
print(bins_comment)
run(f"printf '\n{hooks_comment}' >> /etc/mkinitcpio.conf", shell=True)
run(f"printf '\n{bins_comment}' >> /etc/mkinitcpio.conf", shell=True)
input("[ENTER] ")
run("nvim /etc/mkinitcpio.conf", shell=True)
run("mkinitcpio -P", shell=True)

print("\nTasks completed. You should exit and reboot.")

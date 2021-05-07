#!/usr/bin/env python

import sys

from signal import signal, SIGINT
from subprocess import run, check_output

def handler(recv, frame):
    sys.exit()

signal(SIGINT, handler)

def make_password(s):
    print("Passwords cannot contain ' or \"")
    print(s, end="")

    while True:
        password = input("Password: ").strip()
        second = input("Repeat password: ").strip()

        if password == second and len(password) > 1:
            return password

def confirm_name(s):
    while True:
        name = input(f"{s.capitalize()}: ").strip()

        if len(name) > 1:
            choice = input(f"Would you like '{name}' to be your {s.lower()}? (y/N): ").strip()
            if choice == "y":
                return name

disk = sys.argv[1]
part1 = f"{disk}1"
part2 = f"{disk}2"
part3 = f"{disk}3"
if "nvme" in disk:
    part1 = f"{disk}p1"
    part2 = f"{disk}p2"
    part3 = f"{disk}p3"

fs_type = ""
root_part = part2

try:
    check_output(f"sudo blkid {part3} -o value -s TYPE", shell=True).strip().decode("utf-8")
    fs_type = check_output(f"sudo blkid /dev/mapper/cryptroot -o value -s TYPE", shell=True).strip().decode("utf-8")
    root_part = part3
except:
    try:
        fs_type = check_output(f"sudo blkid /dev/MyVolGrp/root -o value -s TYPE", shell=True).strip().decode("utf-8")
    except:
        fs_type = check_output(f"sudo blkid {root_part} -o value -s TYPE", shell=True).strip().decode("utf-8")

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
run("nvim /etc/pacman.d/gnupg/gpg.conf", shell=True)
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
ucode_img = ""
if ucode == "1":
    ucode_img = "initrd=intel-ucode.img"
    ucode = "intel-ucode"
elif ucode == "2":
    ucode_img = "initrd=amd-ucode.img"
    ucode = "amd-ucode"
else:
    ucode_img = "initrd=amd-ucode.img initrd=intel-ucode.img"
    ucode = "amd-ucode intel-ucode"

boot_loader = input(
    "\nDesired boot loader:"
    "\n(1)  rEFInd"
    "\n(2+) GRUB\n: "
).strip()
if boot_loader == "1":
    boot_loader = "refind"
else:
    boot_loader = "grub"

run(f"yes | pacman -S efibootmgr {boot_loader} {ucode}", shell=True)
root_part_uuid = check_output(f"sudo blkid {root_part} -o value -s UUID", shell=True).strip().decode("utf-8")

root_flags = ""
if fs_type == "ext4":
    root_flags = f"cryptdevice=UUID={root_part_uuid}:cryptroot root=/dev/MyVolGrp/root"
elif fs_type == "btrfs":
    root_flags = f"cryptdevice=UUID={root_part_uuid}:cryptroot root=/dev/mapper/cryptroot rootflags=subvol=@"

if boot_loader == "refind":
    run(f"printf '\"Boot with standard options\"  \"{root_flags} rw {ucode_img} initrd=initramfs-linux.img\"\n' > /boot/refind_linux.conf", shell=True)

    run("refind-install", shell=True)
    run(f"refind-install --usedefault {part1}", shell=True)
elif boot_loader == "grub":
    run(f"printf '\n#{root_flags}' >> /etc/default/grub", shell=True)

    input("Configure GRUB (boot options, encryption, console, etc.). [ENTER] ")

    run("nvim /etc/default/grub", shell=True)
    run("grub-install --target=x86_64-efi --efi-directory=/boot/efi --bootloader-id=ARTIXGRUB --removable --recheck", shell=True)
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

if fs_type == "ext4":
    run("printf '\n/dev/MyVolGrp/swap\t\tswap\t\tswap\t\tdefaults\t0 0\n' >> /etc/fstab", shell=True)
elif fs_type == "btrfs":
    run("printf '\n/dev/mapper/cryptswap\t\tswap\t\tswap\t\tdefaults\t0 0\n' >> /etc/fstab", shell=True)
    swap_uuid = check_output(f"sudo blkid {part2} -o value -s UUID", shell=True).strip().decode("utf-8")
    run(f"printf 'run_hook() {{\n\tcryptsetup open /dev/disk/by-uuid/{swap_uuid} cryptswap\n}}\n' > /etc/initcpio/hooks/openswap", shell=True)
    run("printf 'build() {\n\tadd_runscript\n}\n' > /etc/initcpio/install/openswap", shell=True)

run("nvim /etc/fstab", shell=True)

# Configure mkinitcpio
if fs_type == "ext4":
    hooks_comment = "#HOOKS=(base udev autodetect keyboard keymap modconf block encrypt lvm2 filesystems fsck)"
    bins_comment = "#BINARIES=()"
elif fs_type == "btrfs":
    hooks_comment = "#HOOKS=(base udev autodetect keyboard keymap modconf block encrypt openswap filesystems fsck)"
    bins_comment = "#BINARIES=(/usr/bin/btrfs)"

run(f"printf '\n{hooks_comment}' >> /etc/mkinitcpio.conf", shell=True)
run(f"printf '\n{bins_comment}' >> /etc/mkinitcpio.conf", shell=True)
input("Configure /etc/mkinitcpio.conf with the correct HOOKS AND BINARIES. [ENTER] ")
run("nvim /etc/mkinitcpio.conf", shell=True)
run("mkinitcpio -P", shell=True)

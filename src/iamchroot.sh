#!/bin/sh

# Boring stuff you should probably do
ln -sf /usr/share/zoneinfo/$region_city /etc/localtime
hwclock --systohc

# Localization
sed -i '/en_US\.UTF-8/s/^#//g' /etc/locale.gen
locale-gen
printf "LANG=en_US.UTF-8\n" > /etc/locale.conf
printf "KEYMAP=us\n" > /etc/vconsole.conf

# Host stuff
printf "$my_hostname\n" > /etc/hostname
printf "hostname=\"$hostname\"\n" > /etc/conf.d/hostname
printf "\n127.0.0.1\tlocalhost\n::1\t\tlocalhost\n127.0.1.1\t$hostname.localdomain\t$hostname\n" > /etc/hosts

# Install boot loader
root_part_uuid=$(blkid $root_part -o value -s UUID)

root_flags="cryptdevice=UUID=$root_part_uuid:cryptroot root=$my_root"

sed -i 's/^GRUB_CMDLINE_LINUX_DEFAULT.*$/GRUB_CMDLINE_LINUX_DEFAULT=\"$root_flags\"/g' /etc/default/grub
printf "\n\nGRUB_ENABLE_CRYPTODISK=y\n" >> /etc/default/grub

grub-install --target=x86_64-efi --efi-directory=/boot --recheck
grub-install --target=x86_64-efi --efi-directory=/boot --removable --recheck
grub-mkconfig -o /boot/grub/grub.cfg

# Local.start
printf "rfkill unblock wifi\n" > /etc/local.d/local.start
chmod +x /etc/local.d/local.start

# Add default user
yes $root_password | passwd

rm /etc/skel/.bash*
useradd -D -s /bin/zsh

useradd -m $username

yes $user_password | passwd $username
usermod -a -G wheel $username
usermod -a -G video $username
usermod -a -G audio $username

sed -i '/%wheel ALL=(ALL) ALL/s/^#//g' /etc/sudoers

# Other stuff you should do
rc-update add connmand default

printf "\n$my_swap\t\tswap\t\tswap\t\tsw\t0 0\n" >> /etc/fstab
if [[ $encrypted != "n" && my_fs == "btrfs" ]]; then
    swap_uuid=$(blkid $part2 -o value -s UUID)

    printf 'run_hook() {{\n\tcryptsetup open /dev/disk/by-uuid/{swap_uuid} cryptswap\n}}\n' > /etc/initcpio/hooks/openswap
    printf 'build() {\n\tadd_runscript\n}\n' > /etc/initcpio/install/openswap
fi

# Configure mkinitcpio
if [[ $my_fs == "ext4" ]]; then
    sed -i 's/^HOOKS.*$/HOOKS=(base udev autodetect keyboard keymap modconf block encrypt lvm2 filesystems fsck)/g' /etc/mkinitcpio.conf
elif [[ $my_fs == "btrfs" ]]; then
    sed -i 's/^HOOKS.*$/HOOKS=(base udev autodetect keyboard keymap modconf block encrypt openswap filesystems fsck)/g' /etc/mkinitcpio.conf
    sed -i 's/BINARIES=()/BINARIES=(\/usr\/bin\/btrfs)/g' /etc/mkinitcpio.conf
fi

mkinitcpio -P

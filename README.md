# artix-installer

A stupid installer for Artix Linux

## Usage

1. Boot into the Artix live disk
2. Connect to the internet. Ethernet is setup automatically, and wifi is done with something like:
```
sudo rfkill unblock wifi
sudo ip link set wlan0 up
connmanctl
```
In Connman, use: `agent on`, `scan wifi`, `services`, `connect wifi_NAME`, `quit`
3. Acquire the install scripts:
```
yes | sudo pacman -Sy --needed git && \
git clone https://github.com/Zaechus/artix-installer && \
cd artix-installer
```
4. Run `./install.sh`.
5. When everything finishes, `poweroff`, remove the installation media, and boot into Artix.

### Preinstallation

* ISO downloads can be found at [artixlinux.org](https://artixlinux.org/download.php)
* ISO files can be burned to drives with `dd` or something like Etcher.
* `sudo dd bs=4M if=/path/to/artix.iso of=/dev/sd[drive letter] status=progress`
* A better method these days is to use [Ventoy](https://www.ventoy.net/en/index.html)

## Assumptions

* You can follow basic instructions.
* You don't mess up. The scripts will only hold your hand so far. Mistakes, of course, will either cause the script to kill itself or render the new unbootable.
* You're aware that you'll manually have to enter `--type luks1` as a LUKS option until GRUB gains full support for LUKS2.
* You're aware that the rEFInd option will probably work but lacks full testing because of issues with QEMU. Submit an issue if it doesn't work.

## What you get

A very minimal Artix Linux system with OpenRC and only essential packages.

Post-installation networking is done with Connman.


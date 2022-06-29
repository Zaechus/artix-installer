# artix-installer

![](https://img.shields.io/badge/OS-Artix%20Linux-blue?logo=Artix+Linux)

A simple installer for Artix Linux

## Usage

1. Boot into the Artix live disk (the login and password are both `artix`).
2. Connect to the internet. Ethernet is setup automatically, and wifi is done with something like:
```
sudo rfkill unblock wifi
sudo ip link set wlan0 up
connmanctl
```
In Connman, use: `agent on`, `scan wifi`, `services`, `connect wifi_NAME`, `quit`

3. Acquire the install scripts:
```
curl -OL https://github.com/Zaechus/artix-installer/archive/v2.1.0.tar.gz
tar xzf v2.1.0.tar.gz
cd artix-installer-2.1.0
```
4. Run `./install.sh`.
5. When everything finishes, `poweroff`, remove the installation media, and boot into Artix. Post-installation networking is done with Connman.

### Preinstallation

* ISO downloads can be found at [artixlinux.org](https://artixlinux.org/download.php)
* ISO files can be burned to drives with `dd` or something like Etcher.
* `sudo dd bs=4M if=/path/to/artix.iso of=/dev/sd[drive letter] status=progress`
* A better method these days is to use [Ventoy](https://www.ventoy.net/en/index.html).

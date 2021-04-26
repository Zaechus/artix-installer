#!/bin/sh

rfkill unblock wifi
ip link set wlan0 up
printf "\n> scan wifi\n> services\n> agent on\n> connect wifi_NAME\n> quit\n"
connmanctl
yes | pacman -Sy --needed python
echo "Run 'python install.py' whenever you're ready."

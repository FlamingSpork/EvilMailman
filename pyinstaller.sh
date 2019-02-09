#!/usr/bin/env bash
OS=$(uname -s)
ARCH=$(uname -m)
UNAME="${OS}_$ARCH"
echo "Building binaries for $UNAME"
pyinstaller -F both_server.py
mv dist/both_server "dist/both_server_$UNAME"
cd dns
pyinstaller -F client.py
mv dist/client "../dist/dns_client_$UNAME"
cd ../smtp
pyinstaller -F client.py
mv dist/client "../dist/smtp_client_$UNAME"
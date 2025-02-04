#!/bin/bash
echo "Switching to Bluetooth mode..."
sudo systemctl stop sonoak-go-librespot.service sonoak-snapclient.service
sudo systemctl start bluetooth.service
sudo systemctl start sonoak-bluealsa.service
sudo systemctl start sonoak-agent-bluetooth.service

# Configuration du Bluetooth
echo -e "power on\ndiscoverable on\npairable on\ndiscoverable-timeout 0\npairable-timeout 0\nquit" | bluetoothctl

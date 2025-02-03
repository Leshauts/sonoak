#!/bin/bash
echo "Switching to MacOS mode..."
sudo systemctl stop bluetooth.service sonoak-bluealsa.service sonoak-agent-bluetooth.service sonoak-go-librespot.service
sudo systemctl start sonoak-snapclient.service

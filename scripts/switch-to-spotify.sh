#!/bin/bash
echo "Switching to Spotify mode..."
sudo systemctl stop bluetooth.service sonoak-bluealsa.service sonoak-agent-bluetooth.service sonoak-snapclient.service
sudo systemctl start sonoak-go-librespot.service

#!/bin/bash

# Arrêt des services
sudo systemctl stop bluetooth
sudo systemctl stop bt-agent

# Redémarrage du bluetooth
sudo rfkill unblock bluetooth
sleep 2

# Démarrage des services
sudo systemctl start bluetooth
sleep 2
sudo systemctl start bt-agent

# Affichage des statuts
echo "Status bluetooth:"
sudo systemctl status bluetooth
echo "Status bt-agent:"
sudo systemctl status bt-agent
echo "Log bt-agent:"
sudo tail -n 10 /var/log/bt-agent.log
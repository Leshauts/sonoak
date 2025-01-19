#!/bin/bash
# backend/setup-librespot.sh
# Arrêt des processus existants
pkill -f go-librespot
rm -f /home/leo/.config/go-librespot/lockfile

# Configuration de go-librespot
cat > config.yml << EOL
server:
  enabled: true
  address: "0.0.0.0"  # Allow all connections
  port: 24879
  allow_origin: "http://localhost:5173"

audio:
  backend: pulseaudio
  device: ""
  format: F32
  rate: 44100

player:
  volume: 65536
EOL

# Copie de la configuration
mkdir -p /home/leo/.config/go-librespot/
cp config.yml /home/leo/.config/go-librespot/

# Démarrage de go-librespot
./go-librespot
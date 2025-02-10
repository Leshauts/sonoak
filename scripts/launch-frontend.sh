#!/bin/bash

# Tuer toute instance existante de Chromium
pkill chromium || true  # Le || true permet d'éviter l'erreur si aucun processus n'existe

# Aller dans le dossier frontend et lancer l'app en arrière-plan
cd ../frontend && npm run dev &

# Attendre que le serveur soit prêt (5 secondes)
sleep 5

# Lancer Chromium en mode kiosk
chromium-browser \
  --kiosk \
  --touch-events \
  --enable-touch-events \
  --enable-touch-ui \
  --disable-pinch \
  --no-first-run \
  --disable-infobars \
  --disable-session-crashed-bubble \
  --noerrdialogs \
  --disable-translate \
  --disable-features=TranslateUI \
  --disable-save-password-bubble \
  --disable-notifications \
  --start-maximized \
  --incognito \
  http://localhost:5173
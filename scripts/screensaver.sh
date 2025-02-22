#!/bin/bash

# Chemins vers vos programmes
ETEINDRE_ECRAN="/home/leo/sonoak/RPi-USB-Brightness/64/lite/Raspi_USB_Backlight_nogui -b 0"
ALLUMER_ECRAN="/home/leo/sonoak/RPi-USB-Brightness/64/lite/Raspi_USB_Backlight_nogui -b 5"
TEMPS_VEILLE=2400

# Utiliser le chemin stable vers le WaveShare
TOUCHSCREEN_DEVICE="/dev/input/by-id/usb-WaveShare_WS170120_220211-event-if00"

echo "Utilisation du périphérique : $TOUCHSCREEN_DEVICE"

# Définir le fichier de compteur dans /tmp avec un nom unique
COMPTEUR_FILE="/tmp/screensaver_timer_$USER"

# Créer le fichier s'il n'existe pas
if [ ! -f "$COMPTEUR_FILE" ]; then
    touch "$COMPTEUR_FILE"
    chmod 777 "$COMPTEUR_FILE"
fi

# Initialiser le compteur
echo "0" > "$COMPTEUR_FILE"

# Fonction pour allumer l'écran
allumer_ecran() {
    echo "Allumer l'écran"
    $ALLUMER_ECRAN
    echo "0" > "$COMPTEUR_FILE"
    echo "Compteur réinitialisé à 0"
}

# Fonction pour éteindre l'écran
eteindre_ecran() {
    echo "Éteindre l'écran"
    $ETEINDRE_ECRAN
}

# Allumer l'écran au démarrage du script
allumer_ecran

# Nettoyer à la sortie
trap 'rm -f "$COMPTEUR_FILE"' EXIT

# Démarrer l'incrémentation du compteur dans un processus séparé
(
while true; do
    if [ -f "$COMPTEUR_FILE" ]; then
        compteur=$(<"$COMPTEUR_FILE")
        echo "Compteur : $compteur"
        
        if [ $compteur -ge $TEMPS_VEILLE ]; then
            eteindre_ecran
        fi
        
        echo $((compteur + 1)) > "$COMPTEUR_FILE"
    else
        echo "0" > "$COMPTEUR_FILE"
        chmod 777 "$COMPTEUR_FILE"
    fi
    sleep 1
done
) &

# Surveiller les événements tactiles
libinput debug-events --device "$TOUCHSCREEN_DEVICE" | while read -r line; do
    if [[ $line =~ "TOUCH_DOWN" ]]; then
        echo "Toucher détecté !"
        allumer_ecran
    fi
done
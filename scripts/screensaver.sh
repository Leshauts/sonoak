#!/bin/bash

# Configuration de l'environnement graphique
export DISPLAY=:0
export XAUTHORITY=/home/leo/.Xauthority

# Chemin vers le programme pour éteindre l'écran
ETEINDRE_ECRAN="/home/leo/sonoak/RPi-USB-Brightness/64/lite/Raspi_USB_Backlight_nogui -b 0"

# Chemin vers le programme pour allumer l'écran
ALLUMER_ECRAN="/home/leo/sonoak/RPi-USB-Brightness/64/lite/Raspi_USB_Backlight_nogui -b 5"

# Temps de mise en veille de l'écran en secondes
TEMPS_VEILLE=10

# Fonction pour allumer l'écran
allumer_ecran() {
    echo "Allumer l'écran"
    $ALLUMER_ECRAN
}

# Fonction pour éteindre l'écran
eteindre_ecran() {
    echo "Éteindre l'écran"
    $ETEINDRE_ECRAN
}

# Fonction pour réinitialiser le compteur
reset_compteur() {
    echo "Réinitialiser le compteur"
    compteur=0
}

# Initialiser le compteur
compteur=0

# Attendre que l'environnement graphique soit prêt
sleep 5

# Récupérer la position initiale du curseur
position_initiale=$(xdotool getmouselocation --shell | grep "X=" | cut -d'=' -f2)

# Boucle principale
while true; do
    # Afficher la valeur du compteur
    echo "Compteur : $compteur"

    # Vérifier si le curseur a changé de position
    nouvelle_position=$(xdotool getmouselocation --shell | grep "X=" | cut -d'=' -f2)
    if [ "$nouvelle_position" != "$position_initiale" ]; then
        allumer_ecran
        reset_compteur
        position_initiale="$nouvelle_position"
    fi

    # Vérifier si l'écran doit être éteint
    if [ $compteur -ge $TEMPS_VEILLE ]; then
        eteindre_ecran
    fi

    # Attendre 1 seconde
    sleep 1

    # Incrémenter le compteur
    compteur=$((compteur + 1))
done
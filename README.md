# Sonoak
Lecteur audio pour Raspberry Pi avec interface utilisateur web , supportant multiple sources audio (Spotify via librespot, Bluetooth, Jack, Soundcast)

**Matériel nécessaire :**
* Raspberry Pi 3B+ ou 4
* HifiBerry AMP2 ou AMP4
* Écran
* Carte SD (16GB+ recommandé)

**Partie 1 : Base Audio**
1. Installation :
    * DietPi + HifiBerry
    * Librespot
2. Interfaces React :
    * Interface principale (écran Raspberry)
        * Affichage complet
        * Clavier React intégré
        * Mode kiosk
    * Interface mobile (navigateur)
        * Version allégée
        * Responsive
        * Contrôles essentiels

**Partie 2 : Sources Audio**
* Spotify (Librespot) 
* Bluetooth
* Entrée Jack
* Soundcast (son du Mac au Raspberry)
* Radio Internet (Radio Browser API)

**Partie 3 : Améliorations audio**
* ALSA Equalizer
    * Contrôlable depuis l'interface
    * Préréglages (Jazz, Rock, etc)
* Paramètres :
    * Basses/Aigus
    * Fréquences ?
    * Gauche / droite

**Partie 4 : Système / UI**
* Mode Kiosk :
    * Boot personnalisé
    * Splash screen
    * Récupération erreurs
    * Redémarrage auto
* UI Finale :
    * Thème cohérent
    * Animations fluides
    * Mode jour/nuit
    * Messages système
* Réseau :
    * DNS local
    * Sécurité basique
    * QR code connexion
    * Multi-utilisateurs
* Gestion Système :
    * Mises à jour auto
    * Sauvegardes config
    * Logs système
    * Interface admin
* Tests & Optimisation :
    * Tests charge
    * Tests réseau
    * Optimisation cache
    * Documentation

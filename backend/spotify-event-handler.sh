#!/bin/bash

# Configuration
SERVER_URL="http://127.0.0.1:8888"
LOG_FILE="/tmp/spotify-events.log"
DEBUG=true

# Fonction de logging
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" >> "$LOG_FILE"
    if [ "$DEBUG" = true ]; then
        echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
    fi
}

# Nettoyer les valeurs et convertir les sauts de ligne en virgules
clean_value() {
    if [ -z "$1" ]; then
        echo ""
    else
        echo "$1" | tr '\n' ',' | sed 's/,$//' | sed 's/"/\\"/g'
    fi
}

# Traiter les valeurs
EVENT_TYPE="$PLAYER_EVENT"
TRACK_ID="${TRACK_ID:-""}"
NAME="${NAME:-""}"
ARTISTS=$(clean_value "$ARTISTS")
ALBUM="${ALBUM:-""}"
COVERS=$(clean_value "$COVERS")
POSITION_MS="${POSITION_MS:-0}"
DURATION_MS="${DURATION_MS:-0}"

# Construire le JSON selon le type d'événement
case "$EVENT_TYPE" in
    "track_changed")
        JSON_DATA=$(cat << EOF
{
    "type": "$EVENT_TYPE",
    "trackId": "$TRACK_ID",
    "name": "$NAME",
    "artists": "$ARTISTS",
    "album": "$ALBUM",
    "duration_ms": $DURATION_MS,
    "position_ms": $POSITION_MS,
    "coverUrl": "$(echo "$COVERS" | cut -d',' -f1)"
}
EOF
)
        ;;
    "playing"|"paused"|"stopped"|"position_changed")  # Ajout de position_changed ici
        JSON_DATA=$(cat << EOF
{
    "type": "$EVENT_TYPE",
    "trackId": "$TRACK_ID",
    "position_ms": $POSITION_MS
}
EOF
)
        ;;
    *)
        JSON_DATA=$(cat << EOF
{
    "type": "$EVENT_TYPE"
}
EOF
)
        ;;
esac

# Log pour debug
log "Envoi de l'événement: $EVENT_TYPE"
log "JSON: $JSON_DATA"

# Envoi au serveur
RESPONSE=$(curl -s -X POST "${SERVER_URL}/event" \
     -H "Content-Type: application/json" \
     -d "$JSON_DATA")

log "Réponse: $RESPONSE"
log "=== Fin de l'événement ===\n"

exit 0
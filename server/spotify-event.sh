#!/bin/bash
LOG_FILE="$(pwd)/spotify-event.log"

# Récupérer la première URL de couverture
get_first_cover() {
    echo "$COVERS" | head -n 1
}

case "$PLAYER_EVENT" in
    "track_changed")
        COVER_URL=$(get_first_cover)
        # Sauvegarde des métadonnées complètes avec la couverture
        echo "track_changed | $TRACK_ID | $NAME | $ARTISTS | $ALBUM | $COVER_URL" >> "$LOG_FILE"
        # Sauvegarde des métadonnées dans un fichier temporaire
        echo "$NAME | $ARTISTS | $ALBUM | $COVER_URL" > "$(pwd)/current_track.tmp"
        ;;
    "playing")
        if [ -f "$(pwd)/current_track.tmp" ]; then
            # Lecture des métadonnées sauvegardées
            IFS='|' read -r saved_name saved_artists saved_album saved_cover < "$(pwd)/current_track.tmp"
            echo "playing | $TRACK_ID | $saved_name | $saved_artists | $saved_album | $saved_cover" >> "$LOG_FILE"
        else
            COVER_URL=$(get_first_cover)
            echo "playing | $TRACK_ID | $NAME | $ARTISTS | $ALBUM | $COVER_URL" >> "$LOG_FILE"
        fi
        ;;
    "paused")
        if [ -f "$(pwd)/current_track.tmp" ]; then
            IFS='|' read -r saved_name saved_artists saved_album saved_cover < "$(pwd)/current_track.tmp"
            echo "paused | $TRACK_ID | $saved_name | $saved_artists | $saved_album | $saved_cover" >> "$LOG_FILE"
        else
            COVER_URL=$(get_first_cover)
            echo "paused | $TRACK_ID | $NAME | $ARTISTS | $ALBUM | $COVER_URL" >> "$LOG_FILE"
        fi
        ;;
esac
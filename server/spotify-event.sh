#!/bin/bash
LOG_FILE="$(pwd)/spotify-event.log"
DEBUG_FILE="$(pwd)/spotify-debug.log"

log_debug() {
    echo "$(date): $1" >> "$DEBUG_FILE"
}

log_debug "Script started with event: $PLAYER_EVENT"
log_debug "TRACK_ID: $TRACK_ID"
log_debug "NAME: $NAME"
log_debug "ARTISTS: $ARTISTS"
log_debug "ALBUM: $ALBUM"
log_debug "COVERS content: $COVERS"

# Récupérer la première URL de couverture
get_first_cover() {
    if [ -n "$COVERS" ]; then
        echo "$COVERS" | head -n 1
    else
        log_debug "No covers available"
    fi
}

case "$PLAYER_EVENT" in
    "track_changed")
        COVER_URL=$(get_first_cover)
        log_debug "track_changed event - Cover URL: $COVER_URL"
        # Sauvegarde des métadonnées complètes
        echo "track_changed | $TRACK_ID | $NAME | $ARTISTS | $ALBUM | $COVER_URL" >> "$LOG_FILE"
        echo "$NAME | $ARTISTS | $ALBUM | $COVER_URL" > "$(pwd)/current_track.tmp"
        ;;
    "playing")
        if [ -f "$(pwd)/current_track.tmp" ]; then
            IFS='|' read -r saved_name saved_artists saved_album saved_cover < "$(pwd)/current_track.tmp"
            log_debug "playing event - Using saved data with cover: $saved_cover"
            echo "playing | $TRACK_ID | $saved_name | $saved_artists | $saved_album | $saved_cover" >> "$LOG_FILE"
        else
            COVER_URL=$(get_first_cover)
            log_debug "playing event - No saved data, using current with cover: $COVER_URL"
            echo "playing | $TRACK_ID | $NAME | $ARTISTS | $ALBUM | $COVER_URL" >> "$LOG_FILE"
        fi
        ;;
    "paused")
        if [ -f "$(pwd)/current_track.tmp" ]; then
            IFS='|' read -r saved_name saved_artists saved_album saved_cover < "$(pwd)/current_track.tmp"
            log_debug "paused event - Using saved data with cover: $saved_cover"
            echo "paused | $TRACK_ID | $saved_name | $saved_artists | $saved_album | $saved_cover" >> "$LOG_FILE"
        else
            COVER_URL=$(get_first_cover)
            log_debug "paused event - No saved data, using current with cover: $COVER_URL"
            echo "paused | $TRACK_ID | $NAME | $ARTISTS | $ALBUM | $COVER_URL" >> "$LOG_FILE"
        fi
        ;;
esac

log_debug "Script finished processing event: $PLAYER_EVENT"
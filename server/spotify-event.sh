#!/bin/bash
if [ "$PLAYER_EVENT" = "track_changed" ]; then
    # Format les artistes (remplace les newlines par des virgules)
    FORMATTED_ARTISTS=$(echo "$ARTISTS" | tr '\n' ',')
    echo "track_changed | $TRACK_ID | $NAME | $FORMATTED_ARTISTS | $ALBUM" >> /Users/leo/sonoak/server/spotify-event.log
elif [ "$PLAYER_EVENT" = "playing" ]; then
    echo "playing | $TRACK_ID | $POSITION_MS" >> /Users/leo/sonoak/server/spotify-event.log
elif [ "$PLAYER_EVENT" = "paused" ]; then
    echo "paused | $TRACK_ID" >> /Users/leo/sonoak/server/spotify-event.log
fi
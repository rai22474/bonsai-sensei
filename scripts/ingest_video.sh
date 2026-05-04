#!/bin/bash

if [ "$#" -ne 3 ]; then
    echo "Uso: $0 <URL> <YOUTUBE_URL> <CANAL>"
    echo "Ejemplo: $0 http://localhost:8080 'https://www.youtube.com/watch?v=dQw4w9WgXcQ' ryan-neil"
    exit 1
fi

BASE_URL=$1
YOUTUBE_URL=$2
CHANNEL=$3

curl -s -X POST "$BASE_URL/api/wiki/transcripts/ingest" \
    -H "Content-Type: application/json" \
    -d "{\"url\": \"$YOUTUBE_URL\", \"channel\": \"$CHANNEL\"}" | python3 -m json.tool

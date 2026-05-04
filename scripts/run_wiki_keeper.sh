#!/bin/bash

if [ "$#" -ne 1 ]; then
    echo "Uso: $0 <BASE_URL>"
    echo "Ejemplo: $0 http://localhost:8080"
    exit 1
fi

BASE_URL=$1

curl -s -X POST "$BASE_URL/api/wiki/transcripts/wiki-keeper/run" | python3 -m json.tool

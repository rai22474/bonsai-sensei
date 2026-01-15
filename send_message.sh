#!/bin/bash

if [ "$#" -ne 3 ]; then
    echo "Uso: $0 <URL> <CHAT_ID> <MENSAJE>"
    echo "Ejemplo: $0 http://localhost:8000 123456789 \"Hola mundo\""
    exit 1
fi

URL=$1
CHAT_ID=$2
MESSAGE=$3

curl -v -X POST "$URL/telegram/send" \
    -H "Content-Type: application/json" \
    -d "{\"chat_id\": \"$CHAT_ID\", \"text\": \"$MESSAGE\"}"

#!/bin/bash
set -e

if pgrep -x "ollama" >/dev/null 2>&1; then
    echo "Stopping Ollama..."
    pkill -x ollama
    echo "Ollama stopped."
else
    echo "Ollama is not running."
fi

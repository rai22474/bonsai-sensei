#!/bin/bash
set -e

MODEL_NAME=${1:-qwen2.5:32b-instruct}

if ! command -v ollama >/dev/null 2>&1; then
    echo "Ollama CLI not found. Install it from https://ollama.com before running this script."
    exit 1
fi

if curl -s http://localhost:11434/api/status >/dev/null 2>&1; then
    if lsof -nP -iTCP:11434 -sTCP:LISTEN | grep -q "TCP \*:\|TCP 0.0.0.0:"; then
        echo "Ollama server already running."
    else
        echo "Ollama is running on localhost only. Restarting for container access..."
        pkill -x ollama || true
        OLLAMA_HOST=0.0.0.0:11434 ollama serve >/dev/null 2>&1 &
        sleep 2
    fi
else
    echo "Starting Ollama server..."
    OLLAMA_HOST=0.0.0.0:11434 ollama serve >/dev/null 2>&1 &
    sleep 2
fi

if ollama list | awk '{print $1}' | grep -q "^${MODEL_NAME}$"; then
    echo "Model already present: ${MODEL_NAME}"
else
    echo "Pulling model: ${MODEL_NAME}"
    if ! ollama pull "${MODEL_NAME}"; then
        echo "Model not found: ${MODEL_NAME}"
        echo "Try a model that exists in Ollama, e.g. 'mistral-small3.1' or 'llama3.2'."
        exit 1
    fi
fi

echo "Ollama ready on http://localhost:11434"

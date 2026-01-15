#!/bin/bash

# Build the image
echo "Building Docker image..."
docker build -t bonsai-sensei .

echo "Starting container..."
docker run --env-file .env -p 8050:8000 bonsai-sensei

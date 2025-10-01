#!/bin/bash

# Source conda init first
source ~/miniconda3/etc/profile.d/conda.sh
conda activate rna-project

# Kill any existing process on port 5000
lsof -ti:5000 | xargs kill -9 2>/dev/null || true

# Run API background
echo "Starting API server..."
uvicorn api.main:app --host 0.0.0.0 --port 5000 &
API_PID=$!

# Wait for API to be ready with health check
echo "Waiting for API server to be ready..."
MAX_RETRIES=30
RETRY_COUNT=0

while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
    # Check if API process is still running
    if ! kill -0 $API_PID 2>/dev/null; then
        echo "Error: API server process died unexpectedly"
        exit 1
    fi
    
    # Try health check
    if curl -s -f http://localhost:5000/api/v1/health > /dev/null 2>&1; then
        echo "API server is ready!"
        break
    fi
    
    RETRY_COUNT=$((RETRY_COUNT + 1))
    if [ $RETRY_COUNT -eq $MAX_RETRIES ]; then
        echo "Error: API server failed to start after ${MAX_RETRIES} seconds"
        echo "Killing API process..."
        kill $API_PID 2>/dev/null
        exit 1
    fi
    
    echo "Waiting for API server... (${RETRY_COUNT}/${MAX_RETRIES})"
    sleep 1
done

# Run Gradio with module
echo "Starting Gradio app..."
python -m gradio_app.app
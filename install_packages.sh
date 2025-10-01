#!/bin/bash

echo "Installing pip packages for RNA Analysis Project..."

# Make sure we're in the correct environment
if [[ "$CONDA_DEFAULT_ENV" != "rna-project" ]]; then
    echo "Please activate the rna-project environment first:"
    echo "conda activate rna-project"
    exit 1
fi

echo "[INFO] Installing packages..."

# Install packages in groups to avoid conflicts
pip install --upgrade pip

echo "[1/6] Installing web frameworks..."
pip install gradio==4.15.0 fastapi==0.109.0 "uvicorn[standard]==0.27.0" pydantic==2.5.3

echo "[2/6] Installing Gradio dependencies..."
# Additional packages that Gradio needs
pip install \
    websockets \
    pydub \
    ffmpy \
    semantic-version \
    typing-extensions \
    altair \
    pandas \
    jinja2 \
    markupsafe \
    orjson

echo "[3/6] Installing API and async tools..."
pip install requests==2.31.0 httpx==0.26.0 aiofiles==23.2.1

echo "[4/6] Installing visualization tools..."
pip install matplotlib==3.8.2 seaborn==0.13.2 plotly==5.18.0 pillow==10.2.0

echo "[5/6] Installing ML and vector database..."
# Install PyTorch first
pip install torch==2.1.2 torchvision==0.16.2

# Install compatible versions for sentence-transformers
# Fix for ImportError: cannot import name 'cached_download' from 'huggingface_hub'
pip install \
    transformers==4.36.2 \
    huggingface-hub==0.20.1 \
    tokenizers==0.15.0 \
    sentence-transformers==2.2.2

# Install vector database
pip install chromadb==0.4.22

echo "[6/6] Installing utilities..."
pip install python-dotenv==1.0.0 jupyterlab==4.0.10 biopython==1.83

echo ""
echo "=========================================="
echo "[SUCCESS] All packages installed!"
echo ""
echo "You can now run:"
echo "  python -m api.main      # Start API server"
echo "  python -m gradio_app.app # Start Gradio UI"
echo "=========================================="
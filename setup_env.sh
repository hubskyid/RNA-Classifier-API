#!/bin/bash

# Setup script for RNA Analysis Project

echo "=========================================="
echo "RNA Analysis Project - Environment Setup"
echo "=========================================="

# Fix conda configuration warnings
echo "[INFO] Configuring conda channels..."
conda config --add channels defaults
conda config --add channels conda-forge

# Install mamba
echo "[INFO] Installing mamba for faster environment creation..."
conda install -n base -c conda-forge mamba -y

if [ $? -eq 0 ]; then
    echo "[SUCCESS] Mamba installed successfully!"
    echo ""
    echo "[INFO] Creating environment with mamba..."
    mamba env create -f conda_env.yml
    
    if [ $? -eq 0 ]; then
        echo ""
        echo "=========================================="
        echo "[SUCCESS] Environment created successfully!"
        echo ""
        echo "Next steps:"
        echo "1. Activate environment: conda activate rna-project"
        echo "2. Start API server: python -m api.main"
        echo "3. Start Gradio UI: python -m gradio_app.app"
        echo "=========================================="
    else
        echo "[ERROR] Failed to create environment with mamba"
        echo "Try using conda directly: conda env create -f conda_env.yml"
    fi
else
    echo "[ERROR] Failed to install mamba"
    echo "Try creating environment with conda: conda env create -f conda_env.yml"
fi
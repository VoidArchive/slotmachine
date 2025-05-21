#!/bin/bash

VENV_DIR="venv"

if [ ! -d "$VENV_DIR" ]; then
    echo "Creating virtual environment in $VENV_DIR..."
    if ! python3 -m venv "$VENV_DIR"; then
        echo "Failed to create virtual environment. Please ensure python3 and venv are installed."
        exit 1
    fi
fi


source "$VENV_DIR/bin/activate"

echo "Installing dependencies from requirements.txt..."
if [ -f "requirements.txt" ]; then
    if ! pip install -r requirements.txt; then
        echo "Failed to install dependencies."
        deactivate
        exit 1
    fi
else
    echo "requirements.txt not found. Please create one with your project's dependencies."
    deactivate
    exit 1
fi

echo "Starting the game..."
python3 main.py
echo "Game finished." 
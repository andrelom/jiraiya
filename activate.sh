#!/bin/bash

VENV_DIR=".venv"

if [ -d "$VENV_DIR" ]; then
  echo "Virtual environment already exists."
else
  python3 -m venv $VENV_DIR
fi

echo "Activating virtual environment..."

source $VENV_DIR/bin/activate

if [ -f "requirements.txt" ]; then
  pip install -r requirements.txt
else
  echo "The requirements.txt was not found. Skipping package installation."
fi

echo "Setup complete."

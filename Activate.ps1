$VENV_DIR = ".venv"

if (Test-Path $VENV_DIR) {
    Write-Host "Virtual environment already exists."
} else {
    python -m venv $VENV_DIR
}

Write-Host "Activating virtual environment..."

# Activating the virtual environment.
& "$VENV_DIR\Scripts\Activate.ps1"

if (Test-Path "requirements.txt") {
    pip install -r requirements.txt
} else {
    Write-Host "The requirements.txt was not found. Skipping package installation."
}

Write-Host "Setup complete."

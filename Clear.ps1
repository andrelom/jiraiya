# Remove all __pycache__ directories.
Get-ChildItem -Path . -Recurse -Directory -Filter "__pycache__" | ForEach-Object { Remove-Item -Recurse -Force -Path $_.FullName }

# Remove all .pyc files.
Get-ChildItem -Path . -Recurse -File -Filter "*.pyc" | ForEach-Object { Remove-Item -Force -Path $_.FullName }

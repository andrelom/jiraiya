"""
Utility module for handling file operations.
"""

import os
import logging


logger = logging.getLogger(__name__)

def save_to_file(file_path: str, content: str) -> None:
    """
    Save the given content to the specified file.

    If the directory for the file does not exist, it will be created.

    Args:
        file_path (str): Path of the file to save.
        content (str): Content to write into the file.

    Raises:
        OSError: If an error occurs while creating the directory or writing the file.
    """
    try:
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, "w", encoding="utf-8") as file:
            file.write(content)
        logger.info("Saved file: %s", file_path)
    except OSError as e:
        logger.error("Failed to save file: %s. Error: %s", file_path, e)
        raise

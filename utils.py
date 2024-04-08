import json
import logging
import os
import random

from termcolor import colored

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def clean_dir(path: str) -> None:
    """
    Removes every file in a directory.
    """
    try:
        if not os.path.exists(path):
            os.mkdir(path)
            logger.info(f"Created directory: {path}")

        for file in os.listdir(path):
            file_path = os.path.join(path, file)
            os.remove(file_path)
            logger.info(f"Removed file: {file_path}")

        logger.info(colored(f"Cleaned {path} directory", "green"))
    except Exception as e:
        logger.error(f"Error occurred while cleaning directory {path}: {str(e)}")


def choose_random_song() -> str:
    """
    Chooses a random song from the songs/ directory.
    """
    try:
        songs = os.listdir("songs")
        song = random.choice(songs)
        if not song.endswith(".mp3"):
            song = random.choice(songs)

        logger.info(colored(f"Chose song: {song}", "green"))
        return f"songs/{song}"
    except Exception as e:
        logger.error(
            colored(f"Error occurred while choosing random song: {str(e)}", "red")
        )
        raise Exception(f"Error occurred while choosing random song: {str(e)}") from e

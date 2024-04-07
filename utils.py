import json
import logging
import os
import random
import sys
import uuid
import zipfile

import requests
from pytube import YouTube
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


def fetch_songs(zip_url: str) -> None:
    """
    Downloads songs into songs/ directory to use with geneated videos.
    """
    try:
        print(colored("[+] Fetching songs...", "green"))

        files_dir = "songs"
        if not os.path.exists(files_dir):
            os.mkdir(files_dir)
            logger.info(colored(f"Created directory: {files_dir}", "green"))
        else:
            # Skip if songs are already downloaded
            return

        response = requests.get(zip_url, timeout=300)
        with open("songs/songs.zip", "wb") as file:
            file.write(response.content)

        with zipfile.ZipFile("songs/songs.zip", "r") as file:
            file.extractall("songs")

        os.remove("songs/songs.zip")

        logger.info(colored("Downloaded Songs to songs", "green"))

    except Exception as e:
        logger.error(colored(f"Error occurred while fetching songs: {str(e)}", "red"))


def fetch_youtube_songs() -> None:

    YouTube("https://www.youtube.com/watch?v=RmWLNlKmMBQ").streams.filter(
        only_audio=True
    ).first().download(filename=f"songs/{uuid.uuid4()}.mp3")


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


def check_env_vars() -> None:
    """
    Checks if the necessary environment variables are set.
    """
    try:
        required_vars = ["PEXELS_API_KEY", "TIKTOK_SESSION_ID", "IMAGEMAGICK_BINARY"]
        missing_vars = [
            var + os.getenv(var)
            for var in required_vars
            if os.getenv(var) is None or (len(os.getenv(var)) == 0)
        ]

        if missing_vars:
            missing_vars_str = ", ".join(missing_vars)
            logger.error(
                colored(
                    f"The following environment variables are missing: {missing_vars_str}",
                    "red",
                )
            )
            logger.error(
                colored(
                    "Please consult 'EnvironmentVariables.md' for instructions on how to set them.",
                    "yellow",
                )
            )
            sys.exit(1)  # Aborts the program
    except Exception as e:
        logger.error(f"Error occurred while checking environment variables: {str(e)}")
        sys.exit(1)  # Aborts the program if an unexpected error occurs

import uuid

from pytube import YouTube


def fetch_youtube_songs(url: str) -> None:
    """
    Fetch youtube songs into the designated directory.
    """

    YouTube(url).streams.filter(only_audio=True).first().download(
        filename=f"songs/{uuid.uuid4()}.mp3"
    )


if __name__ == "__main__":
    url = input("Enter the youtube music url : ")
    fetch_youtube_songs(url)

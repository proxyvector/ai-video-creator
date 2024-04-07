from typing import List

import requests
from termcolor import colored


def search_for_stock_videos(
    query: str, api_key: str, it: int, min_dur: int, max_dur: int
) -> List[str]:
    """
    Searches for stock videos based on a query.
    """

    headers = {"Authorization": api_key}
    qurl = f"https://api.pexels.com/videos/search?query='{query}'&per_page={it}"
    r = requests.get(qurl, headers=headers)
    response = r.json()

    # Parse each video
    raw_urls = []
    video_url = []
    try:
        # loop through each video in the result
        for i in range(it):
            # check if video has desired minimum duration
            if (
                response["videos"][i]["duration"] < min_dur
                or response["videos"][i]["duration"] > max_dur
            ):
                continue
            raw_urls = response["videos"][i]["video_files"]
            temp_video_url = ""

            # loop through each url to determine the best quality
            video_res = 0
            for video in raw_urls:
                # Check if video has a valid download link
                # if ".com/external" in video["link"]:
                # Only save the URL with the largest resolution
                if (video["width"] * video["height"]) > video_res:
                    temp_video_url = video["link"]
                    video_res = video["width"] * video["height"]

            # add the url to the return list if it's not empty
            if temp_video_url != "":
                video_url.append(temp_video_url)

    except Exception as e:
        print(colored("[-] No Videos found.", "red"))
        print(colored(e, "red"))

    # Let user know
    print(colored(f'\t=> "{query}" found {len(video_url)} Videos', "cyan"))

    # Return the video url
    return video_url

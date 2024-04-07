import math
import os
import random
import uuid
from datetime import timedelta
from typing import List

import assemblyai as aai
import moviepy.editor as mp
import numpy
import requests
import srt_equalizer
from moviepy.editor import (
    AudioFileClip,
    CompositeVideoClip,
    TextClip,
    VideoFileClip,
    concatenate_videoclips,
)
from moviepy.video.fx.all import crop
from moviepy.video.tools.subtitles import SubtitlesClip
from openai import OpenAI
from PIL import Image
from termcolor import colored

ASSEMBLY_AI_API_KEY = os.getenv("ASSEMBLY_AI_API_KEY")


def save_video(video_url: str, directory: str = "temp") -> str:
    """
    Saves a video from a given URL and returns the path to the video.

    Args:
        video_url (str): The URL of the video to save.
        directory (str): The path of the temporary directory to save the video to

    Returns:
        str: The path to the saved video.
    """
    video_id = uuid.uuid4()
    video_path = f"{directory}/{video_id}.mp4"
    with open(video_path, "wb") as f:
        f.write(requests.get(video_url).content)

    return video_path


def __generate_subtitles_assemblyai(audio_path: str, voice: str, api_key: str) -> str:
    """
    Generates subtitles from a given audio file and returns the path to the subtitles.

    Args:
        audio_path (str): The path to the audio file to generate subtitles from.

    Returns:
        str: The generated subtitles
    """

    language_mapping = {
        "br": "pt",
        "id": "en",  # AssemblyAI doesn't have Indonesian
        "jp": "ja",
        "kr": "ko",
    }

    if voice in language_mapping:
        lang_code = language_mapping[voice]
    else:
        lang_code = voice

    aai.settings.api_key = api_key
    config = aai.TranscriptionConfig(language_code=lang_code)
    transcriber = aai.Transcriber(config=config)
    transcript = transcriber.transcribe(audio_path)
    subtitles = transcript.export_subtitles_srt(chars_per_caption=64)

    return subtitles


def __generate_subtitles_whisper(audio_path: str, openai_api_key: str) -> str:

    client = OpenAI(api_key=openai_api_key)
    audio_file = open(audio_path, "rb")
    transcript = client.audio.transcriptions.create(
        model="whisper-1", file=audio_file, response_format="srt"
    )

    print(transcript)

    return transcript


def __generate_subtitles_locally(
    sentences: List[str], audio_clips: List[AudioFileClip]
) -> str:
    """
    Generates subtitles from a given audio file and returns the path to the subtitles.

    Args:
        sentences (List[str]): all the sentences said out loud in the audio clips
        audio_clips (List[AudioFileClip]): all the individual audio clips which will make up the final audio track
    Returns:
        str: The generated subtitles
    """

    def convert_to_srt_time_format(total_seconds):
        # Convert total seconds to the SRT time format: HH:MM:SS,mmm
        if total_seconds == 0:
            return "0:00:00,0"
        return str(timedelta(seconds=total_seconds)).rstrip("0").replace(".", ",")

    start_time = 0
    subtitles = []

    for i, (sentence, audio_clip) in enumerate(zip(sentences, audio_clips), start=1):
        duration = audio_clip.duration
        end_time = start_time + duration

        # Format: subtitle index, start time --> end time, sentence
        subtitle_entry = f"{i}\n{convert_to_srt_time_format(start_time)} --> {convert_to_srt_time_format(end_time)}\n{sentence}\n"
        subtitles.append(subtitle_entry)

        start_time += duration  # Update start time for the next subtitle

    return "\n".join(subtitles)


def generate_subtitles(
    audio_path: str,
    sentences: List[str],
    audio_clips: List[AudioFileClip],
    voice: str,
    subtitles_path: str,
    api_key: str = "",
    openai_api_key: str = "",
) -> str:
    """
    Generates subtitles from a given audio file and returns the path to the subtitles.

    Args:
        audio_path (str): The path to the audio file to generate subtitles from.
        sentences (List[str]): all the sentences said out loud in the audio clips
        audio_clips (List[AudioFileClip]): all the individual audio clips which will make up the final audio track

    Returns:
        str: The path to the generated subtitles.
    """

    # Save subtitles
    subtitles_path = f"{subtitles_path}/{uuid.uuid4()}.srt"

    if api_key is not None and api_key != "":
        print(colored("[+] Creating subtitles using AssemblyAI", "green"))
        subtitles = __generate_subtitles_assemblyai(audio_path, voice, api_key)
    elif openai_api_key is not None and openai_api_key != "":
        print(colored("[+] Creating subtitles using OpenAI", "green"))
        subtitles = __generate_subtitles_whisper(audio_path, openai_api_key)
    else:
        print(colored("[+] Creating subtitles locally", "green"))
        subtitles = __generate_subtitles_locally(sentences, audio_clips)

    with open(subtitles_path, "w") as file:
        file.write(subtitles)

    # Equalize subtitles
    srt_equalizer.equalize_srt_file(subtitles_path, subtitles_path, 32)

    print(colored("[+] Subtitles generated.", "green"))

    return subtitles_path


def combine_videos(
    video_paths: List[str], max_duration: int, threads: int, project_space: str
) -> str:
    """
    Combines a list of videos into one video and returns the path to the combined video.

    Args:
        video_paths (List): A list of paths to the videos to combine.
        max_duration (int): The maximum duration of the combined video.
        max_clip_duration (int): The maximum duration of each clip.
        threads (int): The number of threads to use for the video processing.

    Returns:
        str: The path to the combined video.
    """
    video_id = uuid.uuid4()
    combined_video_path = f"{project_space}/videos/final_{video_id}.mp4"

    # Required duration of each clip
    # req_dur = max_duration / len(video_paths)

    print(colored("[+] Combining videos...", "blue"))
    # print(colored(f"[+] Each clip will be maximum {req_dur} seconds long.", "blue"))

    clips = []
    tot_dur = 0
    # Add downloaded clips over and over until the duration of the audio (max_duration) has been reached
    random.shuffle(video_paths)
    while tot_dur < max_duration:
        for video_path in video_paths:
            saved_video_path = save_video(video_path, f"{project_space}/videos")
            clip = VideoFileClip(saved_video_path)
            clip = clip.without_audio()
            # Check if clip is longer than the remaining audio
            if (max_duration - tot_dur) < clip.duration:
                clip = clip.subclip(0, (max_duration - tot_dur))
            # Only shorten clips if the calculated clip length (req_dur) is shorter than the actual clip to prevent still image
            # elif req_dur < clip.duration:
            #     clip = clip.subclip(0, req_dur)
            # clip = clip.set_fps(30)

            # Not all videos are same size,
            # so we need to resize them
            if round((clip.w / clip.h), 4) < 0.5625:
                clip = crop(
                    clip,
                    width=clip.w,
                    height=round(clip.w / 0.5625),
                    x_center=clip.w / 2,
                    y_center=clip.h / 2,
                )
            else:
                clip = crop(
                    clip,
                    width=round(0.5625 * clip.h),
                    height=clip.h,
                    x_center=clip.w / 2,
                    y_center=clip.h / 2,
                )
            clip = clip.resize((1080, 1920))

            # if clip.duration > max_clip_duration:
            #     clip = clip.subclip(0, max_clip_duration)

            clips.append(clip)
            tot_dur += clip.duration
            if tot_dur >= max_duration:
                break

    final_clip = concatenate_videoclips(clips)
    final_clip = final_clip.set_fps(30)
    final_clip.write_videofile(combined_video_path, threads=threads)

    return combined_video_path


def generate_video(
    combined_video_path: str,
    tts_path: str,
    subtitles_path: str,
    threads: int,
    subtitles_position: str,
    text_color: str,
    video_path: str,
) -> str:
    """
    This function creates the final video, with subtitles and audio.

    Args:
        combined_video_path (str): The path to the combined video.
        tts_path (str): The path to the text-to-speech audio.
        subtitles_path (str): The path to the subtitles.
        threads (int): The number of threads to use for the video processing.
        subtitles_position (str): The position of the subtitles.

    Returns:
        str: The path to the final video.
    """
    # Make a generator that returns a TextClip when called with consecutive
    generator = lambda txt: TextClip(
        txt,
        font="Papyrus",
        fontsize=80,
        color=text_color,
        bg_color="aqua",
    ).set_opacity(0.7)

    # def text_formatter(txt):
    #     text_clip = TextClip(
    #         txt,
    #         font="Papyrus",
    #         fontsize=80,
    #         color="black",
    #     )

    #     text_clip = text_clip.set_position("center")

    #     image_width, image_height = text_clip.size

    #     padding_width = 80  # 40 pixels on each side
    #     padding_height = 20  # 10 pixels on each side

    #     color_clip = ColorClip(
    #         size=(image_width + padding_width, image_height + padding_height),
    #         color=(0, 255, 255),
    #     ).set_opacity(0.7)

    #     return CompositeVideoClip([color_clip, text_clip])

    # Split the subtitles position into horizontal and vertical
    horizontal_subtitles_position, vertical_subtitles_position = (
        subtitles_position.split(",")
    )

    # Burn the subtitles into the video
    subtitles = SubtitlesClip(subtitles_path, generator)

    result = CompositeVideoClip(
        [
            VideoFileClip(combined_video_path),
            subtitles.set_pos(
                (horizontal_subtitles_position, vertical_subtitles_position)
            ),
        ]
    )

    # Add the audio
    audio = AudioFileClip(tts_path)
    result = result.set_audio(audio)

    result.write_videofile(f"{video_path}/output.mp4", threads=threads or 2)

    return f"{video_path}/output.mp4"


def zoom_in_effect(clip, zoom_ratio=0.04):
    def effect(get_frame, t):
        img = Image.fromarray(get_frame(t))
        base_size = img.size
        new_size = [
            math.ceil(img.size[0] * (1 + (zoom_ratio * t))),
            math.ceil(img.size[1] * (1 + (zoom_ratio * t))),
        ]
        # The new dimensions must be even.
        new_size[0] = new_size[0] + (new_size[0] % 2)
        new_size[1] = new_size[1] + (new_size[1] % 2)
        img = img.resize(new_size, Image.LANCZOS)
        x = math.ceil((new_size[0] - base_size[0]) / 2)
        y = math.ceil((new_size[1] - base_size[1]) / 2)
        img = img.crop([x, y, new_size[0] - x, new_size[1] - y]).resize(
            base_size, Image.LANCZOS
        )
        result = numpy.array(img)
        img.close()
        return result

    return clip.fl(effect)


def video_from_images(project_space: str, image_video_duration: int, max_duration: int):

    size = (1024, 1792)
    video_id = uuid.uuid4()
    combined_video_path = f"{project_space}/videos/final_{video_id}.mp4"
    img_list = os.listdir(f"{project_space}/images")

    slides = []
    duration_left = max_duration
    for n, path in enumerate(img_list):
        full_path = f"{project_space}/images/{path}"
        if duration_left < 5:
            slides.append(
                mp.ImageClip(full_path)
                .set_fps(25)
                .set_duration(duration_left)
                .resize(size)
            )
            slides[n] = zoom_in_effect(slides[n], 0.04)
            break
        slides.append(
            mp.ImageClip(full_path)
            .set_fps(25)
            .set_duration(image_video_duration)
            .resize(size)
        )
        slides[n] = zoom_in_effect(slides[n], 0.04)
        duration_left -= 5

    video = mp.concatenate_videoclips(slides)
    video.write_videofile(combined_video_path)

    return combined_video_path

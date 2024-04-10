import os
import uuid

from moviepy.editor import (
    AudioFileClip,
    CompositeAudioClip,
    CompositeVideoClip,
    TextClip,
    VideoFileClip,
)
from moviepy.video.tools.subtitles import SubtitlesClip
from openai import OpenAI
from termcolor import colored

from config import Config
from prompts import (
    generate_image_prompts,
    generate_images,
    generate_script,
    get_search_terms,
)
from search import search_for_stock_videos
from utils import choose_random_song
from video import combine_videos, generate_subtitles, save_video, video_from_images


class Videographer:
    """
    Videographer class.
    """

    def __init__(self, topic, stage=0, project_space=None):
        self.config = Config("config.json")
        self.topic = topic
        self.project_space = (
            f"temp/{project_space}" if project_space else self.create_temp_folder()
        )
        self.stage = stage

    def create_temp_folder(
        self,
    ):
        """
        Create a temporary folder for the project.
        Subsequently create subfolders for videos, subtitles, audio, and images.
        """

        project_name = uuid.uuid4()

        if not os.path.exists("temp"):
            os.makedirs("temp")
        if not os.path.exists(f"temp/{project_name}"):
            os.makedirs(f"temp/{project_name}")
        if not os.path.exists(f"temp/{project_name}/videos"):
            os.makedirs(f"temp/{project_name}/videos")
        if not os.path.exists(f"temp/{project_name}/subtitles"):
            os.makedirs(f"temp/{project_name}/subtitles")
        if not os.path.exists(f"temp/{project_name}/audio"):
            os.makedirs(f"temp/{project_name}/audio")
        if not os.path.exists(f"temp/{project_name}/images"):
            os.makedirs(f"temp/{project_name}/images")

        return f"temp/{project_name}"

    def get_video_urls_from_search_terms(self, search_terms):
        """
        Get video URLs from search terms.
        """

        video_urls = []

        # Defines how many results it should query and search through
        number_of_stock_vids = 15
        min_clip_duration = 10
        max_clip_duration = 20

        # Loop through all search terms,
        # and search for a video of the given search term
        for search_term in search_terms:
            found_urls = search_for_stock_videos(
                search_term,
                self.config.pexels_api_key,
                number_of_stock_vids,
                min_clip_duration,
                max_clip_duration,
            )
            # Check for duplicates
            for url in found_urls:
                if url not in video_urls:
                    video_urls.append(url)
                    # break

        # Check if video_urls is empty
        if not video_urls:
            print(colored("[-] No videos found to download.", "red"))

        return video_urls

    def download_videos_to_temp_folder(self, video_urls):
        """
        Download videos to the temporary folder.
        """

        video_paths = []

        # Let user know
        print(colored(f"[+] Downloading {len(video_urls)} videos...", "blue"))

        # Save the videos
        for video_url in video_urls:
            try:
                saved_video_path = save_video(video_url, f"{self.project_space}/videos")
                video_paths.append(saved_video_path)
            except Exception:
                print(colored(f"[-] Could not download video: {video_url}", "red"))

        print(colored("[+] Videos downloaded!", "green"))

        return video_paths

    def generate_speech_from_script_openai(self):
        """
        Generate speech from script using OpenAI API.
        """
        print(colored("[+] Generating speech from script...", "green"))

        script = ""

        with open(f"{self.project_space}/script.txt", "r", encoding="utf-8") as f:
            script = (" ").join(f.readlines())

        speech_file_path = f"{self.project_space}/audio/speech.mp3"
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        response = client.audio.speech.create(
            model="tts-1", voice="alloy", input=script
        )

        response.stream_to_file(speech_file_path)

        print(colored("[+] Done generating speech from script.", "green"))

    def add_music_to_video(self):
        """
        Add music to the generated video.
        """

        final_video_path = f"{self.project_space}/output.mp4"

        video_clip = VideoFileClip(final_video_path)
        # Select a random song
        song_path = choose_random_song()

        # Add song to video at 30% volume using moviepy
        original_duration = video_clip.duration
        original_audio = video_clip.audio
        song_clip = AudioFileClip(song_path).set_fps(44100)

        # Set the volume of the song to 20% of the original volume
        song_clip = song_clip.volumex(0.2).set_fps(44100)

        # Add the song to the video
        comp_audio = CompositeAudioClip([original_audio, song_clip])
        video_clip = video_clip.set_audio(comp_audio)
        video_clip = video_clip.set_fps(30)
        video_clip = video_clip.set_duration(original_duration)

        output_file = final_video_path.split(".")[0] + "_music.mp4"
        video_clip.write_videofile(output_file, threads=self.config.n_threads or 1)

        os.rename(output_file, final_video_path)

        print(
            colored(f"[+] Music added to generated video: {final_video_path}!", "green")
        )

    def kill_ffmpeg_processes(
        self,
    ):
        """
        Kill all ffmpeg processes.
        """

        if os.name == "nt":
            # Windows
            os.system("taskkill /f /im ffmpeg.exe")
        else:
            # Other OS
            os.system("pkill -f ffmpeg")

    def generate_video_from_stock_videos(self):
        """
        Generate video from stock videos.
        """

        script = ""

        with open(f"{self.project_space}/script.txt", "r", encoding="utf-8") as f:
            script = (" ").join(f.readlines())

        search_terms = get_search_terms(
            self.topic,
            self.config.no_of_stock_videos,
            script,
            self.config.smart_llm_model,
        )

        video_urls = self.get_video_urls_from_search_terms(search_terms)

        video_duration = AudioFileClip(
            f"{self.project_space}/audio/speech.mp3"
        ).duration

        combined_video_path = combine_videos(
            video_urls,
            video_duration,
            self.config.n_threads or 2,
            self.project_space,
        )

        return combined_video_path

    def generate_video_from_images(self):
        """
        Generate video from dalle images.
        """

        video_duration = AudioFileClip(
            f"{self.project_space}/audio/speech.mp3"
        ).duration

        number_of_images = (video_duration // self.config.image_video_duration) + 1

        print(colored(f"[+] Required Video Duration: {video_duration}", "blue"))
        print(colored(f"[+] Number of images req : {number_of_images}", "blue"))

        image_prompts = generate_image_prompts(number_of_images, self.topic)
        generate_images(os.getenv("OPENAI_API_KEY"), image_prompts, self.project_space)
        video_from_images(
            self.project_space,
            self.config.image_video_duration,
            video_duration,
        )

    def generate_script(self):
        """
        Generate script for the video.
        """

        generate_script(
            self.project_space,
            self.topic,
            self.config.paragraph_number,
            self.config.smart_llm_model,
            "english",  # have to replace this with config.voice
            self.config.custom_prompt,
        )

    def generate_subtitles(self):
        """
        Generate subtitles for the video.
        """

        generate_subtitles(
            self.project_space,
            voice=self.config.voice_prefix,
            openai_api_key=os.getenv("OPENAI_API_KEY"),
        )

    def generate_video(self):
        """
        Generate the final video.
        """

        subtitles_path = f"{self.project_space}/subtitles/subtitles.srt"
        tts_path = f"{self.project_space}/audio/speech.mp3"
        combined_video_path = f"{self.project_space}/videos/final_raw.mp4"

        # Split the subtitles position into horizontal and vertical
        horizontal_subtitles_position, vertical_subtitles_position = (
            self.config.subtitles_position.split(",")
        )

        def on_subtitles_read(txt):
            return TextClip(
                txt,
                font=self.config.text_font,
                fontsize=80,
                color=self.config.text_color or "#FFFF00",
                bg_color="aqua",
            ).set_opacity(0.9)

        # Burn the subtitles into the video
        subtitles = SubtitlesClip(subtitles_path, on_subtitles_read)

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

        result.write_videofile(
            f"{self.project_space}/output.mp4", threads=self.config.n_threads or 2
        )

    def process(self):
        """
        Process the video creation.
        """

        try:

            print(colored("[+] Starting the video creation process", "green"))

            if self.stage < 1:
                # Generate script
                self.generate_script()

            if self.stage < 2:
                # Generate speech
                self.generate_speech_from_script_openai()

            if self.stage < 3:
                # Generate subtitles
                self.generate_subtitles()

            if self.stage < 4:
                # Generate raw video
                if self.config.use_stock_videos:
                    self.generate_video_from_stock_videos()
                else:
                    self.generate_video_from_images()

            if self.stage < 5:
                # Generate final video with speech and subtitles
                self.generate_video()

                print(colored("************", "green"))
                print(colored(f"[+] Video : {self.project_space}/output.mp4", "green"))
                print(colored("************", "green"))

            if self.stage < 6:

                # Add music to the video
                if self.config.use_music:
                    self.add_music_to_video()

        except Exception as e:
            print(colored(f"[-] Error generating video: {e}", "red"))
        finally:
            print(colored("[+] Cleaning up...", "green"))
            self.kill_ffmpeg_processes()


if __name__ == "__main__":
    topic = input("Enter the topic for your video : ")
    Videographer(topic).process()

    # topic = "3 reasons rust is better than python"
    # Videographer(
    #     topic,
    #     4,
    #     "ab6e7366-3cb6-4fad-93da-820e92cd00d8",
    # ).process()

import os
import uuid

from moviepy.editor import (
    AudioFileClip,
    CompositeAudioClip,
    VideoFileClip,
    concatenate_audioclips,
)
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
from tiktokvoice import tts
from utils import choose_random_song
from video import (
    combine_videos,
    generate_subtitles,
    generate_video,
    save_video,
    video_from_images,
)


class Videographer:
    """
    Videographer class.
    """

    def __init__(self):
        self.config = Config("config.json")
        self.project_space = self.create_temp_folder()

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

    def generate_speech_from_script(self, script):
        """
        Generate speech from script using TikTokVoice.
        """

        # Split script into sentences
        sentences = script.split(". ")

        # Remove empty strings
        sentences = list(filter(lambda x: x != "", sentences))
        temp_tts_paths = []

        # Generate TTS for every sentence
        for sentence in sentences:
            current_tts_path = f"{self.project_space}/audio/{uuid.uuid4()}.mp3"
            tts(sentence, self.config.voice, filename=current_tts_path)
            audio_clip = AudioFileClip(current_tts_path)
            temp_tts_paths.append(audio_clip)

        # Combine all TTS files using moviepy
        final_audio = concatenate_audioclips(temp_tts_paths)
        final_tts_path = f"{self.project_space}/audio/{uuid.uuid4()}.mp3"
        final_audio.write_audiofile(final_tts_path)

        return final_tts_path, temp_tts_paths, sentences

    def generate_speech_from_script_openai(self, script):
        """
        Generate speech from script using OpenAI API.
        """

        speech_file_path = f"{self.project_space}/audio/{uuid.uuid4()}.mp3"
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        response = client.audio.speech.create(
            model="tts-1", voice="alloy", input=script
        )

        response.stream_to_file(speech_file_path)

        return speech_file_path, None, None

    def add_music_to_video(self, final_video_path):
        """
        Add music to the generated video.
        """

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

    def process(self, topic):
        """
        Process the video creation.
        """

        print(colored("[+] Starting the video creation process", "green"))

        # Generate a script
        script = generate_script(
            topic,
            self.config.paragraph_number,
            self.config.smart_llm_model,
            "english",  # have to replace this with config.voice
            self.config.custom_prompt,
        )

        # final_tts_path, temp_tts_paths, sentences = self.generate_speech_from_script(
        #     script
        # )

        final_tts_path, temp_tts_paths, sentences = (
            self.generate_speech_from_script_openai(script)
        )

        # Generate subtitles
        try:
            subtitles_path = generate_subtitles(
                audio_path=final_tts_path,
                sentences=sentences,
                audio_clips=temp_tts_paths,
                voice=self.config.voice_prefix,
                subtitles_path=f"{self.project_space}/subtitles",
                openai_api_key=os.getenv("OPENAI_API_KEY"),
            )
        except Exception as e:
            print(colored(f"[-] Error generating subtitles: {e}", "red"))
            subtitles_path = None

        required_video_duration = AudioFileClip(final_tts_path).duration

        if self.config.use_stock_videos:

            # Generate search terms
            search_terms = get_search_terms(
                topic,
                self.config.no_of_stock_videos,
                script,
                self.config.smart_llm_model,
            )

            video_urls = self.get_video_urls_from_search_terms(search_terms)

            combined_video_path = combine_videos(
                video_urls,
                required_video_duration,
                self.config.n_threads or 2,
                f"{self.project_space}",
            )

        else:

            print(
                colored(
                    f"[+] Required Video Duration: {required_video_duration}", "blue"
                )
            )

            number_of_images = (
                required_video_duration // self.config.image_video_duration
            ) + 1

            print(colored(f"[+] Number of images req : {number_of_images}", "blue"))

            image_prompts = generate_image_prompts(number_of_images, topic)
            print(colored(f"[+] Image prompts: {image_prompts}", "blue"))
            generate_images(
                os.getenv("OPENAI_API_KEY"), image_prompts, self.project_space
            )

            combined_video_path = video_from_images(
                self.project_space,
                self.config.image_video_duration,
                required_video_duration,
            )

        # Put everything together
        try:
            final_video_path = generate_video(
                combined_video_path,
                final_tts_path,
                subtitles_path,
                self.config.n_threads or 2,
                self.config.subtitles_position,
                self.config.text_color or "#FFFF00",
                f"{self.project_space}",
                self.config.text_font,
            )

            print(colored("************", "green"))
            print(
                colored(f"[+] Final video generated at : {final_video_path}", "green")
            )
            print(colored("************", "green"))

            if self.config.use_music:
                self.add_music_to_video(final_video_path)

        except Exception as e:
            print(colored(f"[-] Error generating final video: {e}", "red"))
            final_video_path = None

        # Define metadata for the video, we will display this to the user, and use it for the YouTube upload
        # title, description, keywords = generate_metadata(topic, script, config.smart_llm_model)

        self.kill_ffmpeg_processes()


if __name__ == "__main__":
    topic = input("Enter the topic for your video : ")
    Videographer().process(topic)

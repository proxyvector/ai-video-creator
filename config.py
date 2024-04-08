# config file
import json
import os


class Config:
    """Config class."""

    def __init__(self, config_file: str = None):
        """Initialize the config class."""
        self.config_file = config_file if config_file else os.getenv("CONFIG_FILE")
        self.openai_api_key = os.getenv("OPENAI_API_KEY", None)
        self.pexels_api_key = os.getenv("PEXELS_API_KEY", None)
        self.assembly_ai_api_key = os.getenv("ASSEMBLY_AI_API_KEY", None)
        self.no_of_stock_videos = int(os.getenv("NO_OF_STOCK_VIDEOS", 5))
        self.voice = os.getenv("VOICE", "english")
        self.voice_prefix = os.getenv("VOICE_PREFIX", "en")
        self.custom_prompt = os.getenv("CUSTOM_PROMPT", None)
        self.paragraph_number = int(os.getenv("PARAGRAPH_NUMBER", 5))
        self.fast_llm_model = os.getenv("FAST_LLM_MODEL", "gpt-3.5-turbo-16k")
        self.smart_llm_model = os.getenv("SMART_LLM_MODEL", "gpt-4-1106-preview")
        self.n_threads = int(os.getenv("N_THREADS", 1))
        self.subtitles_position = os.getenv("SUBTITLES_POSITION", "bottom")
        self.text_color = os.getenv("TEXT_COLOR", "white")
        self.use_music = os.getenv("USE_MUSIC", False)
        self.automate_youtube_upload = os.getenv("AUTOMATE_YOUTUBE_UPLOAD", False)
        self.songs_zip_url = os.getenv(
            "SONGS_ZIP_URL",
            "https://filebin.net/2avx134kdibc4c3q/drive-download-20240209T180019Z-001.zip",
        )
        self.use_stock_videos = os.getenv("USE_STOCK_VIDEOS", False)
        self.image_video_duration = int(os.getenv("IMAGE_VIDEO_DURATION", 5))

        self.load_config_file()

        os.environ["OPENAI_API_KEY"] = self.openai_api_key
        os.environ["PEXELS_API_KEY"] = self.pexels_api_key
        os.environ["ASSEMBLY_AI_API_KEY"] = self.assembly_ai_api_key

    def load_config_file(self) -> None:
        """Load the config file."""
        if self.config_file is None:
            return None
        with open(self.config_file, "r", encoding="utf-8") as f:
            config = json.load(f)
        for key, value in config.items():
            self.__dict__[key] = value

    def print_config(self) -> None:
        """Print the config."""
        print("Config: \n")
        print(json.dumps(self.__dict__, indent=4))

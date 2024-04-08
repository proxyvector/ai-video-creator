# AI Video Creator 

Automate the creation of short videos for instagram, youtube, tiktok , simply by providing a video topic to talk about.

> **🎥** Watch the video on [YouTube](https://youtu.be/4Z_FKd6UPE0).

## Installation 📥

`AI Video Creator ` requires Python 3.11 to run effectively. If you don't have Python installed, you can download it from [here](https://www.python.org/downloads/).

After you finished installing Python, you can install `AI Video Creator ` by following the steps below:

```bash
git clone https://github.com/proxyvector/ai-video-creator
cd ai-video-creator

# Install requirements
pip install -r requirements.txt

# Copy config-example.json and fill out values
cp config-example.json config.json

# Run the main script
python main.py
```

See [`config-example.json`](config-example.json) for the required environment variables.

## Usage 🛠️

1. Copy the `config-example.json` file to `config.json` and fill in the required values
2. Run the main script using the command `python main.py`
3. Enter a topic to generate a video about and hit enter
4. Wait for the video to be generated
6. The output video's location is printed on the console.It is of the format`temp/<project-id>/output.mp4`

## Music 🎵

You can add music to your videos by putting all your mp3 files in the songs folder.
You can also download royalty free music from youtube. Use the [`scripts/download_music.py`](scripts/download_music.py) file to download the music of any youtube video to the songs folder.

The main script selects a song at random from all the mp3 files in the songs folder and adds it to the video

## Fonts 🅰
To change the font of the subtitles simply specify the font name in the config file.
If you want to try a font not on your system, you need to install the font in the system first.Then you can specify the font in the config file.

## Raising Issues 🤔
If you face any issues while installing or using this tool, you can raise an issue using [`github issues`](https://github.com/proxyvector/ai-video-creator/issues)

## License 📝

See [`LICENSE`](LICENSE) file for more information.

# Connect 🤝

If you liked my work, pls star it! This helps me know if I should build more stuff like this :)
You can connect with me on [twitter](https://twitter.com/proxy_vector) 
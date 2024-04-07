# AI Video Creator 

Automate the creation of YouTube Shorts, simply by providing a video topic to talk about.

> **🎥** Watch the video on [YouTube](https://youtu.be/).

## Installation 📥

`AI Video Creator ` requires Python 3.11 to run effectively. If you don't have Python installed, you can download it from [here](https://www.python.org/downloads/).

After you finished installing Python, you can install `AI Video Creator ` by following the steps below:

```bash
git clone https://github.com/proxyvector/ai-video-creator
cd MoneyPrinter

# Install requirements
pip install -r requirements.txt

# Copy .env.example and fill out values
cp .env.example .env

# Run the main script
python main.py
```

See [`.env.example`](.env.example) for the required environment variables.

If you need help, open [EnvironmentVariables.md](EnvironmentVariables.md) for more information.

## Usage 🛠️

1. Copy the `.env.example` file to `.env` and fill in the required values
1. Open `http://localhost:3000` in your browser
1. Enter a topic to talk about
1. Click on the "Generate" button
1. Wait for the video to be generated
1. The video's location is `MoneyPrinter/output.mp4`

## Music 🎵

To use your own music, compress all your MP3 Files into a ZIP file and upload it somewhere. Provide the link to the ZIP file in the Frontend.

It is recommended to use Services such as [Filebin](https://filebin.net) to upload your ZIP file. If you decide to use Filebin, provide the Frontend with the absolute path to the ZIP file by using More -> Download File, e.g. (use this [Popular TT songs ZIP](https://filebin.net/klylrens0uk2pnrg/drive-download-20240209T180019Z-001.zip), not this [Popular TT songs](https://filebin.net/2avx134kdibc4c3q))

You can also just move your MP3 files into the `Songs` folder. 

## Fonts 🅰

Add your fonts to the `fonts/` folder, and load them by specifying the font name on line `124` in `Backend/video.py`.

## FAQ 🤔

### My ImageMagick binary is not being detected

Make sure you set your path to the ImageMagick binary correctly in the `.env` file, it should look something like this:

```env
IMAGEMAGICK_BINARY="C:\\Program Files\\ImageMagick-7.1.0-Q16\\magick.exe"
```

Don't forget to use double backslashes (`\\`) in the path, instead of one.

### I can't install `playsound`: Wheel failed to build

If you're having trouble installing `playsound`, you can try installing it using the following command:

```bash
pip install -U wheel
pip install -U playsound
```
## License 📝

See [`LICENSE`](LICENSE) file for more information.
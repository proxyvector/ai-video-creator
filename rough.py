import webbrowser
from io import BytesIO

import requests
from openai import OpenAI
from PIL import Image

# Replace YOUR_API_KEY with your OpenAI API key
client = OpenAI(api_key="")

# Call the API
response = client.images.generate(
    model="dall-e-3",
    prompt="a cute cat with a hat on.",
    size="1024x1792",
    quality="standard",
    n=1,
)

response = requests.get(response.data[0].url, timeout=300)
Image.open(BytesIO(response.content)).save("a.png")

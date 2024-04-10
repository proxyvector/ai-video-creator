import json
import os
import re
from io import BytesIO
from typing import List, Tuple

# import g4f
import openai
import requests
from PIL import Image
from termcolor import colored

# import google.generativeai as genai

# Set environment variables
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
openai.api_key = OPENAI_API_KEY
# GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
# genai.configure(api_key=GOOGLE_API_KEY)


def generate_response(prompt: str, ai_model: str) -> str:
    """
    Generate a script for a video, depending on the subject of the video.

    Args:
        video_subject (str): The subject of the video.
        ai_model (str): The AI model to use for generation.


    Returns:

        str: The response from the AI model.

    """

    if ai_model == "g4f":

        # response = g4f.ChatCompletion.create(

        #     model=g4f.models.gpt_35_turbo_16k_0613,

        #     messages=[{"role": "user", "content": prompt}],

        # )
        pass

    elif ai_model in ["gpt3.5-turbo", "gpt4", "gpt-4-1106-preview"]:

        model_name = (
            "gpt-3.5-turbo" if ai_model == "gpt3.5-turbo" else "gpt-4-1106-preview"
        )

        response = (
            openai.chat.completions.create(
                model=model_name,
                messages=[{"role": "user", "content": prompt}],
            )
            .choices[0]
            .message.content
        )
    elif ai_model == "gemmini":
        # model = genai.GenerativeModel('gemini-pro')
        # response_model = model.generate_content(prompt)
        # response = response_model.text
        pass

    else:

        raise ValueError("Invalid AI model selected.")

    return response


def generate_script(
    project_space: str,
    video_subject: str,
    paragraph_number: int,
    ai_model: str,
    voice: str,
    custom_prompt: str,
) -> str:
    """
    Generate a script for a video, depending on the subject of the video, the number of paragraphs, and the AI model.
    """

    print(colored("[+] Generating Video Script ...\n", "green"))

    if custom_prompt:
        prompt = custom_prompt
    else:
        prompt = """
            Generate a script for an engaging youtube short video, depending on the subject of the video.

            The script is to be returned as a string with the specified number of paragraphs.

            Here is an example of a string:
            "This is an example string."

            Do not under any circumstance reference this prompt in your response.

            Get straight to the point, don't start with unnecessary things like, "welcome to this video".

            Obviously, the script should be related to the subject of the video.

            YOU MUST NOT INCLUDE ANY TYPE OF MARKDOWN OR FORMATTING IN THE SCRIPT, NEVER USE A TITLE.
            YOU MUST WRITE THE SCRIPT IN THE LANGUAGE SPECIFIED IN [LANGUAGE].
            ONLY RETURN THE RAW CONTENT OF THE SCRIPT. DO NOT INCLUDE "VOICEOVER", "NARRATOR" OR SIMILAR INDICATORS OF WHAT SHOULD BE SPOKEN AT THE BEGINNING OF EACH PARAGRAPH OR LINE. YOU MUST NOT MENTION THE PROMPT, OR ANYTHING ABOUT THE SCRIPT ITSELF. ALSO, NEVER TALK ABOUT THE AMOUNT OF PARAGRAPHS OR LINES. JUST WRITE THE SCRIPT.

        """

    prompt += f"""
    
    Subject: {video_subject}
    Number of paragraphs: {paragraph_number}
    Language: {voice}

    """

    # Generate script
    response = generate_response(prompt, ai_model)

    # Return the generated script
    if response:
        # Clean the script
        # Remove asterisks, hashes
        response = response.replace("*", "")
        response = response.replace("#", "")

        # Remove markdown syntax
        response = re.sub(r"\[.*\]", "", response)
        response = re.sub(r"\(.*\)", "", response)

        # Split the script into paragraphs
        paragraphs = response.split("\n\n")

        # Select the specified number of paragraphs
        selected_paragraphs = paragraphs[:paragraph_number]

        # Join the selected paragraphs into a single string
        final_script = "\n\n".join(selected_paragraphs)

        # Print to console the number of paragraphs used
        print(
            colored(f"[+] Number of paragraphs generated: {len(selected_paragraphs)}", "green")
        )

        with open(f"{project_space}/script.txt", "w", encoding="utf-8") as f:
            f.write(final_script)

        print(colored("[+] Video script generated and saved !\n", "green"))

        return final_script
    else:
        print(colored("[-] GPT returned an empty response.", "red"))
        return None


def generate_image_prompts(amount: int, subject: str) -> List[str]:
    """
    Generate prompts for images to be used in a video.

    Returns:
        List[str]: The list of prompts for images.
    """

    # Build prompt
    prompt = f"""
    Generate a list of prompts for images to be used in a video.

    Generate {amount} prompts for images to be used in a video,
    depending on the subject of a video.
    Subject: {subject}

    The prompts are to be returned as an Array of strings.

    Each prompt should describe a scene or an object that can be visualized in an image.

    Here is an example of an Array of strings:
    ["prompt 1", "prompt 2", "prompt 3"]

    YOU MUST ONLY RETURN THE ARRAY OF STRINGS.
    YOU MUST NOT RETURN ANYTHING ELSE. 
    YOU MUST NOT RETURN THE SCRIPT.

    The prompts should be related to the subject of the video.

    """

    # Generate prompts
    response = generate_response(prompt, "gpt-4-1106-preview")

    # Parse response into a list of prompts
    prompts = []

    try:
        prompts = json.loads(response)
        if not isinstance(prompts, list) or not all(
            isinstance(prompt, str) for prompt in prompts
        ):
            raise ValueError("Response is not a list of strings.")

    except (json.JSONDecodeError, ValueError):
        print(
            colored(
                "[*] GPT returned an unformatted response. Attempting to clean...",
                "yellow",
            )
        )

        # Attempt to extract list-like string and convert to list
        match = re.search(r'\["(?:[^"\\]|\\.)*"(?:,\s*"[^"\\]*")*\]', response)
        if match:
            try:
                prompts = json.loads(match.group())
            except json.JSONDecodeError:
                print(colored("[-] Could not parse response.", "red"))
                return []

    # Let user know
    print(
        colored(
            f"[+] Generated {len(prompts)} image prompts: {', '.join(prompts)}",
            "green",
        )
    )

    # Return prompts
    return prompts


def get_search_terms(
    video_subject: str, amount: int, script: str, ai_model: str
) -> List[str]:
    """
    Generate a JSON-Array of search terms for stock videos,
    depending on the subject of a video.

    Args:
        video_subject (str): The subject of the video.
        amount (int): The amount of search terms to generate.
        script (str): The script of the video.
        ai_model (str): The AI model to use for generation.

    Returns:
        List[str]: The search terms for the video subject.
    """

    # Build prompt
    prompt = f"""
    Generate {amount} search terms for stock videos,
    depending on the subject of a video.
    Subject: {video_subject}

    The search terms are to be returned as
    a Array of strings.

    Each search term should consist of 1-3 words,
    always add the main subject of the video.
    
    YOU MUST ONLY RETURN THE ARRAY OF STRINGS.
    YOU MUST NOT RETURN ANYTHING ELSE. 
    YOU MUST NOT RETURN THE SCRIPT.
    
    The search terms must be related to the subject of the video.
    Here is an example of a Array of strings:
    ["search term 1", "search term 2", "search term 3"]

    For context, here is the full text:
    {script}
    """

    # Generate search terms
    response = generate_response(prompt, ai_model)

    # Parse response into a list of search terms
    search_terms = []

    try:
        search_terms = json.loads(response)
        if not isinstance(search_terms, list) or not all(
            isinstance(term, str) for term in search_terms
        ):
            raise ValueError("Response is not a list of strings.")

    except (json.JSONDecodeError, ValueError):
        print(
            colored(
                "[*] GPT returned an unformatted response. Attempting to clean...",
                "yellow",
            )
        )

        # Attempt to extract list-like string and convert to list
        match = re.search(r'\["(?:[^"\\]|\\.)*"(?:,\s*"[^"\\]*")*\]', response)
        if match:
            try:
                search_terms = json.loads(match.group())
            except json.JSONDecodeError:
                print(colored("[-] Could not parse response.", "red"))
                return []

    # Let user know
    print(
        colored(
            f"[+] Generated {len(search_terms)} search terms: {', '.join(search_terms)}",
            "green",
        )
    )

    # Return search terms
    return search_terms


def generate_metadata(
    video_subject: str, script: str, ai_model: str
) -> Tuple[str, str, List[str]]:
    """
    Generate metadata for a YouTube video, including the title, description, and keywords.

    Args:
        video_subject (str): The subject of the video.
        script (str): The script of the video.
        ai_model (str): The AI model to use for generation.

    Returns:
        Tuple[str, str, List[str]]: The title, description, and keywords for the video.
    """

    # Build prompt for title
    title_prompt = f"""  
    Generate a catchy and SEO-friendly title for a YouTube shorts video about {video_subject}.  
    """

    # Generate title
    title = generate_response(title_prompt, ai_model).strip()

    # Build prompt for description
    description_prompt = f"""  
    Write a brief and engaging description for a YouTube shorts video about {video_subject}.  
    The video is based on the following script:  
    {script}  
    """

    # Generate description
    description = generate_response(description_prompt, ai_model).strip()

    # Generate keywords
    keywords = get_search_terms(video_subject, 6, script, ai_model)

    print(colored("[-] Metadata for YouTube upload:", "blue"))
    print(colored("   Title: ", "blue"))
    print(colored(f"   {title}", "blue"))
    print(colored("   Description: ", "blue"))
    print(colored(f"   {description}", "blue"))
    print(colored("   Keywords: ", "blue"))
    print(colored(f"  {', '.join(keywords)}", "blue"))

    return title, description, keywords


def generate_images(openai_key, prompt_list, project_space):
    """
    Generate images for a video, depending on the subject of the video.
    Subsequently, save the images to the images folder in the project space.
    """

    # Build prompt
    print(colored("[+] Generating Images ...\n", "green"))

    # Generate images
    # Call the API
    client = openai.OpenAI(api_key=openai_key)
    urls = []

    for i, prompt in enumerate(prompt_list):

        final_prompt = f"""
        Generate an image for {prompt}
        
        THERE SHOULDN'T BE ANY TEXT IN THE IMAGE
        THERE SHOULDN'T BE ANY DEFORMED LIMBS IN THE IMAGE
        THE IMAGE SHOULD BE VERTICALLY ORIENTED

        """

        try:

            response = client.images.generate(
                model="dall-e-3",
                prompt=final_prompt,
                size="1024x1792",
                quality="standard",
                n=1,
            )

            # Return the generated images
            if response:
                image_data = requests.get(response.data[0].url, timeout=300)
                Image.open(BytesIO(image_data.content)).save(
                    f"{project_space}/images/{i}.png"
                )
                urls.append(response.data[0].url)
                print(colored(f"[+] Image generated for prompt: {prompt}", "green"))
                print(colored("[+] Image saved!\n", "green"))
            else:
                print(colored("[-] DALL-E returned an empty response.", "red"))
        except Exception as e:
            print(colored(f"[-] Error generating image: {e}", "red"))

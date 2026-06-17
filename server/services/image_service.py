import os
import requests

from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("HUGGINGFACE_API_KEY")

API_URL = (
    "https://api-inference.huggingface.co/models/"
    "stabilityai/stable-diffusion-xl-base-1.0"
)

headers = {
    "Authorization": f"Bearer {API_KEY}"
}


async def generate_image(prompt: str):

    response = requests.post(
        API_URL,
        headers=headers,
        json={
            "inputs": prompt
        }
    )

    # Debug print
    print("STATUS:", response.status_code)

    if response.status_code != 200:
        print(response.text)

    return response.content
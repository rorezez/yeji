import os
import requests
from typing import Dict
from .plugin import Plugin

# Pastikan kamu telah menginstal openai Python library dengan pip
import openai

class DallePlugin(Plugin):
    """
    A plugin to generate images using OpenAI's DALL-E 3
    """
    def get_source_name(self) -> str:
        return "DALL-E"

    def get_spec(self) -> [Dict]:
        return [{
            "name": "generate_image",
            "description": "Generate an image from a textual description using DALL-E.",
            "parameters": {
                "type": "object",
                "properties": {
                    "prompt": {"type": "string", "description": "Textual description for the image ,the text must be in english."},
                    "size": {"type": "string", "description": "Size of the generated image."},
                    "quality": {"type": "string", "description": "Quality of the generated image."},
                    "n": {"type": "integer", "description": "Number of images to generate."}
                },
                "required": ["prompt"],
            },
        }]

    async def execute(self, function_name, **kwargs) -> Dict:
        try:
            # Set up your OpenAI API key
            openai.api_key = os.getenv("OPENAI_API_KEY")

            # Call the OpenAI API to generate the image
            response = openai.Image.create(
                model="dall-e-3",
                prompt=kwargs["prompt"],
                size=kwargs.get("size", "1024x1024"),
                quality=kwargs.get("quality", "standard"),
                n=kwargs.get("n", 1),
            )

            # Extract the URL of the generated image
            image_url = response['data'][0]['url']

            # Return the URL of the generated image
            return {
                'direct_result': {
                    'kind': 'photo',
                    'format': 'url',
                    'value': image_url
                }
            }

        except Exception as e:
            # Handle exceptions
            return {'result': f'Error: {str(e)}'}


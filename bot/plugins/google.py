import os
import requests
from bs4 import BeautifulSoup
from typing import Dict
from .plugin import Plugin  # Asumsi kamu memiliki base class Plugin
import logging

class WebPlugin(Plugin):
    """
    A plugin to give information for a given URL, then use it along with user query
    """

    def get_source_name(self) -> str:
        return "WebContent"

    def get_spec(self) -> [Dict]:
        return [{
            "name": "web_content",
            "description": "get information of a given URL",
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "the URL based on user input"
                    },
                    "query": {
                        "type": "string",
                        "description": "the user query"
                    }
                },
                "required": ["url", "query"],
            },
        }]

    async def execute(self, function_name, **kwargs) -> Dict:
        url = kwargs['url']
        user_query = kwargs['query']

        # Fetch the content from the URL
        response = requests.get(url)
        if response.status_code != 200:
            logging.error(f"Failed to fetch the URL content. Status code: {response.status_code}")
            return {"Result": "Failed to fetch the URL content"}

        # Parse the fetched content to extract title and paragraphs
        soup = BeautifulSoup(response.content, 'html.parser')
        title = soup.title.string if soup.title else "No title"

        # Find all the paragraph elements and extract just the text from each
        paragraphs = soup.find_all('p')
        paragraph_texts = [p.get_text() for p in paragraphs]

        # Combine all the paragraph texts into one string
        combined_text = ' '.join(paragraph_texts)

        logging.info(f"Title: {title}")
        logging.info(f"Paragraphs: {combined_text[:1000]}")  # Limiting to first 500 characters
        logging.info(f"User query: {user_query}")

        return {
            "title": title,
            "paragraphs": combined_text[:1000],  # Limiting to first 500 characters
            "user_query": user_query
        }

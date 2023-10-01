from typing import Dict
from .plugin import Plugin  # Import Plugin dari modul plugin anda
import requests
from bs4 import BeautifulSoup

class WebScrapingPlugin(Plugin):
    """
    A plugin to scrape web content
    """
    
    def get_source_name(self) -> str:
        return "WebScraper"

    def get_spec(self) -> [Dict]:
        return [{
            "name": "get_web_content",
            "description": "Scrape web content based on URL and query",
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {"type": "string", "description": "Website URL"},
                    "query": {"type": "string", "description": "Query for the information needed"}
                },
                "required": ["url", "query"],
            },
        }]

    async def execute(self, function_name, **kwargs) -> Dict:
        try:
            url = kwargs['url']
            query = kwargs['query']

            response = requests.get(url)
            
            if response.status_code != 200:
                return {'error': f"Failed to get content. Status Code: {response.status_code}"}

            soup = BeautifulSoup(response.content, 'html.parser')
            scraped_data = soup.select(query)

            if not scraped_data:
                return {'result': 'No data found for the given query'}

            results = [element.text for element in scraped_data]
            return {'result': results}
        except Exception as e:
            return {'error': 'An unexpected error occurred: ' + str(e)}

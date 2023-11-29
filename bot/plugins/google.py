import os
import requests
from bs4 import BeautifulSoup
from typing import Dict

from .plugin import Plugin

class GoogleScholarPlugin(Plugin):
    def get_source_name(self) -> str:
        return "Google Scholar"

    def get_spec(self) -> [Dict]:
        return [{
            "name": "scholar_search",
            "description": "Execute a Google Scholar search for the given query and return a list of results",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "the user query"
                    }
                },
                "required": ["query"],
            },
        }]

    async def execute(self, function_name, **kwargs) -> Dict:
        query = kwargs.get('query', '').replace(' ', '+')
        url = f"https://scholar.google.com/scholar?q={query}"
        headers = {'User-Agent': 'Mozilla/5.0'}
        
        try:
            page = requests.get(url, headers=headers)
            soup = BeautifulSoup(page.content, 'html.parser')
            publications = soup.find_all('div', class_='gs_ri')

            results = []
            for pub in publications[:3]:
                title = pub.find('h3', class_='gs_rt').text
                author_info = pub.find('div', class_='gs_a').text
                results.append({'title': title, 'author_info': author_info})

            if not results:
                return {"Result": "No Google Scholar Results were found"}

            return {"result": results}

        except Exception as e:
            return {"Result": str(e)}

import os
from typing import Dict

from googleapiclient.discovery import build

from .plugin import Plugin

class GoogleSearchPlugin(Plugin):
    def __init__(self):
        self.api_key = os.getenv('GOOGLE_API_KEY')  # Ganti dengan variabel lingkungan Anda yang berisi kunci API Google
        self.cse_id = os.getenv('GOOGLE_CSE_ID')  # Ganti dengan ID Custom Search Engine Anda

    def get_source_name(self) -> str:
        return "Google Custom Search"

    def get_spec(self) -> [Dict]:
        return [{
            "name": "web_search",
            "description": "Execute a web search for the given query and return a list of results",
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
        if not self.api_key or not self.cse_id:
            return {"Result": "Google API Key or CSE ID is not provided"}

        service = build("customsearch", "v1", developerKey=self.api_key)

        try:
            res = service.cse().list(
                q=kwargs['query'],
                cx=self.cse_id,
                num=3  # Mengambil 3 hasil pencarian
            ).execute()
        except Exception as e:
            return {"Result": str(e)}

        items = res.get('items', [])

        if not items:
            return {"Result": "No Google Search Result was found"}

        def to_metadata(result):
            return {
                "snippet": result["snippet"],
                "title": result["title"],
                "link": result["link"],
            }

        return {"result": [to_metadata(result) for result in items]}

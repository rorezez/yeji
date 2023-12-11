import os
import requests
from typing import Dict
from .plugin import Plugin

class GoogleCustomSearchPlugin(Plugin):
    """
    A plugin to search the web for a given query, using Google Custom Search JSON API
    """

    def __init__(self):
        self.api_key = os.getenv('GOOGLE_API_KEY')
        self.cse_id = os.getenv('GOOGLE_CSE_ID')

    def get_source_name(self) -> str:
        return "Google"

    def get_spec(self) -> [Dict]:
        return [{
            "name": "web_search",
            "description": "Execute a web search for the given query and return a list of results",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The user query"
                    },
                    "language": {
                        "type": "string",
                        "enum": ["lang_ar", "lang_bg", "lang_ca", "lang_cs", "lang_da", "lang_de", 
                                "lang_el", "lang_en", "lang_es", "lang_et", "lang_fi", "lang_fr", 
                                "lang_hr", "lang_hu", "lang_id", "lang_is", "lang_it", "lang_iw", 
                                "lang_ja", "lang_ko", "lang_lt", "lang_lv", "lang_nl", "lang_no", 
                                "lang_pl", "lang_pt", "lang_ro", "lang_ru", "lang_sk", "lang_sl", 
                                "lang_sr", "lang_sv", "lang_tr", "lang_uk", "lang_zh-CN", "lang_zh-TW"],
                        "description": "The language to restrict results to. Default to 'lang_en' if not specified."
                    }
                },
                "required": ["query"]
            },
        }]


    async def execute(self, function_name, **kwargs) -> Dict:
        results = self.google_search(kwargs['query'])

        if not results:
            return {"Result": "No results found"}

        def to_metadata(result: Dict) -> Dict[str, str]:
            return {
                "snippet": result.get("snippet"),
                "title": result.get("title"),
                "link": result.get("link"),
            }

        return {"result": [to_metadata(result) for result in results]}

    def google_search(self, search_term):
        try:
            url = "https://customsearch.googleapis.com/customsearch/v1"
            params = {
                'q': search_term,
                'cx': self.cse_id,
                'key': self.api_key
            }
            response = requests.get(url, params=params)
            response.raise_for_status()  # This will raise an HTTPError if the HTTP request returned an unsuccessful status code
            search_results = response.json()
            return search_results.get('items', [])
        except requests.exceptions.RequestException as e:
            print(f"Error during Google Custom Search: {e}")
            return []

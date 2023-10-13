from typing import Dict

# Contoh import, asumsi Anda memiliki base class Plugin
from .plugin import Plugin


class WeatherPlugin(Plugin):
    """
    A plugin to fetch the current weather information
    """
    def get_source_name(self) -> str:
        return "HardcodedWeather"

    def get_spec(self) -> [Dict]:
        return [{
            "name": "get_weather",
            "description": "Get the current weather information",
            "parameters": {
                "type": "object",
                "properties": {
                    "location": {"type": "string", "description": "Location for which to get the weather"}
                },
                "required": ["location"],
            },
        }]

    async def execute(self, function_name, **kwargs) -> Dict:
        # Hardcoded untuk tujuan testing
        if kwargs['location'] == 'Jakarta':
            return {
                "temperature": "30C",
                "condition": "Sunny",
                "wind_speed": "5 km/h"
            }
        elif kwargs['location'] == 'Bandung':
            return {
                "temperature": "25C",
                "condition": "Cloudy",
                "wind_speed": "7 km/h"
            }
        else:
            return {
                "error": "Location not supported"
            }

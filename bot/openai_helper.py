import openai
import time
import logging
import os
import json

# Load translations
parent_dir_path = os.path.join(os.path.dirname(__file__), os.pardir)
translations_file_path = os.path.join(parent_dir_path, 'translations.json')
with open(translations_file_path, 'r', encoding='utf-8') as f:
    translations = json.load(f)


def localized_text(key, bot_language):
    """
    Return translated text for a key in specified bot_language.
    Keys and translations can be found in the translations.json.
    """
    try:
        return translations[bot_language][key]
    except KeyError:
        logging.warning(f"No translation available for bot_language code '{bot_language}' and key '{key}'")
        # Fallback to English if the translation is not available
        if key in translations['en']:
            return translations['en'][key]
        else:
            logging.warning(f"No english definition found for key '{key}' in translations.json")
            # return key as text
            return key
class OpenAIHelper:
    def __init__(self, config: dict):
        logging.info('Initializing OpenAIHelper')
        openai.api_key = config['api_key']
        self.client = openai.Client(api_key=openai.api_key)
        self.config = config
        self.thread_mapping = {}
        self.assistant = None
        self.current_message = []

    def get_or_create_assistant(self, name: str, model: str = "gpt-4-1106-preview"):
        logging.info(f'Getting or creating assistant with name {name} and model {model}')
        assistants = self.client.beta.assistants.list().data
        for assistant in assistants:
            if assistant.name == name:
                self.assistant = assistant
                if assistant.model != model:
                    logging.info(f'Updating assistant model from {assistant.model} to {model}')
                    self.client.beta.assistants.update(
                        assistant_id=assistant.id, model=model
                    )
                break
        else:
            self.assistant = self.client.beta.assistants.create(
                model=model,
                name=name,
                instructions="You are a personal assistant. Answer every question with emoji only.",
                tools=[{"type": "code_interpreter"}]
            )
        return self.assistant.id

    def create_thread(self, chat_id: int):
        logging.info(f'Creating thread with chat_id {chat_id}')
        if chat_id not in self.thread_mapping:
            thread = self.client.beta.threads.create()
            self.thread_mapping[chat_id] = thread.id
        return self.thread_mapping[chat_id]

    async def get_message_from_assistant(self, chat_id: int, prompt: str)-> tuple[str, str]:
        logging.info(f'Getting message from assistant for chat_id {chat_id} with prompt {prompt}')
        run_id = await self.run_assistant(chat_id=chat_id, query=prompt, assistant_id=self.assistant.id)
        while True:
            time.sleep(5)
            thread_id = self.thread_mapping.get(chat_id)
            run_status = self.client.beta.threads.runs.retrieve(thread_id=thread_id, run_id=run_id)
            if run_status.status == 'completed':
                message_list = self.client.beta.threads.messages.list(thread_id=thread_id)
                for message in message_list.data:
                    if message.id in self.current_message:
                        continue
                    else:
                        self.current_message.append(message.id)
                    return message.content[0].text.value
                break

    async def run_assistant(self, chat_id: int, query: str, assistant_id: str = None):
        logging.info(f'Running assistant for chat_id {chat_id} with query {query}')
        if not query:
            raise ValueError("Query must not be empty")
        if not assistant_id:
            raise ValueError("Assistant ID must not be empty")
        thread_id = self.thread_mapping.get(chat_id)
        if not thread_id:
            thread_id = self.create_thread(chat_id)
        self.client.beta.threads.messages.create(
            thread_id=thread_id,
            role="user",
            content=query,
        )
        run = self.client.beta.threads.runs.create(
            thread_id=thread_id,
            assistant_id=assistant_id,
        )
        logging.info(f'Run ID: {run.id}')
        return run.id
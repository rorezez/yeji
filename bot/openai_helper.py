import openai
import time
import requests
import logging
import os
import json
import asyncio
from io import BytesIO

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

    async def get_text_response(self, chat_id: int, prompt: str) -> tuple[str, str]:
        try:
            logging.info(f'Getting message from assistant for chat_id {chat_id} with prompt {prompt}')
            run_id = await self.run_assistant(chat_id=chat_id, query=prompt, assistant_id=self.assistant.id)
            
            while True:
                await asyncio.sleep(5)  # Menggunakan asyncio.sleep alih-alih time.sleep untuk non-blocking sleep
                thread_id = self.thread_mapping.get(chat_id)

                try:
                    run_status = self.client.beta.threads.runs.retrieve(thread_id=thread_id, run_id=run_id)
                    if run_status.status == 'completed':
                        message_list = self.client.beta.threads.messages.list(thread_id=thread_id)
                        for message in message_list.data:
                            if message.id not in self.current_message:
                                self.current_message.append(message.id)
                                return message.content[0].text.value
                        break
                except Exception as e:
                    logging.error(f'Error retrieving run status or processing messages: {e}')
                    # Tangani eksepsi spesifik atau berikan respons ke pengguna
                    return "", str(e)  # Atau tangani dengan cara lain sesuai kebutuhan

        except Exception as e:
            logging.error(f'Error in get_message_from_assistant: {e}')
            # Tangani eksepsi umum atau berikan respons ke pengguna
            return "", str(e)  # Atau tangani dengan cara lain sesuai kebutuhan

    async def get_file_response(self, chat_id: int, file_url: str) -> tuple[str, str]:
        try:
            logging.info(f'Getting message from assistant for chat_id {chat_id} with prompt "rangkum file ini"')
            run_id = await self.run_assistant(chat_id=chat_id, query="baca dokumen ini", assistant_id=self.assistant.id, file_url=file_url)
            
            while True:
                await asyncio.sleep(5)  # Menggunakan asyncio.sleep alih-alih time.sleep untuk non-blocking sleep
                thread_id = self.thread_mapping.get(chat_id)

                try:
                    run_status = self.client.beta.threads.runs.retrieve(thread_id=thread_id, run_id=run_id)
                    if run_status.status == 'completed':
                        message_list = self.client.beta.threads.messages.list(thread_id=thread_id)
                        for message in message_list.data:
                            if message.id not in self.current_message:
                                self.current_message.append(message.id)
                                return message.content[0].text.value
                        break
                except Exception as e:
                    logging.error(f'Error retrieving run status or processing messages: {e}')
                    # Tangani eksepsi spesifik atau berikan respons ke pengguna
                    return "", str(e)  # Atau tangani dengan cara lain sesuai kebutuhan

        except Exception as e:
            logging.error(f'Error in get_message_from_assistant: {e}')
            # Tangani eksepsi umum atau berikan respons ke pengguna
            return "", str(e)  # Atau tangani dengan cara lain sesuai kebutuhan    

    async def handle_file(self, chat_id: int, file_url: str, query: str, assistant_id: str = None):
        response = requests.get(file_url)
        file = BytesIO(response.content)
        try:
            logging.info(f'Handling file for chat_id {chat_id} with file_url {file_url}')

            thread_id = self.thread_mapping.get(chat_id)
            file_id= self.client.files.create(
                file=file,
                purpose="assistants",
            )
            self.client.beta.threads.messages.create(
                thread_id=thread_id,
                role="user",
                content=query,
                file_ids=[file_id.id],
            )
            run = self.client.beta.threads.runs.create(
                thread_id=thread_id,
                assistant_id=assistant_id,
            )
            logging.info(f'Run ID handle file: {run.id}')
            return run.id
        except Exception as e:
            logging.error(f'gagal mengirimkan file: {e}')
            # Tangani eksepsi umum atau berikan respons ke pengguna
            return "", str(e)

    async def run_assistant(self, chat_id: int, query: str, assistant_id: str = None ,file_url: str = None):
        logging.info(f'Running assistant for chat_id {chat_id} with query {query}')
        if not query:
            raise ValueError("Query must not be empty")
        if not assistant_id:
            raise ValueError("Assistant ID must not be empty")
        thread_id = self.thread_mapping.get(chat_id)
        if not thread_id:
            thread_id = self.create_thread(chat_id)
    # Cek apakah file_url diberikan
        if file_url:
            # Jika ada file_url, panggil handle_file
            
            response = requests.get(file_url)
            file = BytesIO(response.content)
            try:
                logging.info(f'Handling file for chat_id {chat_id} with file_url {file_url}')

                thread_id = self.thread_mapping.get(chat_id)
                file_id= self.client.files.create(
                    file=file,
                    purpose="assistants",
                )
                self.client.beta.threads.messages.create(
                    thread_id=thread_id,
                    role="user",
                    content=query,
                    file_ids=[file_id.id],
                )
                run = self.client.beta.threads.runs.create(
                    thread_id=thread_id,
                    assistant_id=assistant_id,
                )
                logging.info(f'Run ID handle file: {run.id}')
                return run.id
            except Exception as e:
                logging.error(f'Error handling file: {e}')
                # Tangani eksepsi umum atau berikan respons ke pengguna
                return "", str(e)
            # Anda dapat menambahkan logika tambahan di sini jika diperlukan
        else:
            # Jika tidak ada file_url, lanjutkan seperti biasa
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
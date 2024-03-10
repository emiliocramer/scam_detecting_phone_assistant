import time

from openai import OpenAIError

from src.utils import app_logger
from src.config import openai_client


def create_thread():
    try:
        return openai_client.beta.threads.create()
    except OpenAIError as e:
        app_logger.error(f"failed to create a new thread: {e}")


def send_message_to_assistant(thread_id, message):
    try:
        app_logger.debug(f"message received: {message}")
        return openai_client.beta.threads.messages.create(
            thread_id=thread_id,
            role='user',
            content=message
        )
    except OpenAIError as e:
        app_logger.error(f"Failed to send message to assistant: {e}")


def run_assistant(thread_id, assistant_id):
    try:
        return openai_client.beta.threads.runs.create(
            thread_id=thread_id,
            assistant_id=assistant_id
        )
    except OpenAIError as e:
        app_logger.error(f"Failed to run assistant: {e}")


def handle_get_assistant_response(thread_id, run_id):
    while True:
        run_status = retrieve_assistant_status(thread_id, run_id)

        if run_status.status == 'completed':
            return retrieve_assistant_response(thread_id)
        else:
            time.sleep(0.1)


def retrieve_assistant_status(thread_id, run_id):
    try:
        run_status = openai_client.beta.threads.runs.retrieve(
            thread_id=thread_id,
            run_id=run_id
        )

        return run_status
    except OpenAIError as e:
        app_logger.error(f"failed to retrieve assistant status: {e}")


def retrieve_assistant_response(thread_id):
    try:
        messages_response = openai_client.beta.threads.messages.list(thread_id)
        messages = messages_response.data
        latest_message = messages[0].content[0].text.value
        return latest_message
    except OpenAIError as e:
        app_logger.error(f"failed to retrieve assistant response: {e}")


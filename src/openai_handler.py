from openai import OpenAI

from src.config import RESPONSE_ASSISTANT_ID
from src.config import VERDICT_ASSISTANT_ID
from src.utils import check_run_status_and_get_response
client = OpenAI


def send_message_to_assistant(thread_id, message):
    return client.beta.threads.messages.create(
        thread_id=thread_id,
        role='user',
        content=message
    )


def run_assistant(thread_id):
    return client.beta.threads.runs.create(
        thread_id=thread_id,
        assistant_id=RESPONSE_ASSISTANT_ID
    )


def get_assistant_response(thread_id, run_id):
    return check_run_status_and_get_response(client, thread_id, run_id)


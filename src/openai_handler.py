from openai import OpenAI
from src.utils import check_run_status_and_get_response
from src.config import OPENAI_API_KEY
client = OpenAI(
    api_key=OPENAI_API_KEY
)


def send_message_to_assistant(thread_id, message):
    return client.beta.threads.messages.create(
        thread_id=thread_id,
        role='user',
        content=message
    )


def run_assistant(thread_id, assistant_id):
    return client.beta.threads.runs.create(
        thread_id=thread_id,
        assistant_id=assistant_id
    )


def get_assistant_response(thread_id, run_id):
    return check_run_status_and_get_response(client, thread_id, run_id)


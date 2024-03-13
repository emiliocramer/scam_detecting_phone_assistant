import os
from dotenv import load_dotenv
from openai import OpenAI
load_dotenv()

VOSK_MODEL_PATH = 'model'
VERDICT_ASSISTANT_ID = os.environ.get('VERDICT_ASSISTANT_ID')
OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')
MONGODB_ADMIN_PW = os.environ.get('MONGODB_ADMIN_PW')
openai_client = OpenAI(
    api_key=OPENAI_API_KEY
)


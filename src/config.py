import os
from dotenv import load_dotenv

load_dotenv()

TWILIO_ACCOUNT_SID = os.environ.get('TWILIO_ACCOUNT_SID')
TWILIO_AUTH_TOKEN = os.environ.get('TWILIO_AUTH_TOKEN')
VOSK_MODEL_PATH = 'model'
RESPONSE_ASSISTANT_ID = os.environ.get('RESPONSE_ASSISTANT_ID')
VERDICT_ASSISTANT_ID = os.environ.get('VERDICT_ASSISTANT_ID')
OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')

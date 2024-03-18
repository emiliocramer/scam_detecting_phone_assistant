import os
from dotenv import load_dotenv
from openai import OpenAI
from twilio.rest import Client
load_dotenv()

VOSK_MODEL_PATH = 'model'
VERDICT_ASSISTANT_ID = os.environ.get('VERDICT_ASSISTANT_ID')
OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')
TWILIO_ACCOUNT_SID = os.environ.get('TWILIO_ACCOUNT_SID')
TWILIO_AUTH_TOKEN = os.environ.get('TWILIO_AUTH_TOKEN')
MONGODB_ADMIN_PW = os.environ.get('MONGODB_ADMIN_PW')
twilio_client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
openai_client = OpenAI(
    api_key=OPENAI_API_KEY
)


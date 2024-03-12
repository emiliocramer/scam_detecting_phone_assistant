from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_sock import Sock
from datetime import datetime
from bson import ObjectId

from src.db.config import db
from src.api.profile import register_profile_api
from src.openai.openai_handler import create_thread
from src.twilio.twilio_handler import handle_incoming_call, handle_stream
from twilio.rest import Client
from src.config import TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN
from src.utils import app_logger
from src.api.twilio import register_twilio_api

twilio_client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
app = Flask(__name__)
CORS(app)
register_twilio_api(app)
register_profile_api(app)
sock = Sock(app)

call_start_time = 0
response_thread_id = 0
verdict_thread_id = 0


@app.route('/call/<userId>', methods=['POST'])
def call(user_id):
    global call_start_time, response_thread_id, verdict_thread_id
    try:
        call_start_time = datetime.now()
        response_thread = create_thread()
        verdict_thread = create_thread()
        response_thread_id, verdict_thread_id = response_thread.id, verdict_thread.id

        return handle_incoming_call(request, user_id)
    except Exception as e:
        app_logger.error(f'Error in call route with userId {user_id}: {e}', exc_info=True)
        return "An error occurred", 500


@sock.route('/stream/<user_id>')
def stream(ws, user_id):
    try:
        personal_profile_collection = db['personal_profiles']
        profile = personal_profile_collection.find_one({'_id': ObjectId(user_id)})
        if not profile:
            return jsonify({'error': 'Profile not found'}), 404

        response_assistant_id = str(profile['assistant_id'])
        return handle_stream(ws, response_thread_id, verdict_thread_id, call_start_time, response_assistant_id)
    except Exception as e:
        app_logger.error(f'Error in stream route: {e}', exc_info=True)
        return "An error occurred", 500


if __name__ == '__main__':
    port = '5014'
    app.run(port=int(port))




from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_sock import Sock
from datetime import datetime
from bson import ObjectId
import logging
import os

from src.db.config import db
from src.api.profile import register_profile_api
from src.openai.openai_handler import create_thread
from src.twilio.twilio_handler import handle_incoming_call, handle_stream
from twilio.rest import Client
from src.utils import app_logger
from src.api.auth import register_auth_api

app_logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
app_logger.addHandler(handler)

app = Flask(__name__)
CORS(app)
register_auth_api(app)
register_profile_api(app)
sock = Sock(app)

call_start_time = 0
openai_ids = {}


@app.route('/call/<user_id>', methods=['POST'])
def call(user_id):
    global call_start_time, openai_ids
    try:
        call_start_time = datetime.now()
        response_thread = create_thread()
        verdict_thread = create_thread()

        openai_ids['verdict_thread_id'] = verdict_thread.id
        openai_ids['response_thread_id'] = response_thread.id

        return handle_incoming_call(request, user_id)
    except Exception as e:
        app_logger.error(f'Error in call route with userId {user_id}: {e}', exc_info=True)
        return "An error occurred", 500


@sock.route('/stream/<user_id>')
def stream(ws, user_id):
    global openai_ids
    try:
        profile = db['personal_profiles'].find_one({'_id': ObjectId(user_id)})
        if not profile:
            app_logger.error(f'Profile not found for userId {user_id}')
            return jsonify({'error': 'Profile not found'}), 404

        openai_ids['response_assistant_id'] = str(profile['assistant_id'])
        closing_line = profile['closing_line']

        twilio_user = db['twilio_users'].find_one({'_id': ObjectId(user_id)})
        if not twilio_user:
            app_logger.error(f'twilio user not found for userId {user_id}')
            return jsonify({'error': 'Twilio User not found'}), 404

        twilio_client = Client(twilio_user['account_sid'], twilio_user['auth_token'])
        return handle_stream(ws, call_start_time, openai_ids, closing_line, twilio_client)
    except Exception as e:
        app_logger.error(f'Error in stream route: {e}', exc_info=True)
        return "An error occurred", 500


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5014))
    app.run(host='0.0.0.0', port=port)

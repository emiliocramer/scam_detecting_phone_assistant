from flask import Blueprint, request, jsonify
from src.db.config import db
from bson import ObjectId
from twilio.rest import Client
from pyngrok import ngrok

from src.openai.openai_handler import create_assistant

twilio_api = Blueprint('twilio_api', __name__)


@twilio_api.route('/api/twilio/create-user', methods=['POST'])
def create_twilio_user():
    try:
        data = request.get_json()
        account_sid = data.get('account_sid')
        auth_token = data.get('auth_token')

        if not account_sid or not auth_token:
            return jsonify({'error': 'Missing account_sid or auth_token'}), 400

        twilio_users_collection = db['twilio_users']
        existing_user = twilio_users_collection.find_one({'account_sid': account_sid})

        if existing_user:
            return jsonify({'error': 'A user with this account_sid already exists'}), 409

        user_id = ObjectId()
        user_data = {
            '_id': user_id,
            'account_sid': account_sid,
            'auth_token': auth_token
        }

        personal_assistant = create_assistant("")

        result = twilio_users_collection.insert_one(user_data)
        personal_profile_data = {
            '_id': user_id,
            'assistant_id': personal_assistant.id,
            'full_name': "",
            'available_schedule': "",
            'birthdate': "",
            'city': "",
            'profession': "",
            'interests': "",
        }

        personal_profile_collection = db['personal_profiles']
        personal_profile_collection.insert_one(personal_profile_data)

        return jsonify({'message': 'Data inserted successfully', 'user_id': str(user_id)}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@twilio_api.route('/api/twilio/configure-phone', methods=['POST'])
def configure_twilio_phone():
    try:
        data = request.get_json()
        account_sid = data.get('account_sid')
        auth_token = data.get('auth_token')
        user_id = data.get('user_id')
        if not account_sid or not auth_token or not user_id:
            return jsonify({'error': 'Missing account_sid or auth_token or user_id'}), 400

        twilio_client = Client(account_sid, auth_token)

        port = '5014'
        public_url = ngrok.connect(port, bind_tls=True).public_url
        new_voice_url = f'{public_url}/call/{user_id}'
        number = twilio_client.incoming_phone_numbers.list()[0]
        number.update(voice_url=new_voice_url)

        return jsonify({'message': 'Voice URL updated successfully'}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


def register_twilio_api(app):
    app.register_blueprint(twilio_api)

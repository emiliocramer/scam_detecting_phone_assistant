from flask import Blueprint, request, jsonify
from src.db.config import db
from bson import ObjectId

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

        result = twilio_users_collection.insert_one(user_data)
        personal_profile_data = {
            '_id': user_id,
            'full_name': "",
            'available_schedule': "",
            'birthdate': "",
        }

        personal_profile_collection = db['personal_profiles']
        personal_profile_collection.insert_one(personal_profile_data)

        return jsonify({'message': 'Data inserted successfully', 'user_id': str(user_id)}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


def register_twilio_api(app):
    app.register_blueprint(twilio_api)
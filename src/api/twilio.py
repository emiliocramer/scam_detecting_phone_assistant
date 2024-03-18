from flask import Blueprint, request, jsonify
from src.db.config import db
from bson import ObjectId
from src.config import twilio_client
from src.openai.openai_handler import create_assistant

twilio_api = Blueprint('twilio_api', __name__)


@twilio_api.route('/api/twilio/get-available-numbers', methods=['GET'])
def get_available_numbers():
    try:
        # Assuming you want to fetch available phone numbers for a specific country, e.g., US
        # Adjust the parameters according to your needs
        available_numbers = twilio_client.incoming_phone_numbers.list()

        # Format the response as needed, this is a basic example
        numbers_list = [{'number': number.phone_number, 'friendlyName': number.friendly_name} for number in available_numbers]

        return jsonify(numbers_list)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@twilio_api.route('/api/twilio/get-active-number/<user_id>', methods=['GET'])
def get_active_number(user_id):
    try:
        user_accounts_collection = db['user_accounts']
        account = user_accounts_collection.find_one({'_id': ObjectId(user_id)})
        if not account:
            return jsonify({'error': 'account not found'}), 404

        return jsonify({'active_number': account.get('number', 'No active number associated to this account')}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


def register_twilio_api(app):
    app.register_blueprint(twilio_api)

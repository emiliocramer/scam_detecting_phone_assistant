from flask import Blueprint, request, jsonify
from src.db.config import db
from bson import ObjectId
from src.config import twilio_client
from src.openai.openai_handler import create_assistant

twilio_api = Blueprint('twilio_api', __name__)


@twilio_api.route('/api/twilio/get-available-numbers', methods=['GET'])
def get_available_numbers():
    return twilio_client.incoming_phone_numbers.list()


def register_twilio_api(app):
    app.register_blueprint(twilio_api)

from flask import Blueprint, request, jsonify
from src.db.config import db
from bson import ObjectId

from src.openai.openai_handler import create_assistant
from werkzeug.security import check_password_hash, generate_password_hash

auth_api = Blueprint('auth_api', __name__)


@auth_api.route('/api/auth/create-user', methods=['POST'])
def create_new_user():
    try:
        data = request.get_json()
        username = data.get('username')
        email = data.get('email')
        password = data.get('password')

        if not username or not email or not password:
            return jsonify({'error': 'Missing username or email or password'}), 400

        existing_email = db['user_accounts'].find_one({'email': email})
        if existing_email:
            return jsonify({
                'message': 'This email is already in use.',
                'user_id': str(existing_email['_id'])
            }), 400

        existing_username = db['user_accounts'].find_one({'username': username})
        if existing_username:
            return jsonify({
                'message': 'This username is already taken.',
                'user_id': str(existing_username['_id'])
            }), 400

        hashed_password = generate_password_hash(password, method='sha256')

        user_id = ObjectId()
        user_data = {
            '_id': user_id,
            'username': username,
            'email': email,
            'password': hashed_password
        }

        personal_assistant = create_assistant("")
        result = db['user_accounts'].insert_one(user_data)
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
        db['personal_profiles'].insert_one(personal_profile_data)
        return jsonify({'message': 'Data inserted successfully', 'user_id': str(user_id)}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@auth_api.route('/api/auth/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        email = data.get('email')
        password = data.get('password')

        if not email or not password:
            return jsonify({'error': 'Missing username or password'}), 400

        user = db['user_accounts'].find_one({'email': email})
        if user and check_password_hash(user['password'], password):
            return jsonify({'message': 'Login successful', 'user_id': str(user['_id'])}), 200
        else:
            return jsonify({'error': 'Invalid email or password'}), 401

    except Exception as e:
        return jsonify({'error': str(e)}), 500


def register_auth_api(app):
    app.register_blueprint(auth_api)

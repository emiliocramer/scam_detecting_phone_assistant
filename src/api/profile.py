from flask import request, jsonify, Blueprint
from src.db.config import db
from src.api.twilio import twilio_api
from bson import ObjectId

profile_api = Blueprint('profile_api', __name__)


@profile_api.route('/api/profile/<user_id>', methods=['GET'])
def get_user_profile(user_id):
    try:
        personal_profile_collection = db['personal_profiles']
        profile = personal_profile_collection.find_one({'_id': ObjectId(user_id)})

        if not profile:
            return jsonify({'error': 'Profile not found'}), 404

        profile['_id'] = str(profile['_id'])
        return jsonify(profile), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@profile_api.route('/api/profile/<user_id>', methods=['PUT'])
def update_user_profile(user_id):
    try:
        data = request.get_json()
        personal_profile_collection = db['personal_profiles']

        existing_profile = personal_profile_collection.find_one({'_id': ObjectId(user_id)})
        if not existing_profile:
            return jsonify({'error': 'Profile not found'}), 404

        result = personal_profile_collection.update_one(
            {'_id': ObjectId(user_id)},
            {'$set': {
                'assistant_id': data['assistant_id'],
                'available_schedule': data['available_schedule'],
                'birthdate': data['birthdate'],
                'city': data['city'],
                'full_name': data['full_name'],
                'interests': data['interests'],
                'profession': data['profession']
            }}
        )

        if result.modified_count == 0:
            return jsonify({'message': 'No changes were made to the profile'}), 200

        return jsonify({'message': 'Profile updated successfully'}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


def register_profile_api(app):
    app.register_blueprint(profile_api)
import json
import time
from bson import ObjectId
from flask import jsonify
from flask_sock import ConnectionClosed
from twilio.twiml.voice_response import VoiceResponse, Start, Record
import vosk

from src.twilio.twilio_helpers import handle_incoming_packet
from src.utils import save_call_log, app_logger
from src.config import VOSK_MODEL_PATH
from src.db.config import db

model = vosk.Model(VOSK_MODEL_PATH)
CL = '\x1b[0K'
BS = '\x08'

call_sid = ""
lines = []
rec = vosk.KaldiRecognizer(model, 16000)
utterance = ''
silence_counter = 0


def handle_incoming_call(request, user_id):
    global call_sid
    try:
        app_logger.info(f"Handling incoming call - SID: {call_sid}, UserID: {user_id}")

        profile = db['personal_profiles'].find_one({'_id': ObjectId(user_id)})
        if not profile:
            app_logger.error(f"Profile not found - UserID: {user_id}")
            return jsonify({'error': 'Profile not found'}), 404

        response = VoiceResponse()
        start = Start()
        stream_url = f'wss://{request.host}/stream/{user_id}'
        start.stream(url=stream_url)
        response.append(start)
        app_logger.info(f"Streaming setup - URL: {stream_url}")

        opening_line = profile.get('opening_line', 'Hello, your call is very important to us.')
        response.say(opening_line)
        app_logger.info(f"Opening line delivered - UserID: {user_id}, Line: {opening_line}")

        record_timeout = 10000
        record = Record(timeout=record_timeout)
        response.append(record)
        app_logger.info(f"Call recording started - Timeout: {record_timeout}ms")

        return str(response), 200, {'Content-Type': 'text/xml'}
    except Exception as e:
        app_logger.error(f"Error handling incoming call - UserID: {user_id}, Error: {e}")
        return jsonify({'error': 'Internal Server Error'}), 500


def handle_stream(ws, call_start_time, openai_ids, closing_line):
    app_logger.debug("entered audio stream")
    global lines
    global rec
    global utterance
    global silence_counter

    try:
        time.sleep(5)
        app_logger.debug("began processing audio")
        while True:
            message = ws.receive()
            packet = json.loads(message)
            if packet['event'] == 'media':
                utterance, silence_counter, lines = handle_incoming_packet(
                    packet,
                    rec,
                    utterance,
                    silence_counter,
                    lines,
                    call_sid,
                    openai_ids,
                    closing_line,
                )

    except ConnectionClosed:
        # save_call_log(call_start_time, lines)

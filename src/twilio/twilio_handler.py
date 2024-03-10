import json
import time
from flask_sock import ConnectionClosed
from twilio.twiml.voice_response import VoiceResponse, Start, Record
import vosk

from src.twilio.twilio_helpers import handle_incoming_packet
from src.utils import save_call_log, app_logger
from src.config import VOSK_MODEL_PATH

model = vosk.Model(VOSK_MODEL_PATH)
CL = '\x1b[0K'
BS = '\x08'

call_sid = ""
lines = []
rec = vosk.KaldiRecognizer(model, 16000)
utterance = ''
silence_counter = 0


def handle_incoming_call(request):
    global call_sid
    call_sid = request.form["CallSid"]
    response = VoiceResponse()
    start = Start()
    start.stream(url=f'wss://{request.host}/stream')
    response.append(start)
    response.say('Hey... this is emilio\'s assistant, how can i help you today?.')
    record = Record(timeout=10000)
    response.append(record)
    print(f'Incoming call from {request.form["From"]}')
    return str(response), 200, {'Content-Type': 'text/xml'}


def handle_stream(ws, response_thread_id, verdict_thread_id, call_start_time):
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
                    response_thread_id,
                    verdict_thread_id,
                    lines,
                    call_sid
                )

    except ConnectionClosed:
        save_call_log(call_start_time, lines)

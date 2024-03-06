import json
import audioop
import base64
from datetime import datetime
from flask_sock import ConnectionClosed
from twilio.twiml.voice_response import VoiceResponse, Start
import vosk

from app import call_start_time
from src.config import VOSK_MODEL_PATH
from src.openai_handler import send_message_to_assistant, run_assistant, get_assistant_response
from src.utils import save_call_log, get_float_verdict

model = vosk.Model(VOSK_MODEL_PATH)


def handle_incoming_call(request):
    response = VoiceResponse()
    start = Start()
    start.stream(url=f'wss://{request.host}/stream')
    response.append(start)
    response.say('Hey... this is emilio\'s assistant, how can i help you today?.')
    response.pause(length=1000)
    print(f'Incoming call from {request.form["From"]}')
    return str(response), 200, {'Content-Type': 'text/xml'}


def handle_stream(ws, response_thread_id, verdict_thread_id):
    lines = []
    rec = vosk.KaldiRecognizer(model, 16000)
    buffer = ""
    silence_threshold = 20
    silence_counter = 0
    voice_response = VoiceResponse()

    try:
        while True:
            message = ws.receive()
            packet = json.loads(message)
            if packet['event'] == 'media':
                audio = base64.b64decode(packet['media']['payload'])
                audio = audioop.ulaw2lin(audio, 2)
                audio = audioop.ratecv(audio, 2, 1, 8000, 16000, None)[0]
                is_silence = audioop.rms(audio, 2) < silence_threshold

                if not is_silence:
                    if rec.AcceptWaveform(audio):
                        result = json.loads(rec.Result())
                        buffer += result.get('text', '') + " "
                        silence_counter = 0
                    else:
                        result = json.loads(rec.PartialResult())
                        buffer += result.get('partial', '') + " "
                        silence_counter = 0
                else:
                    silence_counter += 1

                if silence_counter >= 10:
                    if buffer.strip():

                        # construct message and send to assistant
                        _ = send_message_to_assistant(thread_id=response_thread_id, message=buffer.strip())
                        response_run = run_assistant(thread_id=response_thread_id)
                        line = {
                            'speaker': 'caller',
                            'text': buffer.strip(),
                            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        }
                        lines.append(line)

                        response = get_assistant_response(thread_id=response_thread_id, run_id=response_run.id)
                        voice_response.say(response)
                        response_line = {
                            'speaker': 'assistant',
                            'text': response,
                            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        }
                        lines.append(response_line)

                        # construct active verdict
                        _ = send_message_to_assistant(thread_id=verdict_thread_id, message=lines)
                        verdict_run = run_assistant(thread_id=verdict_thread_id)
                        verdict = get_assistant_response(thread_id=verdict_thread_id, run_id=verdict_run.id)
                        float_verdict = get_float_verdict(verdict)
                        if float_verdict > 0.85:
                            voice_response.say("I'm sorry but I've detected an ongoing scam, please refrain from calling again, thank you")
                            voice_response.hangup()
                        if float_verdict < 0.2:
                            voice_response.say("Thanks for going through emilio's assistant, i'm connecting you to him now, have a good day")
                            voice_response.hangup()

                        buffer = ""
                    silence_counter = 0
    except ConnectionClosed:
        save_call_log(call_start_time, lines)

import json
import audioop
import base64
import time
from datetime import datetime
from flask_sock import ConnectionClosed
from twilio.twiml.voice_response import VoiceResponse, Start, Record
from twilio.rest import Client
import vosk

from src.openai_handler import send_message_to_assistant, run_assistant, get_assistant_response
from src.utils import save_call_log, get_float_verdict

from src.config import VOSK_MODEL_PATH
from src.config import RESPONSE_ASSISTANT_ID
from src.config import VERDICT_ASSISTANT_ID
from src.config import TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN
twilio_client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

model = vosk.Model(VOSK_MODEL_PATH)
CL = '\x1b[0K'
BS = '\x08'
call_sid = ""


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
    print("entered stream")
    lines = []
    rec = vosk.KaldiRecognizer(model, 16000)
    utterance = ''
    silence_counter = 0
    voice_response = VoiceResponse()

    try:
        time.sleep(5)
        print("detecting audio")
        while True:
            message = ws.receive()
            packet = json.loads(message)
            if packet['event'] == 'media':
                audio = base64.b64decode(packet['media']['payload'])
                audio = audioop.ulaw2lin(audio, 2)
                audio = audioop.ratecv(audio, 2, 1, 8000, 16000, None)[0]

                if rec.AcceptWaveform(audio):
                    print("accepting waveform")
                    result = json.loads(rec.Result())
                    utterance += result.get('text', '') + " "
                    print(result['text'] + ' ' + '\n')
                    silence_counter = 0
                else:
                    partial = json.loads(rec.PartialResult())
                    if not partial.get('partial'):
                        silence_counter += 1
                        if silence_counter % 100 == 0:
                            print(f"seconds of silence: {silence_counter / 100}")

                if silence_counter > 175:
                    print("silence threshold met")
                    print(utterance)
                    if utterance.strip() != "":
                        process_utterance(ws, utterance.strip(), lines, response_thread_id, verdict_thread_id, voice_response)
                    utterance = ""
                    rec = vosk.KaldiRecognizer(model, 16000)
                    silence_counter = 0
    except ConnectionClosed:
        save_call_log(call_start_time, lines)


def process_utterance(ws, utterance, lines, response_thread_id, verdict_thread_id, voice_response):
    print("detected end of sentence, generating response...")
    print(f"sending the following message to the assistant: {utterance}")
    # construct message and send to assistant
    _ = send_message_to_assistant(thread_id=response_thread_id, message=utterance)
    response_run = run_assistant(thread_id=response_thread_id, assistant_id=RESPONSE_ASSISTANT_ID)
    line = {
        'speaker': 'caller',
        'text': utterance,
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }
    lines.append(line)

    response = get_assistant_response(thread_id=response_thread_id, run_id=response_run.id)
    print("response generated")
    print(f"response: {response}")
    twiml_response = f'<Response><Say>{response}</Say></Response>'
    update_call_with_action(call_sid, twiml_response)
    # voice_response.say(response)
    response_line = {
        'speaker': 'assistant',
        'text': response,
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }
    lines.append(response_line)

    # construct active verdict
    _ = send_message_to_assistant(thread_id=verdict_thread_id, message=str(lines))
    verdict_run = run_assistant(thread_id=verdict_thread_id, assistant_id=VERDICT_ASSISTANT_ID)
    verdict = get_assistant_response(thread_id=verdict_thread_id, run_id=verdict_run.id)
    print("verdict generated")
    print(f"verdict: {verdict}")

    # float_verdict = get_float_verdict(verdict)
    # if float_verdict > 0.9 and len(lines) > 2:
    #     twiml_response = f'<Response><Say>I\'m sorry but I\'ve detected an ongoing scam, please refrain from calling again, thank you</Say></Response>'
    #     update_call_with_action(call_sid, twiml_response)
    #     # voice_response.say("I'm sorry but I've detected an ongoing scam, please refrain from calling again, thank you")
    #     voice_response.hangup()
    # if float_verdict < 0.1 and len(lines) > 2:
    #     twiml_response = f'<Response><Say>Thanks for going through emilio\'s assistant, i\'m connecting you to him now, have a good day</Say></Response>'
    #     update_call_with_action(call_sid, twiml_response)
    #     # voice_response.say("Thanks for going through emilio's assistant, i'm connecting you to him now, have a good day")
    #     voice_response.hangup()


def update_call_with_action(call_sid, twiml_response):
    call = twilio_client.calls(call_sid).update(twiml=twiml_response)
    print(f"Call updated with response: {call.sid}")

import audioop
import base64
import json
import os
import time
from datetime import datetime
from dotenv import load_dotenv
from flask import Flask, request
from flask_sock import Sock, ConnectionClosed
from twilio.twiml.voice_response import VoiceResponse, Start
from twilio.rest import Client
from openai import OpenAI
import vosk
import ssl
import pathlib

 # setup
ssl._create_default_https_context = ssl._create_unverified_context
client = OpenAI

load_dotenv()

app = Flask(__name__)
sock = Sock(app)
twilio_client = Client()
model = vosk.Model('model')
thread_id = None

# Ensure a directory for call logs exists
pathlib.Path('./call_logs').mkdir(parents=True, exist_ok=True)


def save_call_log(call_start_time, lines):
    filename = f'./call_logs/{call_start_time.strftime("%Y-%m-%d_%H-%M-%S")}_call_log.json'
    with open(filename, 'w') as file:
        json.dump(lines, file, indent=4)
    print(f'Call log saved to {filename}')


def check_run_status_and_get_response(thread_id, run_id):
    while True:
        # receive run status
        run_status = client.beta.threads.runs.retrieve(
            thread_id=thread_id,
            run_id=run_id
        )

        if run_status.status == 'completed':
            # get message response
            messages_response = client.beta.threads.messages.list(
                thread_id
            )
            messages = messages_response.data
            latest_message = messages[0].content[0].text.value
            return latest_message
        else:
            time.sleep(0.1)


@app.route('/call', methods=['POST'])
def call():
    # setup globals & initialize thread
    global call_start_time
    global thread_id
    call_start_time = datetime.now()
    thread = client.beta.threads.create()
    thread_id = thread.id

    response = VoiceResponse()
    start = Start()
    start.stream(url=f'wss://{request.host}/stream')
    response.append(start)
    response.say('Hey... this is emilio\'s assistant, how can i help you today?.')
    response.pause(length=60)
    print(f'Incoming call from {request.form["From"]}')
    return str(response), 200, {'Content-Type': 'text/xml'}


@sock.route('/stream')
def stream(ws):
    global lines
    lines = []  # Reset lines for a new call
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
                if rec.AcceptWaveform(audio):
                    result = json.loads(rec.Result())
                    buffer += result.get('text', '') + " "
                    silence_counter = 0
                elif not is_silence:
                    result = json.loads(rec.PartialResult())
                    buffer += result.get('partial', '') + " "
                    silence_counter = 0
                else:
                    silence_counter += 1

                if silence_counter >= 10:
                    if buffer.strip():

                        # send to assistant
                        message_to_assistant = client.beta.threads.messages.create(
                            thread_id=thread_id,
                            role='user',
                            content=buffer.strip()
                        )

                        # run the thread
                        run = client.beta.threads.runs.create(
                            thread_id=thread_id,
                            assistant_id='asst_MUf6wD5zlLsIDa5lU4hu8pKq'
                        )
                        # add to log
                        line = {
                            'speaker': 'caller',
                            'text': buffer.strip(),
                            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        }
                        lines.append(line)

                        # await response
                        response = check_run_status_and_get_response(thread_id=thread_id, run_id=run.id)
                        voice_response.say(response)

                        # add response to log
                        response_line = {
                            'speaker': 'assistant',
                            'text': response,
                            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        }
                        lines.append(response_line)

                        buffer = ""
                    silence_counter = 0
    except ConnectionClosed:
        save_call_log(call_start_time, lines)


if __name__ == '__main__':
    from pyngrok import ngrok
    port = 5010
    public_url = ngrok.connect(port, bind_tls=True).public_url
    number = twilio_client.incoming_phone_numbers.list()[0]
    number.update(voice_url=public_url + '/call')
    print(f'Waiting for calls on {number.phone_number}')
    app.run(port=port)

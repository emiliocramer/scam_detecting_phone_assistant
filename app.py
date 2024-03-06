from flask import Flask, request
from datetime import datetime
from src.openai_handler import client

# twilio
from src.twilio_handler import handle_incoming_call, handle_stream
from twilio.rest import Client
from src.config import TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN

twilio_client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
app = Flask(__name__)

# globals
call_start_time = 0
response_thread_id = 0
verdict_thread_id = 0


@app.route('/call', methods=['POST'])
def call():
    global call_start_time
    global response_thread_id
    global verdict_thread_id
    call_start_time = datetime.now()
    response_thread = client.beta.threads.create()
    verdict_thread = client.beta.threads.create()
    response_thread_id, verdict_thread_id = response_thread.id, verdict_thread.id

    return handle_incoming_call(request)


@app.route('/stream', methods=['GET'])
def stream():
    return handle_stream(
        request.environ.get('wsgi.websocket'),
        response_thread_id,
        verdict_thread_id,
        call_start_time
    )


if __name__ == '__main__':
    from pyngrok import ngrok

    port = '5010'
    public_url = ngrok.connect(port, bind_tls=True).public_url
    number = twilio_client.incoming_phone_numbers.list()[0]
    number.update(voice_url=public_url + '/call')
    print(f'Waiting for calls on {number.phone_number}')
    app.run(port=int(port))

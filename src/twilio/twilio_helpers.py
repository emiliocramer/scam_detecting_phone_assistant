import audioop
import base64
import json

from twilio.base.exceptions import TwilioRestException

from src.openai.openai_handler import send_message_to_assistant, run_assistant, handle_get_assistant_response
from src.config import RESPONSE_ASSISTANT_ID
from src.config import VERDICT_ASSISTANT_ID
from src.config import twilio_client
from src.utils import add_line_to_log, app_logger

call_sid = ""


def handle_incoming_packet(packet, rec, utterance, silence_counter, response_thread_id, verdict_thread_id, lines, sid):
    global call_sid
    call_sid = sid

    audio = base64.b64decode(packet['media']['payload'])
    audio = audioop.ulaw2lin(audio, 2)
    audio = audioop.ratecv(audio, 2, 1, 8000, 16000, None)[0]

    if rec.AcceptWaveform(audio):
        utterance += handle_accepted_waveform(rec)
    else:
        silence_counter = is_partial_waveform(rec, silence_counter)

    if silence_counter > 100:
        silence_counter, utterance, lines = handle_process_utterance(
            utterance,
            response_thread_id,
            verdict_thread_id,
            lines
        )

    return utterance, silence_counter, lines


def handle_accepted_waveform(rec):
    result = json.loads(rec.Result())
    app_logger.debug(f"accepted complete text: {result['text']}")

    return result.get('text', '') + " "


def is_partial_waveform(rec, silence_counter):
    partial = json.loads(rec.PartialResult())
    if not partial.get('partial'):
        silence_counter += 1
        return silence_counter
    return 0


def handle_process_utterance(utterance, response_thread_id, verdict_thread_id, lines):
    updated_lines = lines
    app_logger.debug("silence threshold met")

    if utterance.strip() != "":
        updated_lines = process_utterance(utterance.strip(), lines, response_thread_id, verdict_thread_id)
    return 0, "", updated_lines


def process_utterance(utterance, lines, response_thread_id, verdict_thread_id):
    app_logger.debug(f"sending the following message to the assistant: {utterance}")

    log_with_response = generate_response(response_thread_id, utterance, lines)
    log_with_verdict = generate_verdict(verdict_thread_id, log_with_response)

    return log_with_verdict


def generate_response(response_thread_id, utterance, lines):
    _ = send_message_to_assistant(thread_id=response_thread_id, message=utterance)
    response_run = run_assistant(thread_id=response_thread_id, assistant_id=RESPONSE_ASSISTANT_ID)

    lines = add_line_to_log(lines, utterance, 'caller')
    response = handle_get_assistant_response(thread_id=response_thread_id, run_id=response_run.id)
    app_logger.debug(f"response generated: {response}")

    twiml_response = f'<Response><Say>{response}</Say><Pause length="30" /></Response>'
    update_call_with_action(twiml_response)

    lines = add_line_to_log(lines, response, 'assistant')
    return lines


def generate_verdict(verdict_thread_id, lines):
    _ = send_message_to_assistant(thread_id=verdict_thread_id, message=str(lines))
    verdict_run = run_assistant(thread_id=verdict_thread_id, assistant_id=VERDICT_ASSISTANT_ID)
    verdict = handle_get_assistant_response(thread_id=verdict_thread_id, run_id=verdict_run.id)
    app_logger.debug(f"verdict generated: {verdict}")

    lines[-1]['is_scam_prediction'] = verdict
    return lines


def update_call_with_action(twiml_response):
    try:
        call = twilio_client.calls(call_sid).update(twiml=twiml_response)
        app_logger.debug(f"Call updated with response: {call.sid}")
    except TwilioRestException as e:
        app_logger.error(f'Failed to update call: {e}')

import audioop
import base64
import json

from twilio.base.exceptions import TwilioRestException

from src.openai.openai_handler import send_message_to_assistant, run_assistant, handle_get_assistant_response
from src.config import VERDICT_ASSISTANT_ID
from src.utils import add_line_to_log, app_logger
from src.config import twilio_client

call_sid = ""


def handle_incoming_packet(packet, rec, utterance, silence_counter, lines, sid, openai_ids, closing_line):
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
            lines,
            openai_ids,
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


def handle_process_utterance(utterance, lines, openai_ids):
    updated_lines = lines
    app_logger.debug("silence threshold met")

    if utterance.strip() != "":
        updated_lines = process_utterance(
            utterance.strip(),
            lines,
            openai_ids,
        )
    return 0, "", updated_lines


def process_utterance(utterance, lines, openai_ids):
    app_logger.debug(f"sending the following message to the assistant: {utterance}")

    log_with_response = generate_response(
        openai_ids['response_thread_id'],
        utterance,
        lines,
        openai_ids['response_assistant_id'],
    )
    log_with_verdict = generate_verdict(openai_ids['verdict_thread_id'], log_with_response)

    return log_with_verdict


def generate_response(response_thread_id, utterance, lines, response_assistant_id):
    _ = send_message_to_assistant(thread_id=response_thread_id, message=utterance)
    response_run = run_assistant(thread_id=response_thread_id, assistant_id=response_assistant_id)

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
        if not call_sid:
            app_logger.error('No call SID available to update the call.')
            return

        app_logger.debug(f"Attempting to update call with TwiML: {twiml_response}")

        call = twilio_client.calls(call_sid).update(twiml=twiml_response)
        app_logger.info(f"Call updated with response: {twiml_response}")
    except TwilioRestException as e:
        app_logger.error(f'Failed to update call: {e.msg} - Code: {e.code}')

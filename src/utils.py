import json
import time


def save_call_log(call_start_time, lines):
    filename = f'./call_logs/{call_start_time.strftime("%Y-%m-%d_%H-%M-%S")}_call_log.json'
    with open(filename, 'w') as file:
        json.dump(lines, file, indent=4)
    print(f'Call log saved to {filename}')


def check_run_status_and_get_response(client, thread_id, run_id):
    while True:
        run_status = client.beta.threads.runs.retrieve(
            thread_id=thread_id,
            run_id=run_id
        )

        if run_status.status == 'completed':
            messages_response = client.beta.threads.messages.list(thread_id)
            messages = messages_response.data
            latest_message = messages[0].content[0].text.value
            return latest_message
        else:
            time.sleep(0.1)


def get_float_verdict(verdict):
    try:
        float_verdict = float(verdict)
        return float_verdict
    except ValueError:
        return 0.0



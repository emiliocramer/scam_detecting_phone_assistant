import logging
from logging.handlers import RotatingFileHandler
import os
import json

# Logging setup
if not os.path.exists('logs'):
    os.makedirs('logs')
log_file_path = os.path.join('logs', 'app.log')
file_handler = RotatingFileHandler(log_file_path, maxBytes=10240, backupCount=10)
file_handler.setFormatter(logging.Formatter(
    '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
))
file_handler.setLevel(logging.INFO)
app_logger = logging.getLogger('appLogger')
app_logger.setLevel(logging.INFO)
app_logger.addHandler(file_handler)
app_logger.info('Application startup')


def save_call_log(call_start_time, lines):
    filename = f'./call_logs/{call_start_time.strftime("%Y-%m-%d_%H-%M-%S")}_call_log.json'
    with open(filename, 'w') as file:
        json.dump(lines, file, indent=4)
    app_logger.debug(f'Call log saved to {filename}')


def get_float_verdict(verdict):
    try:
        float_verdict = float(verdict)
        return float_verdict
    except ValueError:
        app_logger.error("failure to convert verdict to float, returned 0.0")
        return 0.0


def add_line_to_log(lines, line, role):
    line = {
        'speaker': role,
        'text': line,
    }
    lines.append(line)

    return lines




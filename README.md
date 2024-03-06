# README for the Flask-Based Voice Assistant Application

This README document provides an overview and setup instructions for a Flask-based voice assistant application designed to process incoming phone calls and evaluate them for potential scams. By integrating OpenAI's beta Assistant API for dynamic response generation and conversation analysis, Twilio for voice communication, Vosk for speech-to-text conversion, and ngrok for exposing a local development server to the Internet, the application acts as a sophisticated intermediary capable of detecting and responding to potential scam attempts over the phone.

## Overview

The application leverages advanced speech recognition and artificial intelligence to serve as an intermediary voice assistant. It processes incoming phone calls via Twilio, converts speech to text using Vosk, and interacts with OpenAI's API to generate appropriate responses and make decisions based on the content of the conversation. Its primary goal is to detect potential scams during the call, providing an additional layer of security and peace of mind for the user.

### Key Features

- **Scam Detection**: Utilizes OpenAI's beta Assistant API to analyze conversations in real-time and identify potential scams.
- **Incoming Call Handling**: Accepts incoming calls, provides a welcoming greeting, and streams call audio for processing.
- **Speech-to-Text Conversion**: Employs Vosk for accurate offline speech recognition, converting call audio to text.
- **Dynamic Response Generation**: Generates contextually appropriate responses based on the caller's input through interaction with OpenAI's API.
- **Conversation Evaluation**: Analyzes the textual content of the conversation to make informed decisions, such as scam identification.
- **Call Logging**: Archives a detailed log of the conversation, including timestamps and the transcribed text, for review and record-keeping.

### Components

- `app.py`: Sets up the Flask application, including routes and server initialization.
- `src/openai_handler.py`: Manages interactions with OpenAI's API for sending messages and processing responses.
- `src/twilio_handler.py`: Handles the mechanics of incoming calls and audio streaming using Twilio's services.
- `src/utils.py`: Provides utility functions for operations like saving call logs and processing responses.
- `src/config.py`: Contains configuration settings, including management of environment variables.

## Setup Instructions

### Prerequisites

- Python 3.8 or later
- Flask
- ngrok account and setup
- Twilio account with a voice-capable phone number
- OpenAI API access
- Vosk and a Vosk model for speech recognition

### Installation Steps

#### Environment Setup:

Clone the repository to your local machine. Navigate to the project directory and create a virtual environment:

```sh
python -m venv venv
source venv/bin/activate  # On Windows use `venv\Scripts\activate`
```

#### Install Dependencies:
Install the required Python packages:

```sh
pip install flask twilio pyngrok openai vosk flask_sock dotenv
```

#### Environment Variables:
Create a .env file in the project root with the following variables:
```sh
TWILIO_ACCOUNT_SID=your_twilio_account_sid
TWILIO_AUTH_TOKEN=your_twilio_auth_token
RESPONSE_ASSISTANT_ID=your_openai_response_assistant_id
VERDICT_ASSISTANT_ID=your_openai_verdict_assistant_id
```
Replace your_twilio_account_sid, your_twilio_auth_token, your_openai_response_assistant_id, and your_openai_verdict_assistant_id with your actual Twilio and OpenAI credentials.

#### Vosk Model Setup:
Download a Vosk model suitable for your language and place it in the specified directory (../model). Update the VOSK_MODEL_PATH in src/config.py if necessary.

#### Starting the Server:
Run the Flask application:
```sh
python app.py
```
This will start the application and use ngrok to expose it to the Internet, making it accessible to Twilio for incoming calls.

#### Twilio Webhook Configuration:
Configure your Twilio phone number's voice webhook to point to the ngrok URL displayed in the terminal followed by /call.

### Testing
Make a phone call to your Twilio number to test the application. You should be greeted by the voice assistant, which will process your speech and respond accordingly.
from flask import Flask, request
import requests
import google.generativeai as genai
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

VERIFY_TOKEN = os.environ.get("VERIFY_TOKEN")
PHONE_NUMBER_ID = os.environ.get("PHONE_NUMBER_ID")
ACCESS_TOKEN = os.environ.get("ACCESS_TOKEN")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

genai.configure(api_key=GEMINI_API_KEY)

SYSTEM_PROMPT = """You are a demo WhatsApp AI chatbot built to showcase how AI can be integrated with WhatsApp using the Meta API and Google Gemini.

Your personality:
- Friendly, helpful and professional
- Always mention you are a DEMO project when someone says hi or hello
- Keep replies short and clear (this is WhatsApp, not an essay!)
- Use simple language
- Add relevant emojis to make replies friendly 😊

Always remember:
- You are a demo project made to showcase AI + WhatsApp integration
- You were built using Python, Flask, Meta WhatsApp API and Google Gemini AI
- If asked who made you, say you were built as a demo project
- Keep responses under 200 words as this is WhatsApp"""

model = genai.GenerativeModel(
    model_name="gemini-1.5-flash",
    system_instruction=SYSTEM_PROMPT
)

@app.route('/webhook', methods=['GET'])
def verify():
    token = request.args.get('hub.verify_token')
    challenge = request.args.get('hub.challenge')
    if token == VERIFY_TOKEN:
        return challenge
    return 'Invalid token', 403

@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.get_json()
    try:
        message = data['entry'][0]['changes'][0]['value']['messages'][0]
        if message['type'] == 'text':
            user_number = message['from']
            user_text = message['text']['body']
            reply = ask_gemini(user_text)
            send_reply(user_number, reply)
    except (KeyError, IndexError):
        pass
    return 'OK', 200

def ask_gemini(user_text):
    try:
        # No memory - every message is fresh
        response = model.generate_content(user_text)
        return response.text
    except Exception as e:
        return f"⚠️ Demo Bot Error: {str(e)}"

def send_reply(to, message):
    url = f"https://graph.facebook.com/v18.0/{PHONE_NUMBER_ID}/messages"
    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }
    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "text",
        "text": {"body": message}
    }
    requests.post(url, headers=headers, json=payload)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 3000))
    app.run(host='0.0.0.0', port=port)

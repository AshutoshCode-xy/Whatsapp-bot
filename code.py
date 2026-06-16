from flask import Flask, request
import requests
from google import genai
from google.genai import types
import os
import time
import threading
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

VERIFY_TOKEN = os.environ.get("VERIFY_TOKEN")
PHONE_NUMBER_ID = os.environ.get("PHONE_NUMBER_ID")
ACCESS_TOKEN = os.environ.get("ACCESS_TOKEN")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

print(f"✅ PHONE_NUMBER_ID: {PHONE_NUMBER_ID}")
print(f"✅ ACCESS_TOKEN exists: {bool(ACCESS_TOKEN)}")
print(f"✅ GEMINI_API_KEY exists: {bool(GEMINI_API_KEY)}")
print(f"✅ VERIFY_TOKEN: {VERIFY_TOKEN}")

client = genai.Client(api_key=GEMINI_API_KEY)

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

# Home route
@app.route('/', methods=['GET'])
def home():
    return "✅ WhatsApp Bot is Running!", 200

# Status route
@app.route('/status', methods=['GET'])
def status():
    meta_status = check_meta_connection()
    gemini_status = check_gemini_connection()
    return {
        "bot": "✅ Running",
        "meta_whatsapp": meta_status,
        "gemini_ai": gemini_status,
        "environment": {
            "PHONE_NUMBER_ID": "✅ Set" if PHONE_NUMBER_ID else "❌ Missing",
            "ACCESS_TOKEN": "✅ Set" if ACCESS_TOKEN else "❌ Missing",
            "GEMINI_API_KEY": "✅ Set" if GEMINI_API_KEY else "❌ Missing",
            "VERIFY_TOKEN": "✅ Set" if VERIFY_TOKEN else "❌ Missing"
        }
    }

def check_meta_connection():
    try:
        url = f"https://graph.facebook.com/v25.0/{PHONE_NUMBER_ID}"
        headers = {"Authorization": f"Bearer {ACCESS_TOKEN}"}
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            data = response.json()
            return f"✅ Connected - Number: {data.get('display_phone_number', 'N/A')}"
        else:
            return f"❌ Failed - {response.status_code}: {response.json().get('error', {}).get('message', 'Unknown error')}"
    except Exception as e:
        return f"❌ Error: {str(e)}"

def check_gemini_connection():
    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash-lite",
            contents="Say 'Gemini Connected!' in 3 words only",
            config=types.GenerateContentConfig(max_output_tokens=10)
        )
        return f"✅ Connected - {response.text.strip()}"
    except Exception as e:
        return f"❌ Error: {str(e)}"

# Webhook verification
@app.route('/webhook', methods=['GET'])
def verify():
    token = request.args.get('hub.verify_token')
    challenge = request.args.get('hub.challenge')
    print(f"Webhook verify attempt - token: {token}")
    if token == VERIFY_TOKEN:
        print("✅ Webhook verified!")
        return challenge
    print("❌ Webhook verification failed!")
    return 'Invalid token', 403

# Receive messages
@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.get_json()
    print(f"📩 Incoming data: {data}")
    try:
        message = data['entry'][0]['changes'][0]['value']['messages'][0]
        if message['type'] == 'text':
            user_number = message['from']
            user_text = message['text']['body']
            print(f"📱 Message from {user_number}: {user_text}")
            reply = ask_gemini(user_text)
            print(f"🤖 Gemini reply: {reply}")
            send_reply(user_number, reply)
    except Exception as e:
        print(f"❌ Webhook error: {str(e)}")
        print(f"❌ Data was: {data}")
    return 'OK', 200

def ask_gemini(user_text):
    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash-lite",
            contents=user_text,
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_PROMPT,
                max_output_tokens=300
            )
        )
        return response.text
    except Exception as e:
        print(f"❌ Gemini error: {str(e)}")
        return f"⚠️ Demo Bot Error: {str(e)}"

def send_reply(to, message):
    url = f"https://graph.facebook.com/v25.0/{PHONE_NUMBER_ID}/messages"
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
    response = requests.post(url, headers=headers, json=payload)
    print(f"📤 WhatsApp API: {response.status_code} - {response.text}")



if __name__ == '__main__':
    port = int(os.environ.get('PORT', 3000))
    app.run(host='0.0.0.0', port=port)

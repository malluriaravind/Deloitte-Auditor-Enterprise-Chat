from flask import Flask, request, jsonify, render_template
import requests
import re
import os
from flask_sqlalchemy import SQLAlchemy
from requests.adapters import Retry, HTTPAdapter
from datetime import datetime

app = Flask(__name__)

# Configuration for the database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///chat_history.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Define a model for storing chat history
class TaxChat(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    prompt = db.Column(db.Text, nullable=False)
    response = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

# Create the database tables
with app.app_context():
    db.create_all()

# Route to serve the home page (index.html)
@app.route('/')
def home():
    return render_template('index.html')

# Function to validate tax-related questions
def is_tax_related(question):
    tax_keywords = [
        "deduction", "deductions", "credit", "credits", "tax", "return", "filing",
        "IRS", "exemption", "taxable", "income", "expenses", "audit", "rebate",
        "refund", "w-2", "w-4", "form", "schedule", "tax laws", "capital gains",
        "tax rate", "withholding", "payroll", "adjusted gross income",
        "standard deduction", "itemized deduction", "earned income", "dependent", "1099",
        "1040", "self-employment tax", "estate tax", "gift tax", "alternative minimum tax",
        "tax bracket", "tax liability", "taxable income", "tax"
    ]
    pattern = re.compile(r'\b(?:' + '|'.join(tax_keywords) + r')\b', re.IGNORECASE)
    return bool(pattern.search(question))

# Function to get OpenAI response and handle incomplete responses
def get_openai_response(question):
    api_key = 'Enter OpenAI_API_Key_Here'
    if not api_key:
        return "Error: OpenAI API key not found."

    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json'
    }

    prompt = f"""
You are an expert U.S. tax advisor. Please answer the following question:

Question: "{question}"

Provide a detailed response in paragraphs. If the response is longer than 50 words, split it into separate paragraphs after every 50 words.

Include the following details:
- A clear and concise explanation of the question.
- Relevant tax laws or IRS guidelines.
- Possible deductions or credits.
- Relevant forms or deadlines.

If the question is unclear or not tax-related, ask for clarification politely.
"""

    data = {
        'model': 'gpt-4',
        'messages': [{'role': 'user', 'content': prompt.strip()}],
        'max_tokens': 2000,
        'temperature': 0.5,
    }

    session = requests.Session()
    retries = Retry(total=5, backoff_factor=1, status_forcelist=[502, 503, 504])
    session.mount('https://', HTTPAdapter(max_retries=retries))

    try:
        response = session.post('https://api.openai.com/v1/chat/completions',
                                headers=headers, json=data, timeout=60)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        return f"Error communicating with OpenAI API: {e}"

    response_data = response.json()
    return response_data['choices'][0]['message']['content'].strip()

# Flask route to handle tax-related question input
@app.route('/api/tax-prompt', methods=['POST'])
def tax_prompt():
    data = request.get_json()
    question = data.get('question', '').strip()

    if not question:
        return jsonify({'error': 'No question provided.'}), 400

    if not is_tax_related(question):
        return jsonify({'error': 'Please ask a valid tax-related question.'}), 400

    response = get_openai_response(question)

    # Check for errors in the OpenAI response
    if response.startswith("Error"):
        return jsonify({'error': response}), 500

    # Store the question and response in the database
    chat = TaxChat(prompt=question, response=response)
    db.session.add(chat)
    db.session.commit()

    return jsonify({'answer': response})

# Route to get previous chats (with question followed by response)
@app.route('/api/get-chats', methods=['GET'])
def get_chats():
    chats = TaxChat.query.order_by(TaxChat.timestamp.desc()).all()
    chat_history = [{'prompt': chat.prompt, 'response': chat.response, 'timestamp': chat.timestamp} for chat in chats]
    return jsonify(chat_history)

# Route to get a specified number of previous responses for history context
@app.route('/api/get-history', methods=['GET'])
def get_history():
    count = request.args.get('count', default=5, type=int)
    chats = TaxChat.query.order_by(TaxChat.timestamp.desc()).limit(count).all()
    chat_history = [{'prompt': chat.prompt, 'response': chat.response, 'timestamp': chat.timestamp} for chat in reversed(chats)]
    return jsonify(chat_history)

if __name__ == '__main__':
    app.run(debug=True)

from flask import Flask, request, jsonify, render_template
import requests
import re
import os
from flask_sqlalchemy import SQLAlchemy
from requests.adapters import Retry, HTTPAdapter

app = Flask(__name__)

# Configuration for the database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///chat_history.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Define a model for storing chat history
class Chat(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    question = db.Column(db.Text, nullable=False)
    answer = db.Column(db.Text, nullable=False)

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

# Function to check if the user is asking for more details or in-depth explanation using regex
def is_follow_up(question):
    follow_up_keywords = [
        "more details", "explain further", "in-depth", "elaborate", "can you clarify", 
        "expand", "give more information", "go deeper", "explain in more detail", "I did not understand"
    ]
    pattern = re.compile(r'\b(?:' + '|'.join(follow_up_keywords) + r')\b', re.IGNORECASE)
    return bool(pattern.search(question))

# Function to split response into paragraphs of 50 words each
def split_into_paragraphs(response, words_per_paragraph=50):
    words = response.split()
    paragraphs = []
    paragraph = []
    
    for word in words:
        paragraph.append(word)
        if len(paragraph) >= words_per_paragraph:
            paragraphs.append(' '.join(paragraph))
            paragraph = []
    
    if paragraph:
        paragraphs.append(' '.join(paragraph))
    
    return '\n\n'.join(paragraphs)  # Each paragraph separated by two new lines

# Function to get OpenAI response and handle incomplete responses
def get_openai_response(question, detailed=False, previous_answer=None):
    api_key = 'Enter your openai_api_key here'
    if not api_key:
        return "Error: OpenAI API key not found. Please set the OPENAI_API_KEY environment variable."

    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json'
    }

    # Construct prompt based on whether it's a detailed follow-up
    if detailed and previous_answer:
        prompt = f"""
You provided the following response earlier:

Response: "{previous_answer}"

The user has now asked for more details or clarification. Please provide a more detailed, in-depth explanation:

Question: "{question}"

Include additional tax laws, examples, and relevant forms where applicable.
"""
    else:
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
        'max_tokens': 2000,  # Increase max_tokens to allow longer responses
        'temperature': 0.5,
    }

    session = requests.Session()
    retries = Retry(total=5, backoff_factor=1, status_forcelist=[502, 503, 504])
    session.mount('https://', HTTPAdapter(max_retries=retries))

    try:
        # Increase the timeout to 60 seconds
        response = session.post('https://api.openai.com/v1/chat/completions',
                                headers=headers, json=data, timeout=60)
        response.raise_for_status()
    except requests.exceptions.Timeout:
        return "Error: The request timed out while communicating with the OpenAI API. Please try again later."
    except requests.exceptions.RequestException as e:
        return f"Error communicating with OpenAI API: {e}"

    response_data = response.json()
    original_response = response_data['choices'][0]['message']['content'].strip()

    # If the response is incomplete (cut off in the middle), add prompt to continue
    if response_data['choices'][0]['finish_reason'] == 'length':
        # Prompt the API to continue from where it left off
        next_prompt = f"Continue from: '{original_response[-30:]}'"
        continuation = get_openai_continuation(next_prompt)
        original_response += continuation

    # Split the response into paragraphs after every 50 words
    formatted_response = split_into_paragraphs(original_response)
    
    return formatted_response

# Function to get continuation if the response is cut off
def get_openai_continuation(prompt):
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        return ""

    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json'
    }

    data = {
        'model': 'gpt-4',
        'messages': [{'role': 'user', 'content': prompt.strip()}],
        'max_tokens': 1000,  # Fetch additional 1000 tokens for continuation
        'temperature': 0.5,
    }

    session = requests.Session()
    retries = Retry(total=5, backoff_factor=1, status_forcelist=[502, 503, 504])
    session.mount('https://', HTTPAdapter(max_retries=retries))

    try:
        response = session.post('https://api.openai.com/v1/chat/completions',
                                headers=headers, json=data, timeout=60)
        response.raise_for_status()
    except requests.exceptions.Timeout:
        return ""
    except requests.exceptions.RequestException as e:
        return ""

    response_data = response.json()
    continuation = response_data['choices'][0]['message']['content'].strip()
    
    return continuation

# Flask route to handle tax-related question input
@app.route('/api/tax-prompt', methods=['POST'])
def tax_prompt():
    data = request.get_json()
    question = data.get('question', '').strip()

    # Check if this is a follow-up question or a request for more details using regex
    follow_up_chat = Chat.query.order_by(Chat.id.desc()).first()  # Fetch the latest question
    if follow_up_chat and is_follow_up(question):
        # User asked a follow-up or more detailed question
        detailed_response = get_openai_response(follow_up_chat.question, detailed=True, previous_answer=follow_up_chat.answer)
        chat = Chat(question=question, answer=detailed_response)
        db.session.add(chat)
        db.session.commit()
        return jsonify({'answer': detailed_response})

    # Validate the question for a new question
    if not question:
        return jsonify({'error': 'No question provided.'}), 400

    if not is_tax_related(question):
        # If it's not a valid tax-related question, ask the user to ask a valid tax question.
        return jsonify({'error': 'Please ask a valid tax-related question.'}), 400

    # Check if the same question was asked before
    previous_chat = Chat.query.filter_by(question=question).first()
    if previous_chat:
        return jsonify({'answer': previous_chat.answer})

    # If it's a new question, get the GPT response
    response = get_openai_response(question)

    # Check for errors in the OpenAI response
    if response.startswith("Error"):
        return jsonify({'error': response}), 500

    # Store the question and response in the database
    chat = Chat(question=question, answer=response)
    db.session.add(chat)
    db.session.commit()

    # Return the response to the client
    return jsonify({'answer': response})

# Route to get previous chats (with question followed by response)
@app.route('/api/get-chats', methods=['GET'])
def get_chats():
    chats = Chat.query.order_by(Chat.id.desc()).all()
    chat_history = [{'question': chat.question, 'answer': chat.answer} for chat in chats]
    return jsonify(chat_history)

if __name__ == '__main__':
    app.run(debug=True)

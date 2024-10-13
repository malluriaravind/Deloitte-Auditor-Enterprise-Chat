# Deloitte-Auditor-Enterprise-Chat-UI
Deloitte Auditor Enterprise Chat UI could refer to a chat-based interface or application designed to facilitate communication, collaboration, and reporting among auditors working on financial audits, risk assessments, or compliance checks for enterprises.

# Chatbot Application

A simple chatbot application built with Python Flask, enabling users to interact with a tax-related AI chatbot. The application supports user queries through a web interface and responds with relevant information. 

![Chatbot Interface](output/chatbot_interface.png)  

## Features

- **AJAX Support:** Asynchronous communication between the frontend and backend for a seamless user experience.
- **RESTful API:** A structured API to handle requests and responses for chat interactions.
- **Chat History:** Users can view the history of their interactions with the chatbot.
- **User-Friendly Interface:** A simple web interface to input questions and receive answers.
- **Customizable AI Responses:** The chatbot is powered by an AI model capable of understanding and responding to tax-related queries.

## Technologies Used

- **Backend:**
  - Python
  - Flask
  - Flask-CORS (for Cross-Origin Resource Sharing)
  - Flask-SQLAlchemy (for database management)
  
- **Frontend:**
  - HTML
  - CSS
  - JavaScript
  - AJAX (for asynchronous data fetching)

## Installation

Follow the steps below to set up and run the application locally.

1. **Clone the repository:**

   ```bash
   git clone https://github.com/malluriaravind/Deloitte-Auditor-Enterprise-Chat-UI.git
   cd Deloitte-Auditor-Enterprise-Chat-UI
   ```


2. **Install the required packages:**

   ```bash
   pip install flask
   ```

4. **Set up the database (if applicable):**
   - Initialize your database. If using SQLite, the database file will be created automatically when the application runs.

## Usage

1. **Run the Flask application:**

   ```bash
   python app.py
   ```

2. **Access the application:**
   Open your web browser and navigate to `http://127.0.0.1:5000`.

3. **Interact with the chatbot:**
   - Type your question in the input box and click the send button to receive responses from the chatbot.

## API Endpoints

### POST /api/tax-prompt

- **Description:** Sends a user question to the chatbot and retrieves an answer.
- **Request Body:**
  
  ```json
  {
    "question": "Your question here"
  }
  ```
- **Response:**
  
  ```json
  {
    "answer": "Chatbot response here"
  }
  ```
- - Chatbot Interface Providing Tax-Related Responses
- ![Tax Related Response 1](output/tax-related-response-1.png)  
- ![Tax Related Response 2](output/tax-related-response-2.png)  
- ![Tax Related Response 3](output/tax-related-response-3.png)  
- ![Non Tax Related Response](output/non-tax-related-response.png)  

### GET /api/get-chats

- **Description:** Retrieves the chat history for the user.
- **Response:**

  ```json
  [
    {
      "question": "Question 1",
      "answer": "Answer 1"
    },
    {
      "question": "Question 2",
      "answer": "Answer 2"
    }
  ]
  ```
- Local Session Store Storing Prompts
- ![Chat Storing Local Session Storage](output/local-session-store.png)  


## Frontend Implementation

The frontend of this application is built using standard web technologies. Here’s how it communicates with the backend:

- **AJAX calls** are made to the `/api/tax-prompt` endpoint to send user questions and receive answers asynchronously.
- The chat interface updates dynamically without requiring a page reload, providing a smooth user experience.

### Example JavaScript Code

Here's a sample snippet of how AJAX is implemented in the frontend:

```javascript
$(document).ready(function() {
    $("#sendButton").click(function() {
        const userQuestion = $("#userInput").val();
        $.ajax({
            url: "/api/tax-prompt",
            method: "POST",
            contentType: "application/json",
            data: JSON.stringify({ question: userQuestion }),
            success: function(response) {
                $("#chatArea").append(`<div>User: ${userQuestion}</div>`);
                $("#chatArea").append(`<div>Bot: ${response.answer}</div>`);
            }
        });
    });
});
```

## Testing

You can test the application using tools like Postman or directly through the frontend interface. Ensure that the server is running to receive requests.

## Contributing

Contributions are welcome! Please feel free to submit a pull request or open an issue. You can enhance the chatbot's capabilities, improve the UI, or optimize the backend logic.


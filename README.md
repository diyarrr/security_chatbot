# Rank-Aware Security Chatbot

An AI-powered Security Advisor Chatbot that utilizes a Large Language Model (LLM) to interactively educate and advise users on cybersecurity best practices.

## Features

- Interactive chat interface for security questions
- Rank-based progression system with XP
- Retrieval-Augmented Generation (RAG) for accurate responses
- Topic-based access control by rank
- Feedback mechanism for continuous improvement
- PDF document processing for knowledge base creation

## Setup Instructions

1. Clone this repository

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create a .env file with your OpenAI API key and other configurations:
```
OPENAI_API_KEY=your_openai_api_key_here
SECRET_KEY=your_secret_key_here
DEBUG=True
```

5. Add your PDF security documents to `data/pdf_documents/` directory

6. Process PDF documents to create knowledge base:
```bash
python -c "from utils import create_knowledge_base_from_pdfs; create_knowledge_base_from_pdfs()"
```

7. Start the Flask server:
```bash
python backend/app.py
```

8. Open frontend/index.html in a web browser

## User Ranks

- **Security Novice** (0 XP) - Basic security concepts
- **Security Apprentice** (100 XP) - Intermediate topics  
- **Security Adept** (250 XP) - Advanced topics
- **Security Expert** (500 XP) - Professional security concepts
- **Security Master** (1000 XP) - Expert-level security knowledge

## Adding PDF Security Documents

1. Place your PDF documents in the `data/pdf_documents/` directory
2. Run the PDF processing function to convert them to text format
3. The system will automatically use them to enhance chatbot responses

## Supported PDF Sources

The system can process PDF documents from reliable sources such as:
- NIST Cybersecurity Framework
- SANS Security Guidelines
- ISO 27001 Standards
- Company security policies
- Academic security research papers
- Government cybersecurity guidelines

## License

MIT

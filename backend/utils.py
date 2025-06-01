import os
import json
import logging
import PyPDF2
import fitz  # PyMuPDF - alternative PDF library
from pathlib import Path
from .config import TOPICS

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("app.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

def identify_topics(query):
    """
    Identify security topics in the query based on keywords
    Returns a list of topics found in the query
    """
    query_lower = query.lower()
    detected_topics = []

    for topic, details in TOPICS.items():
        keywords = details["keywords"]
        if any(keyword in query_lower for keyword in keywords):
            detected_topics.append(topic)

    # If no specific topic is detected, default to basic security
    if not detected_topics:
        detected_topics.append("basic_security")

    return detected_topics


def check_rank_access(topics, user_rank):
    """
    Check if the user's rank allows access to all detected topics
    Returns True if access is granted, False otherwise
    """
    for topic in topics:
        required_rank = TOPICS.get(topic, {"rank": 1})["rank"]
        if user_rank < required_rank:
            return False

    return True


def extract_text_from_pdf_pypdf2(pdf_path):
    """
    Extract text from PDF using PyPDF2 library
    """
    try:
        text = ""
        with open(pdf_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"
        return text
    except Exception as e:
        logger.error(f"Error extracting text from {pdf_path} using PyPDF2: {str(e)}")
        return None


def extract_text_from_pdf_pymupdf(pdf_path):
    """
    Extract text from PDF using PyMuPDF (fitz) library
    Better for complex PDFs with images and formatting
    """
    try:
        text = ""
        doc = fitz.open(pdf_path)
        for page in doc:
            text += page.get_text() + "\n"
        doc.close()
        return text
    except Exception as e:
        logger.error(f"Error extracting text from {pdf_path} using PyMuPDF: {str(e)}")
        return None


def extract_text_from_pdf(pdf_path):
    """
    Extract text from PDF using multiple methods as fallback
    """
    # Try PyMuPDF first (generally better results)
    text = extract_text_from_pdf_pymupdf(pdf_path)
    
    # If PyMuPDF fails, try PyPDF2
    if not text or len(text.strip()) < 100:
        logger.info(f"PyMuPDF extraction poor for {pdf_path}, trying PyPDF2...")
        text = extract_text_from_pdf_pypdf2(pdf_path)
    
    if not text:
        logger.error(f"Failed to extract text from {pdf_path}")
        return None
    
    return text.strip()


def process_pdf_documents(pdf_directory="./data/pdf_documents"):
    """
    Process all PDF documents in the specified directory and convert them to text files
    """
    knowledge_base_dir = "./data/knowledge_base"
    os.makedirs(knowledge_base_dir, exist_ok=True)
    
    pdf_dir = Path(pdf_directory)
    if not pdf_dir.exists():
        logger.error(f"PDF directory {pdf_directory} does not exist")
        return False
    
    pdf_files = list(pdf_dir.glob("*.pdf"))
    if not pdf_files:
        logger.warning(f"No PDF files found in {pdf_directory}")
        return False
    
    processed_count = 0
    
    for pdf_file in pdf_files:
        logger.info(f"Processing PDF: {pdf_file.name}")
        
        # Extract text from PDF
        extracted_text = extract_text_from_pdf(str(pdf_file))
        
        if extracted_text:
            # Create output filename (replace .pdf with .txt)
            output_filename = pdf_file.stem + ".txt"
            output_path = os.path.join(knowledge_base_dir, output_filename)
            
            # Write extracted text to file
            try:
                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write(f"# Security Document: {pdf_file.name}\n\n")
                    f.write(extracted_text)
                
                logger.info(f"Successfully converted {pdf_file.name} to {output_filename}")
                processed_count += 1
                
            except Exception as e:
                logger.error(f"Error writing text file for {pdf_file.name}: {str(e)}")
        else:
            logger.error(f"Failed to extract text from {pdf_file.name}")
    
    logger.info(f"Processed {processed_count} PDF documents out of {len(pdf_files)} found")
    return processed_count > 0


def clean_extracted_text(text):
    """
    Clean and format extracted text from PDFs
    """
    # Remove excessive whitespace
    lines = [line.strip() for line in text.split('\n')]
    lines = [line for line in lines if line]  # Remove empty lines
    
    # Join lines and clean up spacing
    cleaned_text = '\n'.join(lines)
    
    # Remove multiple consecutive newlines
    import re
    cleaned_text = re.sub(r'\n{3,}', '\n\n', cleaned_text)
    
    return cleaned_text


def create_knowledge_base_from_pdfs(pdf_directory="./data/pdf_documents"):
    """
    Main function to create knowledge base from PDF documents
    """
    logger.info("Starting PDF to knowledge base conversion...")
    
    # Create PDF directory if it doesn't exist
    os.makedirs(pdf_directory, exist_ok=True)
    
    if not os.listdir(pdf_directory):
        logger.warning(f"PDF directory {pdf_directory} is empty. Please add your PDF documents there.")
        return False
    
    # Process PDF documents
    success = process_pdf_documents(pdf_directory)
    
    if success:
        logger.info("Knowledge base creation from PDFs completed successfully!")
    else:
        logger.error("Failed to create knowledge base from PDFs")
    
    return success


def create_env_file():
    """
    Create a sample .env file with required configuration
    """
    env_content = """# OpenAI API Key
OPENAI_API_KEY=your_openai_api_key_here

# Flask Configuration
SECRET_KEY=your_secret_key_here
DEBUG=True

# Database Configuration
DB_DIRECTORY=./data/chroma_db

# Knowledge Base Configuration
KNOWLEDGE_BASE_DIR=./data/knowledge_base

# PDF Documents Directory
PDF_DOCUMENTS_DIR=./data/pdf_documents

# LLM Configuration
DEFAULT_MODEL=gpt-4o
"""

    with open(".env", 'w', encoding='utf-8') as f:
        f.write(env_content)

    logger.info("Created sample .env file. Please update with your actual API keys.")


def create_readme():
    """
    Create a README file with setup and usage instructions
    """
    readme_content = """# Rank-Aware Security Chatbot

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
source venv/bin/activate  # On Windows: venv\\Scripts\\activate
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
"""

    with open("README.md", 'w', encoding='utf-8') as f:
        f.write(readme_content)

    logger.info("Created README.md file with setup and usage instructions")


def create_requirements_file():
    """
    Create a requirements.txt file with necessary dependencies including PDF processing
    """
    requirements = """flask==2.3.3
flask-cors==4.0.0
openai==1.3.8
langchain==0.0.335
chromadb==0.4.22
sentence-transformers==2.2.2
python-dotenv==1.0.0
PyPDF2==3.0.1
PyMuPDF==1.23.8
pathlib2==2.3.7.post1"""

    with open("requirements.txt", 'w', encoding='utf-8') as f:
        f.write(requirements)

    logger.info("Created requirements.txt file with PDF processing dependencies")
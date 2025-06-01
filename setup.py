import os
import logging
import sys
from pathlib import Path
from dotenv import load_dotenv

# Configure logger for this setup script
# This will create/overwrite setup.log and print to console
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("setup.log", mode='w'),
        logging.StreamHandler(sys.stdout)
    ]
)
setup_logger = logging.getLogger("project_setup")

# Attempt to import utility functions from the 'backend' directory
try:
    from backend.utils import (
        create_env_file,
        create_requirements_file,
        create_readme,
        process_pdf_documents,
        create_knowledge_base_from_pdfs
    )
except ImportError as e:
    setup_logger.error(f"Failed to import from backend/utils.py: {e}")
    setup_logger.error("Ensure backend/utils.py exists and the backend directory is structured correctly.")
    sys.exit(1)

# Default paths (used if config.py import fails or .env doesn't specify them)
DEFAULT_KNOWLEDGE_BASE_DIR = "./data/knowledge_base"
DEFAULT_DB_DIRECTORY = "./data/chroma_db"
DEFAULT_PDF_DIRECTORY = "./data/pdf_documents"

def check_pdf_files(pdf_directory):
    """Check for PDF files in the documents directory"""
    pdf_dir = Path(pdf_directory)
    if not pdf_dir.exists():
        return []
    
    pdf_files = list(pdf_dir.glob("*.pdf"))
    
    if pdf_files:
        setup_logger.info(f"Found {len(pdf_files)} PDF file(s) in {pdf_directory}:")
        for pdf_file in pdf_files:
            try:
                size_mb = pdf_file.stat().st_size / (1024 * 1024)
                setup_logger.info(f"  - {pdf_file.name} ({size_mb:.2f} MB)")
            except Exception as e:
                setup_logger.warning(f"  - {pdf_file.name} (could not read size: {e})")
    
    return pdf_files

def setup_pdf_processing(knowledge_base_dir, pdf_directory):
    """Handle PDF document processing setup"""
    setup_logger.info("=== PDF Document Processing Setup ===")
    
    # Create PDF directory if it doesn't exist
    os.makedirs(pdf_directory, exist_ok=True)
    setup_logger.info(f"PDF documents directory ensured: {os.path.abspath(pdf_directory)}")
    
    # Check for existing PDF files
    pdf_files = check_pdf_files(pdf_directory)
    
    if pdf_files:
        setup_logger.info(f"Processing {len(pdf_files)} PDF document(s)...")
        
        # Check if PDF processing libraries are available
        try:
            import PyPDF2
            import fitz  # PyMuPDF
            setup_logger.info("PDF processing libraries (PyPDF2, PyMuPDF) are available.")
        except ImportError as e:
            setup_logger.error(f"PDF processing libraries not found: {e}")
            setup_logger.error("Please install required libraries: pip install PyPDF2 PyMuPDF")
            setup_logger.info("SKIPPING PDF processing. You can:")
            setup_logger.info("1. Install the libraries: pip install PyPDF2 PyMuPDF")
            setup_logger.info("2. Re-run this setup script")
            return False
        
        try:
            # Process PDF documents
            success = process_pdf_documents(pdf_directory)
            
            if success:
                setup_logger.info("✅ PDF processing completed successfully!")
                setup_logger.info(f"Processed documents saved to: {os.path.abspath(knowledge_base_dir)}")
                return True
            else:
                setup_logger.warning("PDF processing completed with some failures. Check logs for details.")
                return False
                
        except Exception as e:
            setup_logger.error(f"Error during PDF processing: {e}")
            return False
    
    else:
        setup_logger.info("No PDF files found. You can:")
        setup_logger.info(f"1. Add PDF documents to: {os.path.abspath(pdf_directory)}")
        setup_logger.info("2. Re-run this setup script to process them")
        setup_logger.info("3. Or continue with sample documents")
        setup_logger.info("\nRecommended PDF sources:")
        setup_logger.info("- NIST Cybersecurity Framework")
        setup_logger.info("- SANS Security Guidelines")
        setup_logger.info("- ISO 27001 Standards")
        setup_logger.info("- OWASP Security Guidelines")
        setup_logger.info("- Company security policies")
        return False

def main():
    setup_logger.info("========= Starting Project Setup =========")

    # --- Step 1: Create .env file and prompt for API Key ---
    setup_logger.info("Step 1: Creating .env file...")
    create_env_file() # From backend/utils.py
    setup_logger.info("ACTION REQUIRED: The '.env' file has been created (or may have already existed) in the project root.")
    setup_logger.info("Please edit it NOW to set your OPENAI_API_KEY.")
    setup_logger.info("Other configurations like SECRET_KEY can also be reviewed.")
    setup_logger.info("The script will pause. Press Enter to continue after editing .env, or Ctrl+C to exit.")
    try:
        input("Press Enter to continue...")
    except KeyboardInterrupt:
        setup_logger.info("Setup interrupted by user. Please complete .env and re-run this script (python setup.py).")
        sys.exit(0)

    # --- Step 2: Load .env variables ---
    setup_logger.info("Step 2: Loading environment variables from .env file (in project root)...")
    if load_dotenv(override=True): 
        setup_logger.info(".env file loaded successfully by setup.py.")
    else:
        setup_logger.warning(".env file not found in root or could not be loaded by setup.py. Defaults will be used for paths. OpenAI features will likely fail.")
    
    current_openai_api_key = os.getenv("OPENAI_API_KEY")

    # --- Step 3: Import configuration and determine paths ---
    setup_logger.info("Step 3: Determining configuration paths...")
    KNOWLEDGE_BASE_DIR = DEFAULT_KNOWLEDGE_BASE_DIR
    DB_DIRECTORY = DEFAULT_DB_DIRECTORY
    PDF_DIRECTORY = os.getenv("PDF_DOCUMENTS_DIR", DEFAULT_PDF_DIRECTORY)
    
    try:
        from backend.config import KNOWLEDGE_BASE_DIR as CFG_KB_DIR, DB_DIRECTORY as CFG_DB_DIR
        
        if CFG_KB_DIR: KNOWLEDGE_BASE_DIR = CFG_KB_DIR
        if CFG_DB_DIR: DB_DIRECTORY = CFG_DB_DIR
        
        setup_logger.info(f"Using KNOWLEDGE_BASE_DIR (resolved from root): {os.path.abspath(KNOWLEDGE_BASE_DIR)}")
        setup_logger.info(f"Using DB_DIRECTORY (resolved from root): {os.path.abspath(DB_DIRECTORY)}")
        setup_logger.info(f"Using PDF_DIRECTORY: {os.path.abspath(PDF_DIRECTORY)}")
    except ImportError as e:
        setup_logger.warning(f"Could not import from backend.config: {e}. Using default paths.")
    except Exception as e:
        setup_logger.warning(f"An error occurred importing from backend.config: {e}. Using default paths.")

    # --- Step 4: Create other essential project files ---
    setup_logger.info("Step 4: Creating requirements.txt and README.md in project root...")
    create_requirements_file()
    setup_logger.info("requirements.txt created/updated.")
    setup_logger.info("ACTION REQUIRED: Install dependencies using: pip install -r requirements.txt")
    
    create_readme()
    setup_logger.info("README.md created/updated.")

    # --- Step 5: Create data directories ---
    setup_logger.info("Step 5: Ensuring data directories exist (relative to project root)...")
    try:
        os.makedirs("./data", exist_ok=True)
        os.makedirs(KNOWLEDGE_BASE_DIR, exist_ok=True)
        os.makedirs(DB_DIRECTORY, exist_ok=True)
        os.makedirs(PDF_DIRECTORY, exist_ok=True)
        setup_logger.info(f"Data directories ensured: {os.path.abspath('./data')}, {os.path.abspath(KNOWLEDGE_BASE_DIR)}, {os.path.abspath(DB_DIRECTORY)}, {os.path.abspath(PDF_DIRECTORY)}")
    except Exception as e:
        setup_logger.error(f"Error creating data directories: {e}. Please check path validity and permissions.")
        sys.exit(1)

    # --- Step 6: PDF Document Processing (NEW) ---
    setup_logger.info("Step 6: PDF Document Processing...")
    pdf_processed = setup_pdf_processing(KNOWLEDGE_BASE_DIR, PDF_DIRECTORY)
    
    # --- Step 7: Create sample security documents (if no PDFs processed) ---
    if not pdf_processed:
        setup_logger.info("Step 7: Creating sample security documents...")
        setup_logger.info("Since no PDFs were processed, creating sample documents as fallback.")
        create_sample_security_documents()
        setup_logger.info(f"Sample documents created in '{os.path.abspath(KNOWLEDGE_BASE_DIR)}'.")
    else:
        setup_logger.info("Step 7: Skipping sample document creation (PDFs were processed).")

    # --- Step 8: Initialize Knowledge Base (ChromaDB) ---
    setup_logger.info("Step 8: Attempting to initialize and populate Knowledge Base (ChromaDB)...")
    if current_openai_api_key and current_openai_api_key != "your_openai_api_key_here":
        setup_logger.info("OPENAI_API_KEY appears to be set. Proceeding with ChromaDB setup.")
        try:
            from backend.retriever import DocumentRetriever
            
            retriever_instance = DocumentRetriever(db_directory=DB_DIRECTORY)
            
            if retriever_instance.collection.count() == 0:
                setup_logger.info(f"Knowledge base (ChromaDB collection '{retriever_instance.collection.name}' in '{os.path.abspath(DB_DIRECTORY)}') is empty.")
                setup_logger.info(f"Populating with documents from: {os.path.abspath(KNOWLEDGE_BASE_DIR)}...")
                
                if retriever_instance.add_security_knowledge_base(knowledge_dir=KNOWLEDGE_BASE_DIR):
                    setup_logger.info("Knowledge base populated successfully.")
                else:
                    setup_logger.warning(f"Knowledge base population from '{os.path.abspath(KNOWLEDGE_BASE_DIR)}' did not add documents.")
                    setup_logger.warning("Ensure the directory exists, is accessible, and contains .txt or .md files.")
            else:
                setup_logger.info(f"Knowledge base (ChromaDB collection '{retriever_instance.collection.name}') already contains {retriever_instance.collection.count()} documents.")
                setup_logger.info("Skipping population to avoid duplicates.")

        except ValueError as e: 
            setup_logger.error(f"Error during DocumentRetriever initialization or use: {e}")
            setup_logger.error("ChromaDB population SKIPPED. Ensure OPENAI_API_KEY in .env is correct and not a placeholder.")
        except ImportError:
            setup_logger.error("Failed to import DocumentRetriever from backend.retriever. Ensure 'backend/retriever.py' exists and all dependencies are installed.")
        except Exception as e:
            setup_logger.error(f"An unexpected error occurred during knowledge base initialization: {e}", exc_info=True)
            setup_logger.error("ChromaDB population SKIPPED.")
    else:
        setup_logger.warning("OPENAI_API_KEY not found, is a placeholder, or .env was not configured.")
        setup_logger.warning("Knowledge base (ChromaDB) will NOT be populated at this time.")
        setup_logger.warning("This is a CRITICAL step for the chatbot's RAG functionality.")

    setup_logger.info("========= Project Setup Finished =========")
    setup_logger.info("Summary of Required Next Steps (if not already completed):")
    setup_logger.info("1. VERIFY '.env' file in project root: Ensure OPENAI_API_KEY is correctly set.")
    setup_logger.info("2. INSTALL dependencies: `pip install -r requirements.txt` (run from project root)")
    
    if pdf_processed:
        setup_logger.info("3. ✅ PDF documents have been processed and are ready for use.")
    else:
        setup_logger.info(f"3. OPTIONAL: Add PDF documents to '{os.path.abspath(PDF_DIRECTORY)}' and re-run setup for better knowledge base.")
    
    setup_logger.info(f"4. CHECK document paths: Ensure documents are in '{os.path.abspath(KNOWLEDGE_BASE_DIR)}'.")
    setup_logger.info("5. RUN the Flask application (from project root): `python backend/app.py`")
    setup_logger.info("----------------------------------------------------")

if __name__ == "__main__":
    main()
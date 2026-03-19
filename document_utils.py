import boto3
import fitz  # This is PyMuPDF
import os
from dotenv import load_dotenv

load_dotenv()

def upload_to_s3(file_path, bucket_name, object_name=None):
    """Uploads a file to an AWS S3 bucket"""
    if object_name is None:
        object_name = os.path.basename(file_path)

    # Initialize the S3 client using our IAM keys from .env
    s3_client = boto3.client('s3', region_name=os.getenv("AWS_DEFAULT_REGION"))
    
    try:
        print(f"Uploading '{file_path}' to S3 bucket '{bucket_name}'...")
        s3_client.upload_file(file_path, bucket_name, object_name)
        print(f"Successfully uploaded to s3://{bucket_name}/{object_name}")
        return True
    except Exception as e:
        print(f"Error uploading to S3: {e}")
        return False

def extract_text_from_pdf(file_path):
    """Extracts text from a PDF file using PyMuPDF (Open-source Textract alternative)"""
    print(f"Extracting text from '{file_path}'...")
    try:
        # Open the PDF file
        doc = fitz.open(file_path)
        text = ""
        
        # Iterate through all pages and extract text
        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            text += page.get_text()
            
        print(f"Successfully extracted {len(text)} characters of text.")
        return text
    except Exception as e:
        print(f" Error extracting text: {e}")
        return None

if __name__ == "__main__":
    # --- TEST THE FUNCTIONS ---
    
    # 1. PASTE THE UNIQUE S3 BUCKET NAME HERE
    BUCKET_NAME = "enterprise-genai-agent-sharad-2026" 
    
    # 2. The name of the dummy PDF we will test with
    SAMPLE_PDF = "sample_policy.pdf"
    
    if os.path.exists(SAMPLE_PDF):
        # Test 1: Extract Text
        extracted_text = extract_text_from_pdf(SAMPLE_PDF)
        print("\n--- Preview of extracted text ---")
        print(extracted_text[:250] + "...\n")
        
        # Test 2: Upload to S3
        upload_to_s3(SAMPLE_PDF, BUCKET_NAME)
    else:
        print(f"Please place a PDF named '{SAMPLE_PDF}' in the project folder to test.")
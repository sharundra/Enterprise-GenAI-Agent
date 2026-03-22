import os
import shutil
import re
from fastapi import FastAPI, UploadFile, File, HTTPException, Query
from pydantic import BaseModel
from dotenv import load_dotenv

# Import our custom logic from the previous steps
from document_utils import upload_to_s3
from rag_pipeline import ingest_pdf_to_chroma
from agent import agent_app
from langchain_core.messages import HumanMessage
import sqlite3

load_dotenv()

# Initialize the FastAPI application
app = FastAPI(
    title="Enterprise GenAI Agent API",
    description="API for Document RAG and Structured SQL querying",
    version="1.0.0"
)

# Define the Pydantic model for our query endpoint (Data Validation!)
class QueryRequest(BaseModel):
    query: str

# ==========================================
# ENDPOINT 1: Upload Document
# ==========================================
@app.post("/upload", include_in_schema=False)
async def upload_document(file: UploadFile = File(...)):
    """
    Receives a PDF, saves it temporarily, uploads to S3, and ingests into ChromaDB.
    """
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")
    
    temp_file_path = f"temp_{file.filename}"
    
    try:
        # 1. Save the uploaded file locally so we can process it
        with open(temp_file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        # 2. Upload to Amazon S3 (Replace with your actual bucket name!)
        bucket_name = "enterprise-genai-agent-sharad-2026" # <-- UPDATE THIS!
        s3_success = upload_to_s3(temp_file_path, bucket_name)
        
        if not s3_success:
            raise HTTPException(status_code=500, detail="Failed to upload to S3.")
            
        # 3. Ingest into local Chroma DB vector store
        ingest_pdf_to_chroma(temp_file_path)
        
        return {"status": "success", "message": f"'{file.filename}' uploaded and ingested successfully."}
        
    finally:
        # Cleanup: Delete the temporary file from the container's hard drive
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)

# ==========================================
# ENDPOINT 2: Ask the Custom LangGraph Agent
# ==========================================
@app.post("/ask-custom-agent", include_in_schema=False)
async def ask_custom_agent(request: QueryRequest):
    """
    Sends a user query to our explicit LangGraph Supervisor Agent.
    """
    try:
        # Format the input for LangGraph
        initial_state = {"messages": [HumanMessage(content=request.query)]}
        
        # Invoke the graph (We use .invoke() instead of .stream() for standard API responses)
        final_state = agent_app.invoke(initial_state)
        
        # Extract the final message from the LLM
        last_message = final_state["messages"][-1]
        
        # Handle Amazon Nova's potential list-based output format
        final_text = ""
        if isinstance(last_message.content, list):
            for block in last_message.content:
                if isinstance(block, dict) and "text" in block:
                    final_text += block["text"] + "\n"
                elif isinstance(block, str):
                    final_text += block + "\n"
        else:
            final_text = last_message.content

        # Strip out the <thinking> tags 
        # re.DOTALL ensures it removes multi-line thinking blocks
        clean_text = re.sub(r'<thinking>.*?</thinking>', '', final_text, flags=re.DOTALL).strip()
            
        return {
            "status": "success",
            "query": request.query,
            "answer": clean_text
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    

# ==========================================
# ENDPOINT 3: For the Bedrock Managed Agent
# ==========================================
@app.get("/api/get-employee-data", operation_id="get_employee_data")
async def get_employee_data(
    employee_id: int = Query(..., description="The unique numeric ID of the employee to look up.")
):
    """
    Fetches the leave balance and department for a specific employee.
    The Bedrock Agent will call this endpoint automatically.
    """
    try:
        conn = sqlite3.connect('company_data.db')
        cursor = conn.cursor()
        cursor.execute("SELECT name, department, leave_days_remaining FROM employee_balances WHERE employee_id = ?", (employee_id,))
        result = cursor.fetchone()
        conn.close()
        
        if result:
            return {
                "employee_id": employee_id,
                "name": result[0],
                "department": result[1],
                "leave_days_remaining": result[2]
            }
        else:
            raise HTTPException(status_code=404, detail="Employee not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Health check endpoint for AWS ECS Fargate later
@app.get("/health", include_in_schema=False)
async def health_check():
    return {"status": "healthy"}
import os
from dotenv import load_dotenv

# LangChain imports for RAG
from langchain_aws import BedrockEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from langchain_core.tools import tool

# Import the extraction function we wrote in Step 2!
from document_utils import extract_text_from_pdf

load_dotenv()

# 1. Initialize Amazon Titan Embeddings via Bedrock
embeddings = BedrockEmbeddings(
    model_id="amazon.titan-embed-text-v2:0",
    region_name=os.getenv("AWS_DEFAULT_REGION")
)

# The folder where our local Vector Database will live
VECTOR_STORE_DIR = "./chroma_db"

def ingest_pdf_to_chroma(pdf_path):
    """Reads a PDF, chunks it, embeds it, and saves it to ChromaDB."""
    print(f"\n--- Starting Ingestion for {pdf_path} ---")
    
    # Step A: Extract the text
    text = extract_text_from_pdf(pdf_path)
    if not text:
        print("No text found to ingest.")
        return
    
    # Step B: Chunking Strategy
    # We use RecursiveCharacterTextSplitter (The industry standard)
    print("Chunking the document...")
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,   # 500 characters per chunk
        chunk_overlap=50  # 50 character overlap so we don't cut sentences in half
    )
    chunks = text_splitter.split_text(text)
    print(f"Created {len(chunks)} chunks.")

    # Step C: Generate Embeddings and Store in Vector DB
    print("Generating Amazon Titan embeddings and saving to ChromaDB...")
    vectorstore = Chroma.from_texts(
        texts=chunks,
        embedding=embeddings,
        persist_directory=VECTOR_STORE_DIR
    )
    print("Successfully ingested into ChromaDB!")


# Step D: Create the Agent Tool
# The @tool decorator tells LangGraph "This is a function the AI is allowed to use!"
@tool
def search_policy_documents(query: str) -> str:
    """
    Searches the company policy documents for the given query.
    Use this tool to find rules, HR policies, guidelines, and document text.
    """
    print(f"\n[Tool Execution] Searching Vector DB for: '{query}'")
    
    # Connect to our existing database
    vectorstore = Chroma(
        persist_directory=VECTOR_STORE_DIR,
        embedding_function=embeddings
    )
    
    # Retrieve the top 3 most mathematically similar chunks
    results = vectorstore.similarity_search(query, k=3)
    
    if not results:
        return "No relevant policy documents found."
    
    # Combine the chunks into a single readable string for the LLM
    context = "\n\n...\n\n".join([doc.page_content for doc in results])
    return context


if __name__ == "__main__":
    # --- TEST THE PIPELINE ---
    
    SAMPLE_PDF = "sample_policy.pdf"
    
    if os.path.exists(SAMPLE_PDF):
        # 1. Ingest the document into the database
        ingest_pdf_to_chroma(SAMPLE_PDF)
        
        # 2. Test the Search Tool exactly how the AI will use it
        print("\n--- Testing the Search Tool ---")
        test_query = "What is the leave policy?" # Change this to match text in your PDF!
        answer = search_policy_documents.invoke(test_query)
        
        print(f"\n🔍 Retrieved Context for '{test_query}':")
        print("-" * 40)
        print(answer)
        print("-" * 40)
    else:
        print(f"Please ensure '{SAMPLE_PDF}' is in the project folder.")
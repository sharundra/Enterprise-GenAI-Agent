import os
from dotenv import load_dotenv
from langchain_aws import ChatBedrockConverse

# 1. Load the AWS and LangSmith keys from the .env file
load_dotenv()

print("Authenticating with AWS Bedrock...")

# 2. Initialize the Bedrock LLM
# Note: We can change the model_id to match the exact Claude version you enabled 
# (e.g., anthropic.claude-3-5-sonnet-20241022-v2:0 or anthropic.claude-3-haiku-20240307-v1:0)
llm = ChatBedrockConverse( 
    model="amazon.nova-lite-v1:0",
    region_name=os.getenv("AWS_DEFAULT_REGION")
)

# 3. Send a test prompt
print("Sending prompt to Model...")
try:
    response = llm.invoke("Hello, Model! Are you successfully connected to my local machine via AWS Bedrock?")
    print("\n SUCCESS! Response from Model:")
    print("-" * 40)
    print(response.content)
    print("-" * 40)
except Exception as e:
    print("\n ERROR connecting to Bedrock:")
    print(e)
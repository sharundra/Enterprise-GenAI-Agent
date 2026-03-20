import os
import sqlite3
from dotenv import load_dotenv

# Core LangChain & LangGraph imports
from langchain_core.tools import tool
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_aws import ChatBedrockConverse
from langgraph.graph import StateGraph, START, END, MessagesState
from langgraph.prebuilt import ToolNode
from langgraph.graph import END

# Import our RAG tool from the previous step!
from rag_pipeline import search_policy_documents

load_dotenv()

# ==========================================
# 1. DEFINE THE TOOLS (The Workers)
# ==========================================
@tool
def query_employee_database(sql_query: str) -> str:
    """
    Executes a SQL query against the company SQLite database.
    The database has one table named 'employee_balances' with columns:
    - employee_id (INTEGER)
    - name (TEXT)
    - department (TEXT)
    - leave_days_remaining (INTEGER)
    
    ONLY pass valid SQL SELECT queries to this tool.
    """
    print(f"\n[Worker Node] Executing SQL Query: {sql_query}")
    try:
        conn = sqlite3.connect('company_data.db')
        cursor = conn.cursor()
        cursor.execute(sql_query)
        results = cursor.fetchall()
        conn.close()
        
        if not results:
            return "No results found in the database."
        return str(results)
    except Exception as e:
        return f"SQL Error: {e}"

tools = [search_policy_documents, query_employee_database]

# ==========================================
# 2. INITIALIZE THE LLM (The Supervisor)
# ==========================================
llm = ChatBedrockConverse(
    model="amazon.nova-lite-v1:0", 
    region_name=os.getenv("AWS_DEFAULT_REGION"),
    temperature=0.1 
)

# Bind the tools to the LLM so it knows they exist
llm_with_tools = llm.bind_tools(tools)

system_prompt = SystemMessage(content="""
You are an intelligent HR and Operations Assistant for the company.
You have access to two tools:
1. search_policy_documents: Use this to look up company rules, guidelines, and text policies.
2. query_employee_database: Use this to look up specific employee data and leave balances using SQL.

If the user asks a hybrid question, use BOTH tools before answering.
Synthesize the final answer clearly.
""")

# ==========================================
# 3. DEFINE THE GRAPH NODES
# ==========================================
def supervisor_node(state: MessagesState):
    """This node calls the LLM to decide the next step."""
    # We pass the system prompt + the conversation history to the LLM
    messages = [system_prompt] + state["messages"]
    response = llm_with_tools.invoke(messages)
    # We return the response to be appended to the state
    return {"messages": [response]}



# LangGraph provides a prebuilt ToolNode that handles the messy 
# JSON parsing of actually running the Python functions
worker_node = ToolNode(tools)

def custom_router(state: MessagesState):
    """
    Checks the LLM's last message. 
    If it wants to use a tool, route to the worker. 
    If it just generated text, route to the END.
    """
    last_message = state["messages"][-1]
    
    # Does the LLM's message contain a request to use a tool?
    if last_message.tool_calls:
        return "action_worker" # Route to our worker node
    
    # If not, the conversation turn is finished
    return END

# ==========================================
# 4. BUILD THE EXPLICIT GRAPH
# ==========================================
workflow = StateGraph(MessagesState)

# We can name our nodes clearly now!
workflow.add_node("supervisor_llm", supervisor_node)
workflow.add_node("action_worker", worker_node)

# 1. Start at the Supervisor
workflow.add_edge(START, "supervisor_llm")

# 2. After the Supervisor thinks, use our custom router to decide where to go
workflow.add_conditional_edges(
    "supervisor_llm",
    custom_router
)

# 3. If the router sent us to the worker, the worker must ALWAYS 
# report back to the supervisor afterward to synthesize the answer.
workflow.add_edge("action_worker", "supervisor_llm")

# Compile the graph
agent_app = workflow.compile()

# ==========================================
# 5. RUN THE AGENT
# ==========================================
if __name__ == "__main__":
    print("Enterprise Agent Initialized. Type 'quit' to exit.")
    print("-" * 50)
    
    while True:
        user_input = input("\nUser: ")
        if user_input.lower() in ['quit', 'exit']:
            break
            
        print("\nAgent is thinking...")
        
        initial_state = {"messages": [HumanMessage(content=user_input)]}
        
        # Stream the graph execution
        for event in agent_app.stream(initial_state):
            for node_name, node_state in event.items():
                
                if node_name == "action_worker":
                    print(f"   -> [Graph Router] Worker Node finished executing tools.")
                
                elif node_name == "supervisor_llm":
                    last_message = node_state["messages"][-1]
                    
                    # If the LLM decided to use a tool, print which tool it chose!
                    if last_message.tool_calls:
                        tool_names = [t['name'] for t in last_message.tool_calls]
                        print(f"   -> [Supervisor] Decided to use tools: {tool_names}")
                    
                    # If there are no tool calls, this is the final synthesized answer!
                    else:
                        print("\nAgent Final Answer:")
                        print("-" * 40)
                        
                        # Amazon Nova sometimes returns a list of dictionaries. 
                        # This safely extracts the text no matter the format.
                        if isinstance(last_message.content, list):
                            for block in last_message.content:
                                if isinstance(block, dict) and "text" in block:
                                    print(block["text"])
                                else:
                                    print(block)
                        else:
                            print(last_message.content)
                            
                        print("-" * 40)
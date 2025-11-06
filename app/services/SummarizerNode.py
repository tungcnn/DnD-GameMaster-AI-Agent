import tiktoken
import os
from langchain_core.messages import BaseMessage, SystemMessage
from langchain_openai import ChatOpenAI
from app.DTOs.GameState import GameState
from dotenv import load_dotenv

load_dotenv()

BASE_URL = os.getenv("AZURE_OPENAI_ENDPOINT")
LLM_API_KEY = os.getenv("AZURE_OPENAI_API_KEY")
LLM_MODEL_NAME = os.getenv("AZURE_DEPLOYMENT_NAME")
ENCODER = tiktoken.encoding_for_model(LLM_MODEL_NAME.lower())
TOKEN_LIMIT = 12000
MESSAGES_TO_KEEP = 6

def count_messages_tokens(messages: list[BaseMessage]) -> int:
    """Counts the total tokens in a list of BaseMessage objects."""
    text = "\n".join([m.content for m in messages])
    return len(ENCODER.encode(text))

async def summarize_history_node(state: GameState) -> GameState:
    messages: list[BaseMessage] = state["messages"]
    
    # Isolate messages to summarize (all but the most recent N)
    old_messages = messages[:-MESSAGES_TO_KEEP]
    recent_messages = messages[-MESSAGES_TO_KEEP:]
    
    llm_summarizer = ChatOpenAI(
        model=LLM_MODEL_NAME,
        base_url=BASE_URL,
        api_key=LLM_API_KEY,
        temperature=0.1,
        timeout=300,
    ) 

    summary_text = await llm_summarizer.ainvoke(f"""Tóm tắt đoạn chat sau, 
        giữ lại hết mức có thể nội dung chính và ngữ cảnh:
        {old_messages}
    """)
    
    summary_message = SystemMessage(
        content=f"Summary of previous conversation history: {summary_text.content}"
    )
    
    # Update the state: Summary + Recent Messages
    new_messages = [summary_message] + recent_messages
    state["messages"] = new_messages
    print("Summarized chat")
    return state

def check_for_summarization(state: GameState) -> str:
    """Routes to summarization if the context window is near the limit."""
    messages = state.get("messages", [])
    
    if not messages:
        return "continue" # Nothing to summarize
        
    token_count = count_messages_tokens(messages)
    
    if token_count > TOKEN_LIMIT:
        return "summarize_history"
    else:
        # Continue to the main LLM call
        return "continue"
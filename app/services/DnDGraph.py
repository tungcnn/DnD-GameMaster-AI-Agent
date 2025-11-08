import os
from langgraph.graph import StateGraph, START
from langchain_openai import ChatOpenAI
from app.config.LoadAppConfig import LoadAppConfig
from app.DTOs.GameState import GameState
from app.services.RAGTool import monster_query_tool, player_query_tool, phandelverstory_query_tool, handle_skill_check_tool, combat_tool, ask_skill_check_tool
from app.services.ToolNode import BasicToolNode, route_tools
from app.services.SummarizerNode import summarize_history_node, check_for_summarization
from app.services.SqliteService import sqlite_service
from dotenv import load_dotenv

load_dotenv()
CFG = LoadAppConfig()

def build_graph():
    BASE_URL = os.getenv("AZURE_OPENAI_ENDPOINT")
    LLM_API_KEY = os.getenv("AZURE_OPENAI_API_KEY")
    LLM_MODEL_NAME = os.getenv("AZURE_DEPLOYMENT_NAME")
    
    dnd_llm = ChatOpenAI(
        model=LLM_MODEL_NAME,
        base_url=BASE_URL,
        api_key=LLM_API_KEY,
        temperature=CFG.primary_agent_llm_temperature,
        timeout=300,
    ) 
    
    dnd_graph = StateGraph(GameState)

    tools = [
        monster_query_tool,
        player_query_tool,
        phandelverstory_query_tool,
        handle_skill_check_tool,
        combat_tool,
        ask_skill_check_tool
    ]

    dnd_llm_with_tools = dnd_llm.bind_tools(tools)

    def handle_chat(state: GameState):
        return {"messages": [dnd_llm_with_tools.invoke(state["messages"])]}

    dnd_graph.add_node("main_chat_node", handle_chat)
    tool_node = BasicToolNode(tools=tools)
    dnd_graph.add_node("tools_node", tool_node)

    dnd_graph.add_conditional_edges(
        "main_chat_node",
        route_tools,
        {"tools": "tools_node", "__end__": "__end__"},
    )

    dnd_graph.add_edge("tools_node", "main_chat_node")
    dnd_graph.add_edge(START, "main_chat_node")
    
    dnd_graph.add_node("summarize_history", summarize_history_node)
    dnd_graph.add_conditional_edges(
        "tools_node", # Check after tools/before LLM call
        check_for_summarization,
        {"summarize_history": "summarize_history", "continue": "main_chat_node"}
    )
    dnd_graph.add_edge("summarize_history", "main_chat_node")

    graph = dnd_graph.compile(checkpointer=sqlite_service.checkpointer)

    return graph

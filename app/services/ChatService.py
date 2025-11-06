import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_core.output_parsers.openai_tools import PydanticToolsParser
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from pydantic import SecretStr

from dotenv import load_dotenv
from typing import List
from app.DTOs.GameState import GameState
from app.models.PlayerCharacter import PlayerCharacter
from app.config.LoadAppConfig import LoadAppConfig
from app.services.DnDGraph import build_graph

CFG = LoadAppConfig()

class ChatService:
    def __init__(
            self,
            llm_api_key=None,
            base_url=None,
            llm_model_name=None,
            embedding_model=None,
            embedding_api_key=None,
    ):
        load_dotenv()
        BASE_URL: str | None = base_url or os.getenv("AZURE_OPENAI_ENDPOINT")
        EMBEDDING_MODEL_NAME: str | None = embedding_model or os.getenv("AZURE_EMBEDDING_NAME")
        EMBEDDING_API_KEY: str | None = embedding_api_key or os.getenv("AZURE_EMBEDDING_API_KEY")
        LLM_API_KEY: str | None = llm_api_key or os.getenv("AZURE_OPENAI_API_KEY")
        LLM_MODEL_NAME: str | None = llm_model_name or os.getenv("AZURE_DEPLOYMENT_NAME")

        self.embedding_model = OpenAIEmbeddings(
            model=(EMBEDDING_MODEL_NAME if EMBEDDING_MODEL_NAME is not None else ""),
            base_url=BASE_URL,
            api_key=SecretStr(
                EMBEDDING_API_KEY if EMBEDDING_API_KEY is not None else ""
            )
        )
        
        self.llm_model = ChatOpenAI(
            model=LLM_MODEL_NAME,
            base_url=BASE_URL,
            api_key=LLM_API_KEY,
            temperature=CFG.primary_agent_llm_temperature,
            timeout=300,
        ) 

        message = SystemMessage(CFG.init_system_message)
        self.game_state = GameState(messages=[message])
        self.dnd_graph = build_graph()

        # Character data extraction chan
        self.llm_player_extractor = self.llm_model.bind_tools(
            [PlayerCharacter]
        ) | PydanticToolsParser(tools=[PlayerCharacter])

    # ------------------------------Methods---------------------------------

    async def init_character_info(self, state: GameState) -> list[PlayerCharacter]:
        players: list[PlayerCharacter] = state.get("players") or []
        if players:
            return players

        character_data: str = CFG.fighter + CFG.wizard
        return await self.llm_player_extractor.ainvoke(character_data)
   
    async def chat(self, input_msg: str, session_id: str) -> str:
        cfg = {"configurable": {"thread_id": session_id}}
        
        if not self.game_state.get("players"):
            await self.init_character_info(self.game_state)
        
        self.game_state.get("messages").append(HumanMessage(input_msg))
        
        events = self.dnd_graph.astream(
            {"messages": self.game_state.get('messages')}, config=cfg, stream_mode="values"
        )
        response_content = ""
        async for event in events:
            response_content = event["messages"][-1].content
            event["messages"][-1].pretty_print()

        # Update conversation with the new assistant message
        self.game_state.get("messages").append(AIMessage(response_content))
        return response_content

    def generate_embedding(self, text: str) -> List[float]:
        """
        Generate embedding for a given text using OpenAI.

        Args:
            text: Text to generate embedding for

        Returns:
            List of floats representing the embedding vector
        """
        try:
            embedding = self.embedding_model.embed_query(text)
            return embedding
        except Exception as e:
            print(f"Error generating embedding: {e}")
            raise

openai_service = ChatService()

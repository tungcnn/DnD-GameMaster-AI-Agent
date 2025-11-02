import os
import aiofiles
from dotenv import load_dotenv
from langchain_classic.chains.summarize import load_summarize_chain
from langchain_core.documents import Document
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.output_parsers.openai_tools import PydanticToolsParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END
from pydantic import SecretStr

from dotenv import load_dotenv
from typing import List
from app.DTOs.GameState import ChatContent, GameState
from app.models.PlayerCharacter import PlayerCharacter
from app.services.SqliteService import sqlite_service

from app.services.CombatService import combat_service

few_shot_examples = [
    ("user", "Bắt đầu trò chơi"),
    ("assistant", """
        Hành trình của bạn diễn ra yên ả, nhưng hòn đảo hiện ra ngoài mũi tàu hứa hẹn những điều kỳ diệu hiếm có. 
        Tảo biển lấp lánh dưới mặt nước với muôn vàn sắc màu rực rỡ, những tia nắng mặt trời xuyên qua bầu trời u ám 
        chiếu sáng thảm cỏ xanh và những tảng đá bazan đen của hòn đảo. 
        Tránh xa những mỏm đá nhô lên từ đại dương, con tàu của bạn chậm rãi tiến vào một bến cảng yên bình ở phía Bắc đảo. 
        Trên bãi biển, bạn bắt gặp hai zombie đang lảo đảo tiến đến!
    """),
    ("user", "Tôi có thể làm gì trong combat"),
    ("assistant", """
        As a Fighter, you can perform this action: Attack - With your weapon: Greataxe (1D12) + Str Modifiers
    """),
    ("user", "Tôi tấn công con zombie gần nhất bằng thanh kiếm của mình."),
    ("assistant", """
        Bạn vung thanh kiếm về phía con zombie! Không khí rít lên khi lưỡi thép vẽ một đường vòng cung chết chóc. 
        Bạn tung xúc xắc được 18 — trúng đòn! Gây (3+2)+3 = 8 sát thương!
        Con zombie rít lên đau đớn, nhưng vẫn chưa gục ngã.
        Đến lượt của zombie! Nó lao về phía bạn và cắn mạnh!
        (D20 = 12) — Trúng đòn! Bạn nhận 3 sát thương!
        Đến lượt bạn rồi, anh hùng!
    """)
]

class OpenAIService:
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
        LLM_API_KEY: str | None = llm_api_key or os.getenv("AZURE_OPENAI_API_KEY")
        LLM_MODEL_NAME: str | None = llm_model_name or os.getenv(
            "AZURE_DEPLOYMENT_NAME"
        )
        EMBEDDING_MODEL_NAME: str | None = embedding_model or os.getenv("AZURE_EMBEDDING_NAME")
        EMBEDDING_API_KEY: str | None = embedding_api_key or os.getenv("AZURE_EMBEDDING_API_KEY")

        self.embedding_model = OpenAIEmbeddings(
            model=(EMBEDDING_MODEL_NAME if EMBEDDING_MODEL_NAME is not None else ""),
            base_url=BASE_URL,
            api_key=SecretStr(
                EMBEDDING_API_KEY if EMBEDDING_API_KEY is not None else ""
            )
        )
        
        self.tools = [
            combat_service.moves_list
        ]
                
        self.llm_model = ChatOpenAI(
            model=LLM_MODEL_NAME if LLM_MODEL_NAME is not None else "",
            base_url=BASE_URL,
            api_key=SecretStr(LLM_API_KEY if LLM_API_KEY is not None else ""),
            temperature=0.8,
            timeout=300,
        )
        
        self.llm_with_tools = self.llm_model.bind_tools(self.tools)
        
        # Base chain
        base_prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    "{system_instruction}",
                ),
                # *few_shot_examples,
                ("assistant", "{extra_content}"),
                ("user", "{input}"),
            ]
        )
        self.base_chain = base_prompt | self.llm_with_tools | StrOutputParser()

        # Summarizer chain
        # SUMMARIZER_MODEL = "VietAI/vit5-base-vietnews-summarization"
        # tokenizer = AutoTokenizer.from_pretrained(SUMMARIZER_MODEL)
        # model = AutoModelForSeq2SeqLM.from_pretrained(SUMMARIZER_MODEL)
        # summarizer_pipeline = pipeline(task="summarization", model=model, tokenizer=tokenizer)
        # hf = HuggingFacePipeline(pipeline=summarizer_pipeline)
        map_prompt = ChatPromptTemplate.from_template(
            """Tóm tắt ngắn gọn nội dung sau bằng tiếng Việt:
            Kết hợp đoạn tóm tắt cũ và đoạn chat gần nhất để ra đoạn tóm tắt mới
            Tóm tắt cũ: {old_summary}
            Đoạn chat gần nhất:\n{recent_chat}
            """)
        self.summarizer_chain = load_summarize_chain(
            self.llm_model,
            chain_type="stuff",  # can be "stuff", "refine", etc.
            prompt=map_prompt,
            verbose=True,
            document_variable_name="recent_chat"
        )

        # Character data extraction chan
        self.player_extractor_chain = self.llm_model.bind_tools(
            [PlayerCharacter]
        ) | PydanticToolsParser(tools=[PlayerCharacter])

        # ---- Build the graph ----
        self.graph: StateGraph | None = None
        self.game_master_chain = None

    # ------------------------------Methods---------------------------------
    def init_openai_service(self):
        self.graph = StateGraph(GameState)
        self.graph.add_node("ensure_system", self.ensure_system)
        self.graph.add_node("invoke_base_chain", self.invoke_base_chain)
        self.graph.add_node("summarize_chat", self.summarize_chat)
        
        # ---- Connect the nodes ----
        self.graph.set_entry_point("ensure_system")
        self.graph.add_edge("ensure_system", "invoke_base_chain")
        self.graph.add_edge("invoke_base_chain", "summarize_chat")
        self.graph.add_edge("summarize_chat", END)
        self.game_master_chain = openai_service.graph.compile(checkpointer=sqlite_service.checkpointer)

    async def ensure_system(self, state: GameState) -> GameState:
        if state.get("sys_msg"):
            return {}
        return {
            "sys_msg": await OpenAIService.get_system_message(),
            "players": await self.init_character_info(state),
        }

    @staticmethod
    async def get_system_message() -> str:
        try:
            async with aiofiles.open("resource/init-prompt.txt", "r") as file:
                init_script: str = await file.read()
        except FileNotFoundError as _:
            init_script: str = """Hello world"""
        return init_script

    async def init_character_info(self, state: GameState) -> list[PlayerCharacter]:
        players: list[PlayerCharacter] = state.get("players") or []
        if players:
            return players
        try:
            async with aiofiles.open("resource/character-sheet.txt", "r") as file:
                character_data: str = await file.read()
        except FileNotFoundError as _:
            character_data: str = """Default character sheet:"""
        return await self.player_extractor_chain.ainvoke(character_data)

    async def invoke_base_chain(self, state: GameState) -> GameState:
        print("invoke_base_chain")
        chat_history: list[ChatContent] = state.get("chat_history") or []
        sys_msg: str = state.get("sys_msg") or ""
        user_input = state.get("input") or ""
        
        if not sys_msg:
            return {
                "chat_history": (
                        chat_history
                        + [
                            ChatContent(
                                role="assistant", content="sys_msg not yet initialized"
                            )
                        ]
                )[-100:]
            }
        if not state.get("chat_history"):
            response: str = await self.base_chain.ainvoke(
                {
                    "system_instruction": sys_msg,
                    "extra_content": f"""
                        You are a DnD Dungeon Master running the campaign Dragon of Storm Wreck Isles

                        Người chơi hiện tại: {state.get("players") if state.get("players") else "Non"}
                    """,
                    "input": user_input,
                }
            )
        else:
            response: str = await self.base_chain.ainvoke(
                {
                    "system_instruction": sys_msg,
                    "extra_content": f"""
                        {state.get("summary") or "No available summary"}

                        Người chơi hiện tại: {state.get("players") if state.get("players") else "Non"}
                    """,
                    "input":user_input,
                }
            )
        return {
            "chat_history": (
                    chat_history
                    + [
                        ChatContent(role="user", content=user_input),
                        ChatContent(role="assistant", content=response),
                    ]
            )[-100:]
        }
   
    async def summarize_chat(self, state: GameState) -> GameState:
        chat_history: list[ChatContent] = state.get("chat_history") or []
        if not chat_history:
            return {}
        docs: list[Document] = [Document(page_content=f"{msg.get("role")} - {msg.get("content")}") for msg in
                                chat_history[-2:]]
        response = await self.summarizer_chain.ainvoke(
            {"input_documents": docs, "old_summary": state.get("summary") or "Không có đoạn tóm tắt cũ nào"})
        return {"summary": response.get("output_text")}

    async def chat(self, input_msg: str, session_id: str) -> str:
        cfg = {"configurable": {"thread_id": session_id}}
        result = await self.game_master_chain.ainvoke(GameState(input=input_msg), config=cfg)  # type: ignore
        return result["chat_history"][-1]["content"]

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

openai_service = OpenAIService()

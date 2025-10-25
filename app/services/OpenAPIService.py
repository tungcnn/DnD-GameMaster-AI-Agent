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


class OpenAIService:
    def __init__(
            self,
            llm_api_key=None,
            base_url=None,
            llm_model_name=None,
            # embedding_model=None,
            # embedding_api_key=None,
    ):
        load_dotenv()
        BASE_URL: str | None = base_url or os.getenv("AZURE_OPENAI_ENDPOINT")
        LLM_API_KEY: str | None = llm_api_key or os.getenv("AZURE_OPENAI_API_KEY")
        LLM_MODEL_NAME: str | None = llm_model_name or os.getenv(
            "AZURE_DEPLOYMENT_NAME"
        )
        # EMBEDDING_MODEL_NAME: str | None = embedding_model or os.getenv("")
        # EMBEDDING_API_KEY: str | None = embedding_api_key or os.getenv("")

        # self.embedding_model = OpenAIEmbeddings(
        #     model=(EMBEDDING_MODEL_NAME if EMBEDDING_MODEL_NAME is not None else ""),
        #     base_url=BASE_URL,
        #     api_key=SecretStr(
        #         EMBEDDING_API_KEY if EMBEDDING_API_KEY is not None else ""
        #     ),
        # )
        self.llm_model = ChatOpenAI(
            model=LLM_MODEL_NAME if LLM_MODEL_NAME is not None else "",
            base_url=BASE_URL,
            api_key=SecretStr(LLM_API_KEY if LLM_API_KEY is not None else ""),
            temperature=0.2,
            timeout=300,
        )

        # Base chain
        base_prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    "{system_instruction}",
                ),
                ("assistant", "{extra_content}"),
                ("user", "{input}"),
            ]
        )
        self.base_chain = base_prompt | self.llm_model | StrOutputParser()

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
        chat_history: list[ChatContent] = state.get("chat_history") or []
        sys_msg: str = state.get("sys_msg") or ""
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
                        Bối cảnh: Lênh đênh trên một con thuyền gỗ, nhóm các bạn đang chuẩn bị cập bến vào hòn đảo Storm Wreck sau một chuyến đi dài.
                        Phóng mắt ra tầm xa, các bạn có thể thấy xung quanh đảo có rất nhiều xác tàu chìm, tàu đắm, thậm chí là nghe thấy những âm thanh rùng rợn phát ra từ đó.
                        Cuối cùng, các bạn cập bến ở trong một làng chài nhỏ tên là Saltmarsh, nơi mà những tin đồn về những con rồng và mối đe dọa từ hải tặc đang rình rập.
                        Làng này nổi tiếng cạn kiệt vì nạn cướp biển ở vùng biển Stormwreck.
                        Các bạn muốn làm gì?

                        Người chơi hiện tại: {state.get("players") if state.get("players") else "Non"}
                    """,
                    "input": state.get("input") or "",
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
                    "input": state.get("input"),
                }
            )
        return {
            "chat_history": (
                    chat_history
                    + [
                        ChatContent(role="user", content=state.get("input") or ""),
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

    def __init_character_info(self, state: GameState) -> list[PlayerCharacter]:
        players: list[PlayerCharacter] = state.get("players") or []
        if not players:
            try:
                with open("resource/character-sheet.txt", "r") as file:
                    character_data: str = file.read()
                    players: list[PlayerCharacter] = (
                        self.__player_extractor_chain.invoke(character_data)
                    )
            except:
                character_data: str = """Default character sheet:"""
        return players

    def generate_embedding(self, text: str) -> List[float]:
        """
        Generate embedding for a given text using OpenAI.

        Args:
            text: Text to generate embedding for

        Returns:
            List of floats representing the embedding vector
        """
        try:
            embedding = self.__embedding_model.embed_query(text)
            return embedding
        except Exception as e:
            print(f"Error generating embedding: {e}")
            raise

openai_service = OpenAIService()

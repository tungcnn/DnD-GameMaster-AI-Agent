import os
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.output_parsers.openai_tools import PydanticToolsParser
from langchain.chains.summarize import load_summarize_chain
from pydantic import SecretStr
from langchain_core.documents import Document
from langgraph.graph import StateGraph, END
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

        # Initialize embedding model for semantic search
        self.__embedding_model = OpenAIEmbeddings(
            model=(EMBEDDING_MODEL_NAME if EMBEDDING_MODEL_NAME is not None else "text-embedding-3-small"),
            base_url=BASE_URL,
            api_key=SecretStr(
                EMBEDDING_API_KEY if EMBEDDING_API_KEY is not None else LLM_API_KEY if LLM_API_KEY is not None else ""
            ),
        )
        self.__llm_model = ChatOpenAI(
            model=LLM_MODEL_NAME if LLM_MODEL_NAME is not None else "",
            base_url=BASE_URL,
            api_key=SecretStr(LLM_API_KEY if LLM_API_KEY is not None else ""),
            temperature=0.3,
            timeout=300,
        )
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
        summarizer_prompt = ChatPromptTemplate.from_template(
            """
            Dựa vào đoạn tóm tắt cũ này: {old_summary}
            Tóm tắt đoạn chat sau đây và nối tiếp vào đoạn tóm tắt trên dựa theo ý cảnh nếu có: {docs}
            """
        )

        # ---- Chain ----
        self.__base_chain = base_prompt | self.__llm_model | StrOutputParser()
        self.__summarizer_chain = load_summarize_chain(
            llm=self.__llm_model,
            chain_type="stuff",
            prompt=summarizer_prompt,
            document_variable_name="docs",
        )
        self.__player_extractor_chain = self.__llm_model.bind_tools(
            [PlayerCharacter]
        ) | PydanticToolsParser(tools=[PlayerCharacter])

        # ---- Build the graph ----
        graph = StateGraph(GameState)
        graph.add_node("ensure_system", self.__ensure_system)
        graph.add_node("invoke_base_chain", self.__invoke_base_chain)
        graph.add_node("summarize_chat", self.__summarize_chat)

        # ---- Connect the nodes ----
        graph.set_entry_point("ensure_system")
        graph.add_edge("ensure_system", "invoke_base_chain")
        graph.add_edge("invoke_base_chain", "summarize_chat")
        graph.add_edge("summarize_chat", END)

        # ---- Compile ----
        self.__game_master_chain = graph.compile(
            checkpointer=sqlite_service.checkpointer
        )

    # ------------------------------Methods---------------------------------
    def __ensure_system(self, state: GameState) -> GameState:
        if state.get("sys_msg") or None:
            return {}
        return {
            "sys_msg": self.__init_system_message(),
            "players": self.__init_character_info(state),
        }

    def __init_system_message(self) -> str:
        try:
            with open("resource/init-prompt.txt", "r") as file:
                init_script: str = file.read()
        except:
            init_script: str = """Hello world"""
        return init_script

    def __invoke_base_chain(self, state: GameState) -> GameState:
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
            response = self.__base_chain.invoke(
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
            response = self.__base_chain.invoke(
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

    def __summarize_chat(self, state: GameState) -> GameState:
        chat_history: list[ChatContent] = state.get("chat_history") or []
        if not chat_history:
            return {}
        chat_list: list[str] = list(
            map(
                lambda message: f"{message["role"]} - {message["content"]}",
                chat_history,
            )
        )
        docs: list[Document] = [Document(page_content=chat) for chat in chat_list]
        response = self.__summarizer_chain.invoke(
            {
                "input_documents": docs[-2:],
                "old_summary": state.get("summary")
                or "Chưa có đoạn tóm tắt cũ nào, hãy tóm tắt dựa theo đoạn chat dưới đây",
            }
        )
        return {"summary": response["output_text"]}

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

    def chat(self, input_msg: str, session_id: str) -> str:
        cfg = {"configurable": {"thread_id": session_id}}
        return self.__game_master_chain.invoke(GameState(input=input_msg), config=cfg)["chat_history"][-1]["content"]  # type: ignore


openai_service = OpenAIService()

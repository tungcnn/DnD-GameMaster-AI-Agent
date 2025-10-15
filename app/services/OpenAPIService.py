import os
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser
from langchain_core.chat_history import InMemoryChatMessageHistory
from langchain_core.runnables.history import RunnableWithMessageHistory
from dotenv import load_dotenv
from pydantic import SecretStr

load_dotenv()


class OpenAIService:
    def __init__(
        self,
        llm_api_key=None,
        base_url=None,
        llm_model_name=None,
        embedding_model=None,
        embedding_api_key=None,
    ):
        BASE_URL: str | None = base_url or os.getenv("AZURE_OPENAI_ENDPOINT")
        LLM_API_KEY: str | None = llm_api_key or os.getenv("AZURE_OPENAI_API_KEY")
        LLM_MODEL_NAME: str | None = llm_model_name or os.getenv(
            "AZURE_DEPLOYMENT_NAME"
        )
        EMBEDDING_MODEL_NAME: str | None = embedding_model or os.getenv("")
        EMBEDDING_API_KEY: str | None = embedding_api_key or os.getenv("")

        try:
            with open("resource/init-prompt.txt", "r") as file:
                self.init_script = file.read()
        except:
            self.init_script = """Hello world"""

        self.embedding_model = OpenAIEmbeddings(
            model=(EMBEDDING_MODEL_NAME if EMBEDDING_MODEL_NAME is not None else ""),
            base_url=BASE_URL,
            api_key=SecretStr(
                EMBEDDING_API_KEY if EMBEDDING_API_KEY is not None else ""
            ),
        )
        self.llm_model = ChatOpenAI(
            model=LLM_MODEL_NAME if LLM_MODEL_NAME is not None else "",
            base_url=BASE_URL,
            api_key=SecretStr(LLM_API_KEY if LLM_API_KEY is not None else ""),
            temperature=0.3,
            timeout=300,
        )
        self.prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    "{system_instruction}\n{extra_content}",
                ),
                MessagesPlaceholder("chat_history"),
                ("user", "{input}"),
            ]
        )
        self.chat_history_for_chain = InMemoryChatMessageHistory()
        self.base_chain = self.prompt | self.llm_model | StrOutputParser()

        self.chain_with_history = RunnableWithMessageHistory(
            self.base_chain,  # your LLM / RAG chain
            lambda _: self.chat_history_for_chain,
            input_messages_key="input",
            history_messages_key="chat_history",
        )

    # ------------------------------Methods---------------------------------
    def chat(self, input: str, session_id: str) -> str:
        extra_content: str = (
            "Dùng tiếng việt và nối tiếp câu chuyện cùng với lựa chọn trước đó của người chơi"
        )

        return self.__invoke_chain(self.init_script, extra_content, input, session_id)

    def startGame(self, session_id: str):

        extra_content: str = """Bối cảnh: Lênh đênh trên một con thuyền gỗ, nhóm các bạn đang chuẩn bị cập bến vào hòn đảo Storm Wreck sau một chuyến đi dài.
                 Phóng mắt ra tầm xa, các bạn có thể thấy xung quanh đảo có rất nhiều xác tàu chìm, tàu đắm, thậm chí là nghe thấy những âm thanh rùng rợn phát ra từ đó.
                 Cuối cùng, các bạn cập bến ở trong một làng chài nhỏ tên là Saltmarsh, nơi mà những tin đồn về những con rồng và mối đe dọa từ hải tặc đang rình rập. 
                 Làng này nổi tiếng cạn kiệt vì nạn cướp biển ở vùng biển Stormwreck. 
                 Các bạn muốn làm gì?"""
        return self.__invoke_chain(
            self.init_script, extra_content, "Start game", session_id
        )

    def __invoke_chain(
        self, init_script: str, extra_content: str, input: str, session_id: str
    ) -> str:
        return self.chain_with_history.invoke(
            {
                "input": input,
                "extra_content": extra_content,
                "system_instruction": init_script,
            },
            config={"configurable": {"session_id": session_id}},
        )

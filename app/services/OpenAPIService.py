import os
from openai import OpenAI
from dotenv import load_dotenv
import uvicorn
import app.main

load_dotenv()

class OpenAIService:
    def __init__(self, api_key=None, base_url=None, model=None):
        self.api_key = api_key or os.getenv("AZURE_OPENAI_API_KEY")
        self.base_url = base_url or os.getenv("AZURE_OPENAI_ENDPOINT")
        self.model = model or os.getenv("AZURE_DEPLOYMENT_NAME")

        self.client = OpenAI(
            api_key=self.api_key,
            base_url=self.base_url
        )
    
    def chat(self, messages: list[dict]):
        """Send a chat completion request."""
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages
        )
        return response.choices[0].message.content
    
    def startGame(self):
        try:
            with open("resource/init-prompt.txt", "r") as file:
                initScript = file.read()
        except:
            initScript = """Hello world"""
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": initScript},
                {"role": "user", "content": "Start the game"},
                {"role": "assistant", "content": """
                    Lênh đênh trên một con thuyền gỗ, nhóm các bạn đang chuẩn bị cập bến vào hòn đảo Storm Wreck sau một chuyến đi dài.
                 Phóng mắt ra tầm xa, các bạn có thể thấy xung quanh đảo có rất nhiều xác tàu chìm, tàu đắm, thậm chí là nghe thấy những âm thanh rùng rợn phát ra từ đó.
                 Cuối cùng, các bạn cập bến ở trong một làng chài nhỏ tên là Saltmarsh, nơi mà những tin đồn về những con rồng và mối đe dọa từ hải tặc đang rình rập. 
                 Làng này nổi tiếng cạn kiệt vì nạn cướp biển ở vùng biển Stormwreck. 
                 Các bạn muốn làm gì?
                 """},
                {"role": "user", "content": "Start the game"}
            ]
        )
        return response


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
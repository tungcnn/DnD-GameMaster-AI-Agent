from openai import AzureOpenAI
import os

os.environ["AZURE_OPENAI_ENDPOINT"] = "https://aiportalapi.stu-platform.live/jpe" 
os.environ["AZURE_OPENAI_API_KEY"] = "sk-HOBqRzuLjhzmlLZYtj7y8g" #đổi thành key của mình
os.environ["AZURE_DEPLOYMENT_NAME"] = "GPT-4o-mini"
api_version = "2024-07-01-preview"
client = AzureOpenAI(
api_version=api_version,
azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
api_key=os.getenv("AZURE_OPENAI_API_KEY"),
)


# Step 2: Load transcript text (example: read from a file)
try:
    with open("init-prompt.txt", "r") as file:
        initScript = file.read()
except:
    initScript = """Hello world"""
# Step 3: Craft prompt for summarization
prompt = f"""Use the following configurations to init the campaign and my characters. 
Then start the adventure by an opening background introduction
The config:\n\n{initScript}"""

# Step 4: Call OpenAI ChatCompletion API
response = client.chat.completions.create(
    model=os.getenv("AZURE_DEPLOYMENT_NAME"),
    messages=[
        {"role": "system", "content": "You are a profession DnD 5e dungeon master, here to guide players through an exiciting adventure"},
        {"role": "user", "content": prompt}
    ],
    temperature=0.3,
    max_tokens=500
)
# Step 5: Extract and display summary
summary = response.choices[0].message.content.strip()
print(summary)
prompt = input("Steve sẽ làm gì: ")
prompt += input("Tony sẽ làm gì: ")

def show_menu():
    global prompt
    print("=== Dragon of storm wreck isle ===")
    response = client.chat.completions.create(
    model=os.getenv("AZURE_DEPLOYMENT_NAME"),
    messages=[
        {"role": "system", "content": "Continue the story as a Dungeon Master. Always use Vietnamese"},
        {"role": "user", "content": prompt}
    ],
    temperature=0.3,
    max_tokens=500
    )
    # Step 5: Extract and display summary
    summary = response.choices[0].message.content.strip()
    print(summary)

    prompt = input("Steve sẽ làm gì: ")
    prompt += input("Tony sẽ làm gì: ")

# Gọi hàm
while True:
    show_menu()
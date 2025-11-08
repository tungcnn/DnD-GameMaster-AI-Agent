import os
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings
from langchain_core.tools import tool
from app.config.LoadAppConfig import LoadAppConfig
from dotenv import load_dotenv

TOOLS_CFG = LoadAppConfig()
load_dotenv()

class RAGTool:
    def __init__(self, k: int, collection_name: str) -> None:
        """
        Initializes the monsterRAGTool with the necessary configurations.

        Args:
            k (int): The number of nearest neighbor monster to retrieve based on query similarity.
            collection_name (str): The name of the collection inside the vector database that holds the relevant monster.
        """
        self.embedding_model = TOOLS_CFG.rag_embedding_model
        self.k = k
        self.vectordb = Chroma(
            collection_name=collection_name,
            persist_directory=TOOLS_CFG.rag_vectordb_directory,
            embedding_function=OpenAIEmbeddings(
                model=self.embedding_model,
                base_url=os.getenv("AZURE_OPENAI_ENDPOINT"),
                api_key=os.getenv("AZURE_EMBEDDING_API_KEY")
            )
        )
        print("Number of vectors in vectordb:",
              self.vectordb._collection.count(), "\n\n")
        
@tool
def monster_query_tool(query: str, name: str, size: str, legendary: str, align: str) -> str:
    """
    Consult the monster embedded vector document below for a summarization of a monster. 
    Only reveal appearance, type, habitat, strength level, etc 
    don't reveal any actual stats (such as HP, AC, damage, spells) so as to not spoil players
    
    Args:
    query (str): The player query
    name (str): The name of the monster
    size (str): The size of the monster
    legendary (str): Whether the monster is legendary. If not, leave blank
    align (str): The alignment of the monster
    Returns:
        str: The monster's description based on the return result from embedded data
    Example:
        >>> Ancient Black Dragon là một con rồng huyền thoại khổng lồ! Bọn chúng luôn mang xu hướng chaotic evil!!
        >>> Mind Flayer are Psionic tyrants, slavers, and interdimensional voyagers, they are insidious masterminds that harvest entire races for their own twisted ends.
    """

    rag_tool = RAGTool(
        k=TOOLS_CFG.rag_k_monster,
        collection_name=TOOLS_CFG.monster_rag_collection_name)

    docs = rag_tool.vectordb.similarity_search(query, k=rag_tool.k)
    return "\n\n".join([doc.page_content for doc in docs])

@tool
def player_query_tool(query: str) -> str:
    """
    Look up the player embedded DB and return any information about the query.
    For example, if players ask what subclasss for Fighter class can they choose from,
    give them a brief description of each sub class.
    
    Or if players ask what does Wild Magic sorceror gain on level 6, tell them.
    
    Or if player ask how much damage can they do with a Greataxe, tell them it's 1d12 slash damage!
    
    Or if play ask about the details of a spell, give them a description, damage, range, aoe, etc.
    
    Args:
    query (str): The player query
    Returns:
        str: The description based on the return result from embedded data
    Example:
        >>> Fireball:
        A bright streak flashes from your pointing finger to a point you choose within range 
        and then blossoms with a low roar into an explosion of flame. 
        Each creature in a 20-foot-radius sphere centered on that point must make a dexterity 
        saving throw. A target takes 8d6 fire damage on a failed save, or half as much damage 
        on a successful one.
        Range: 60 ft
        Requirements: V
        Damage: 8d6
        Aoe: 20 ft
        >>> The Greataxe does 1D12 slashing damage by default! Unless you are a savage babarian haha.
        >>> As a Fighter, you will gain an extra attack on level 3. Go beat them up!
    """
    rag_tool = RAGTool(
        k=TOOLS_CFG.rag_k_player,
        collection_name=TOOLS_CFG.player_rag_collection_name
    )
    
    docs = rag_tool.vectordb.similarity_search(query, k=rag_tool.k)
    return "\n\n".join([doc.page_content for doc in docs])

@tool
def phandelverstory_query_tool(query: str) -> str:
    """
    Look up the details of the main campaign, Lost Mines of Phandelver, as players progresses.
    Use this to either answer player's query, of guide the adventure.
    Of use this to act as an NPC when conversing with players
    
    Args:
    query (str): The player query
    Returns:
        str: The story at the moment, with hooks to upcoming events!
        Or lore pieces that relates to player's questions
    Example:
        >>> You've been on the Triboar Trail for about half a day. As you
        come around a bend, you spot two dead horses sprawled
        about fifty feet ahead of you, blocking the path. Each has
        several black-feathered arrows sticking out of it. The woods
        press close to the trail here, with a steep embankment and
        dense thickets on either side. What will you do?
        >>> When you were busy inspecting the satchels, you realized they're all empty. 
        This is a trap! Four goblin jumps out of thin air and point their arrows at you. 
        Roll for initiative!
        >>> "Sildar": "Thank you for rescuing me, adventurer. To answer your question, 
        Yes the Rockseeker brothers recently discovered the long lost entrance to 
        the Wave Echo cave"
    """
    rag_tool = RAGTool(
        k=TOOLS_CFG.rag_k_phandelverstory,
        collection_name=TOOLS_CFG.phandelverstory_rag_collection_name
    )
    
    docs = rag_tool.vectordb.similarity_search(query, k=rag_tool.k)
    return "\n\n".join([doc.page_content for doc in docs])

@tool
def ask_skill_check_tool(skill: str, difficulty: str, player_dice: str, status: str, description: str) -> str:
    """
    Handle when player enter a prompt that might require a skill check
    Come up with a fitting difficulty class to the situation, 
    and ask the user to roll for this skill check.
    Don't show the difficulty to the player, it's for the AI to keep track only (In brackets)
    Args:
    difficulty (str): The difficulty of the skill check the AI came up with
    skill (str): The skill in check. Could be animal handling, investigation, acrobatic, strength, etc
    Returns:
        str: Ask the user to roll for skill check
    Example:
        >>> To search the horse's body, give me an investigation roll (Difficulty 11)
        >>> Give me a perception check, let's see if you can identify the hidden threat 
        in the jungle!
    """
    
    return "Ask player to roll skill check"

@tool
def handle_skill_check_tool(skill: str, difficulty: str, player_dice: str, status: str, description: str) -> str:
    """
    Verify the user's dice roll against the difficulty of the skill check.
    Args:
    difficulty (str): The difficulty of the skill check the AI came up with
    player_dice(str): The dice roll result of the player
    skill (str): The skill in check. Could be animal handling, investigation, acrobatic, strength, etc
    status(str): The status of the skill check, either passed or failed.
    description(str): The description of the result of the skill check
    Returns:
        str: The description of the skill check results
    Example:
        >>> For this strength check of difficulty 15, you failed with a roll of 12!
        You bend down and try to lift the horse's body with all your strength!
        The horse didn't budge at all due to your noodle hands. HAHA! What else can you do?
        >>> For this investigation check of difficulty 9, you passed with a roll of 15!
        You searched horse's body throughly using your experience in hunting.
        With your keen senses, you noticed that the horses have been dead for a while 
        and were dragged here as a bait. This is a trap, you think to yourself. What do you do now?
    """
    
    return f"""For this {skill} check of difficulty {difficulty}, you {status} with a roll of {player_dice}!
        {description}
    """

@tool
def combat_tool(damage: str, hit_status: str, description: str) -> str:
    """
    Handle when player enter a prompt while in combat
    Deny all prompts unrelated to the combat. 
    Calculate the hit against the target's AC, and calculate the damage if it's a hit.
    Ask the player for their stats if you don't know. 
    If the attack requires a saving throw, such as Fireball, 
    roll the saving throw for the target yourselves.
    Don't show players the content within the brackets, such as (Goblin has 9HP left). 
    Content within bracket is only for the AI to track combat stats.
    Args:
    damage (str): The damage of the attack
    hit_status(str): Whether the attack land
    description (str): The description of the result of the attack
    Returns:
        str: The description of the skill check results
    Example:
        >>> You bend your arms and slash the Golbin with your sword. The edge barely missed the 
        Goblin's neck, dealing no damage! (Roll of 9 against 10 AC)
        >>> You aim your bow at the target and release the arrow. It's a direct hit!
        The Goblin loses its balance and stumbled back, angrier than before.
        It took 6 piercing damage. (The goblin has 4 HP left)
        >>> The goblin dashes towards you and tries to club you in the head! What is your AC?
        >>> With an AC of 13, you expertly dodged the goblin's club!
        >>> With an AC of 13, you couldn't dodge the blow from the Goblin. 
        The thich club made from ancient wood bangs your head directly, you took 6 bludgeoning damage!
        >>> The 2 goblins try to dodge your Fireball center of explosion!
         Goblin 1 manages to dodge with a high enough dex roll, dodging out of the way
         with a half burnt leg. Taking only half damage (6 HP left)
         Goblin 2 was too slow, and it took full damage! He burns in agony! (1HP left)
    """
    
    return "Done"
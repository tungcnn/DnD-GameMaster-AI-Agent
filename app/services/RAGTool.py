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



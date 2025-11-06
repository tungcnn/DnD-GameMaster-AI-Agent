import yaml
from pyprojroot import here

class LoadAppConfig:

    def __init__(self) -> None:
        with open(here("resource/app_config.yml")) as cfg:
            app_config = yaml.load(cfg, Loader=yaml.FullLoader)

        # Primary agent
        self.primary_agent_llm_temperature = app_config["primary_agent"]["llm_temperature"]
        
        #Init system message
        self.init_system_message = app_config["init_system_message"]
        
        #Init characters
        self.fighter = app_config["characters"]["Fighter"]
        self.wizard = app_config["characters"]["Wizard"]

        # RAG configs
        self.rag_embedding_model = app_config["rag"]["embedding_model"]
        self.rag_vectordb_directory = str(here(app_config["rag"]["vectordb"]))
        self.rag_chunk_size = app_config["rag"]["chunk_size"]
        self.rag_chunk_overlap = app_config["rag"]["chunk_overlap"]
        
        #Monster
        self.monster_rag_collection_name = app_config["rag"]["collection_name_monster"]
        self.rag_k_monster = app_config["rag"]["k_monster"]
        
        #Player
        self.player_rag_collection_name = app_config["rag"]["collection_name_player"]
        self.rag_k_player = app_config["rag"]["k_player"]
        
        #Phandelver story
        self.phandelverstory_rag_collection_name = app_config["rag"]["collection_name_phandelverstory"]
        self.rag_k_phandelverstory = app_config["rag"]["k_phandelverstory"]


        # Graph configs
        self.thread_id = str(
            app_config["graph_configs"]["thread_id"])

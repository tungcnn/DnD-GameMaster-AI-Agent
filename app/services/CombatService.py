from langchain_core.tools import tool

class CombatState:
    def __init__(self):
        self.in_combat = False
        self.combatants = []
        self.turn_index = 0

combat_state = CombatState()

class CombatService:
    @tool
    def moves_list(class_name: str, move_name: str, details: str) -> str:
        """
        Return the move list of the asking player. Use the embedded class data to find the combat actions available
        Args:
        class_name (str): The player's class
        move_name (str): The name of the move
        details (str): The details of the move
        Returns:
        str: A concatenated string of all moves of the asking player
        Example:
                >>> moves_list('Fighter')
        'As a Fighter, you can perform this action: Attack - With your weapon: Greataxe (1D12) + Str Mod'
        """

        return "As a {class_name}, you can perform this action: {move_name} - {details}"
    
combat_service = CombatService()
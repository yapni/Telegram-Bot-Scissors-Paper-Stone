class Player:
    '''
    Represents a player in the game.
    '''
    
    def __init__(self, player_id, player_name):
        self.id = player_id
        self.name = player_name
        self.move = None
    
    def __str__(self):
        return self.name + " - Move: " + str(self.move)
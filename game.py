from player import Player

class GameSession:
    '''
    Holds the details of a game session in a group chat
    '''

    def __init__(self, chat_id, chat_name):
        self.chat_id = chat_id
        self.chat_name = chat_name
        self.player1 = None
        self.player2 = None
    
    def add_player(self, player_id, player_name):
        '''
        Adds a player to the current session.
        Returns current number of players if success.
        Else returns -1 if there are already 2 players and a new player cannot be added.
        '''
        if self.player1 == None:
            self.player1 = Player(player_id, player_name)
            return 1
        elif self.player2 == None:
            self.player2 = Player(player_id, player_name)
            return 2
        else:
            return -1
    
    def get_num_players(self):
        '''
        Returns the current number of players in the current session.
        '''
        return sum(player is not None for player in [self.player1, self.player2])
        
    def __str__(self):
        return "[Chat ID " + str(self.chat_id) + "]\n" + \
            "Player 1: " + str(self.player1) + "\n" + \
            "Player 2: " + str(self.player2) + "\n"

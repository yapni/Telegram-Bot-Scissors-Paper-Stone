"""
A simple telegram bot that allows users to play a game of "Scissor, Paper, Stone".

A beginner's creation by Yap Ni.
"""

from game import GameSession
from telegram import KeyboardButton
from telegram import ReplyKeyboardMarkup
from telegram.ext import CommandHandler
from telegram.ext import MessageHandler
from telegram.ext import Updater
from telegram.ext.filters import Filters
import logging
import os
import sys

# Fetch required variables
TOKEN = os.getenv('TELEGRAM_SPS_BOT_TOKEN') # Authentication token for this bot
PORT = int(os.environ.get('TELEGRAM_SPS_BOT_PORT', 8443)) # Port number to listen for the webhook (default: 8443)
MODE = os.getenv('TELEGRAM_SPS_BOT_MODE') # Development ('dev') mode or production mode ('prod')
HEROKU_APP_NAME = os.getenv('TELEGRAM_SPS_BOT_HEROKU_NAME') 

# Set up logs
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
LOGGER = logging.getLogger()
LOGGER.setLevel(logging.INFO)

GAME_SESSIONS = dict() # Dictionary mapping active chat_id to game sessions
PLAYER_TO_ACTIVE_CHAT_ID = dict() # Dictionary mapping player's user_id to a queue of chat_id where it is in an active game session

# Representations for scissors, paper, stone
SCISSORS = "✂"
PAPER = "📃"
STONE = "🗿"

# Callback function for /start command
def start(update, context):
    '''
    Starts or restarts a game.
    '''
    chat_id = update.effective_chat.id
    chat_name = update.effective_chat.title

    # Update from private chat
    if update.effective_chat.type == "private":
        send_private_chat_error_message(context.bot, chat_id)
        return

    # Create a new game session. Remove previous session if exists.
    if chat_id in GAME_SESSIONS:
        del GAME_SESSIONS[chat_id]
    GAME_SESSIONS[chat_id] = GameSession(chat_id, chat_name)

    # DEBUG
    for sess in GAME_SESSIONS.values():
        print(sess)

    LOGGER.info("Created a new session in chat [" + str(chat_id) + "]")

    welcome_msg = "Lets play a game of scissors paper stone! Type /join to join the game (maximum 2 players DUH)." \
                    " Players will need to open a private chat to @letsPlaySPS_bot (I am a stupid bot and can't do it myself)."
    context.bot.send_message(chat_id=update.effective_chat.id, text=welcome_msg)

# Callback function for /join command
def join(update, context):
    '''
    Adds a user to a game session.
    '''
    user_name = update.effective_user.username
    user_id = update.effective_user.id
    chat_name = update.effective_chat.title
    chat_id = update.effective_chat.id

    # Update from private chat
    if update.effective_chat.type == "private":
        send_private_chat_error_message(context.bot, chat_id)
        return

    # No existing game session: return error message
    if chat_id not in GAME_SESSIONS:
        LOGGER.info("Error /join command from user [" + user_name + "] in chat [" + str(chat_id) + "]. No existing session.")
        context.bot.send_message(chat_id=chat_id, text="Error! You will need to type /start to start a new game.")
        return

    # Add player to corresponding game session
    num_players = GAME_SESSIONS[chat_id].add_player(user_id, user_name)

    # Failed adding player: return error message
    if num_players == -1:
        LOGGER.info("Failed to add player [" + user_name + "] to the game session in chat [" + str(chat_id) + "]")
        context.bot.send_message(chat_id=chat_id, text="Error! You already have the maximum 2 players in the current session.")
        return
    
    # Success adding player
    LOGGER.info("Added player [" + user_name + "] to the game session in chat [" + str(chat_id) + "]")
    context.bot.send_message(chat_id=user_id, text="You have joined a game in " + chat_name)
    context.bot.send_message(chat_id=chat_id, text="" + user_name + " has joined the game!")

    # DEBUG
    for sess in GAME_SESSIONS.values():
        print(sess)

    # Total number of players fulfilled: start the game
    if num_players == 2:
        player1_name = GAME_SESSIONS[chat_id].player1.name
        player2_name = GAME_SESSIONS[chat_id].player2.name
        context.bot.send_message(chat_id=chat_id, text="It's " + player1_name + " vs. " + player2_name + "!\n" + \
                                    "Let the game begins...")
        start_game(context.bot, GAME_SESSIONS[chat_id])

# Callback function for /status command
def status(update, context):
    '''
    Shows the current players and whether they have made a move in a game session (if any).
    '''
    chat_id = update.effective_chat.id

    # Update from private chat
    if update.effective_chat.type == "private":
        send_private_chat_error_message(context.bot, chat_id)
        return

    # No existing game session: return error message
    if chat_id not in GAME_SESSIONS:
        context.bot.send_message(chat_id=chat_id, text="There is no existing game session. Type /start to start a new session.")
        return
    
    num_players = GAME_SESSIONS[chat_id].get_num_players()

    # Existing game session, but not enough players: return error message
    if num_players != 2:
        player1_text = GAME_SESSIONS[chat_id].player1.name if GAME_SESSIONS[chat_id].player1 else "-"
        player2_text = GAME_SESSIONS[chat_id].player2.name if GAME_SESSIONS[chat_id].player2 else "-"
        players_text = "Player 1: " + player1_text + "\n" + "Player 2: " + player2_text
        message_text = "" + str(2-num_players) + " more player(s) needed!\n\nCurrent players:\n" + players_text 
        context.bot.send_message(chat_id=chat_id, text=message_text)
        return
    
    # Game has started, but player(s) have not made a move
    waiting_move_text = "[Waiting for move...]"
    made_move_text = "[Move made!]"
    player1_move_text = waiting_move_text if not GAME_SESSIONS[chat_id].player1.move else made_move_text
    player2_move_text = waiting_move_text if not GAME_SESSIONS[chat_id].player2.move else made_move_text
    players_text = "Player 1: " + str(GAME_SESSIONS[chat_id].player1.name) + " " + player1_move_text + "\n" + \
                        "Player 2: " + str(GAME_SESSIONS[chat_id].player2.name) + " " + player2_move_text
    message_text = "Game has started! Players status:\n" + players_text
    context.bot.send_message(chat_id=chat_id, text=message_text)

# Callback function for /help command
def help(update, context):
    chat_id = update.effective_chat.id

    # Update from private chat
    if update.effective_chat.type == "private":
        send_private_chat_error_message(context.bot, chat_id)
        return

    preamble_text = "To start a new game session of scissors paper stone, type /start. " \
                    "Then, players can join the game of scissors paper stone by typing /join. " \
                    "Only a maximum of 2 players are allowed (DUH). " \
                    "Players cannot join a game if there is no running session (i.e. /start not entered yet)"
    start_text = "/start: Start a new game of scissors paper stone"
    join_text = "/join: Join a game of scissors paper stone"
    status_text = "/status: Show current status of the game session (if any)"
    help_text = "/help: Show this menu"
    commands_text = "List of commands:\n" + start_text + "\n" + join_text + "\n" + status_text + "\n" + help_text

    context.bot.send_message(chat_id=chat_id, text=preamble_text + "\n\n" + commands_text)

def start_game(bot, game_session):
    '''
    Starts the game of scissors paper stone. 
    This is where players will be asked to pick a move against the other player.
    (Note: when a move is made, it is not handled here but in the handle_move function)
    '''
    LOGGER.info("Starting a game in " + str(game_session.chat_id))

    # Mark players as being in an active game session: add chat_id to the queue
    if game_session.player1.id not in PLAYER_TO_ACTIVE_CHAT_ID:
        PLAYER_TO_ACTIVE_CHAT_ID[game_session.player1.id] = []
    PLAYER_TO_ACTIVE_CHAT_ID[game_session.player1.id].append(game_session.chat_id)
    if game_session.player2.id not in PLAYER_TO_ACTIVE_CHAT_ID:
        PLAYER_TO_ACTIVE_CHAT_ID[game_session.player2.id] = []
    PLAYER_TO_ACTIVE_CHAT_ID[game_session.player2.id].append(game_session.chat_id)

    # DEBUG
    print("Current active sessions:")
    print(PLAYER_TO_ACTIVE_CHAT_ID)

    # Create keyboard
    scissors_button = KeyboardButton(text=SCISSORS)
    paper_button = KeyboardButton(text=PAPER)
    stone_button = KeyboardButton(text=STONE)
    keyboard = ReplyKeyboardMarkup(keyboard=[[scissors_button, paper_button, stone_button]], one_time_keyboard=True)

    # Prompt reader to pick their move
    bot.send_message(chat_id=game_session.player1.id, text="Pick your move against " + game_session.player2.name, \
                        reply_markup=keyboard)
    bot.send_message(chat_id=game_session.player2.id, text="Pick your move against " + game_session.player1.name, \
                        reply_markup=keyboard)

# Callback function for a move message ("✂", "📃", "🗿")
def handle_move(update, context):
    '''
    Handles a move by a player.
    If a player is in more than one active game session (>1 group chats), the move will be for the
    earliest game session (FIFO queue)
    '''
    user_id = update.effective_user.id
    user_name = update.effective_user.username

    # Return if user not in an active game session.
    if user_id not in PLAYER_TO_ACTIVE_CHAT_ID or len(PLAYER_TO_ACTIVE_CHAT_ID[user_id]) == 0:
        context.bot.send_message(chat_id=user_id, text="Error! You are currently not in any active game session.")
        return

    # If user is in >1 active game session, get the chat_id of the game session this move is for by dequeuing
    # it in the corresponding queue in PLAYER_TO_ACTIVE_CHAT_ID
    chat_id = PLAYER_TO_ACTIVE_CHAT_ID[user_id].pop(0)
    game_session = GAME_SESSIONS[chat_id]

    # Assign the move to the corresponding player
    move = update.message.text
    if user_id == game_session.player1.id:
        game_session.player1.move = move
    else:
        game_session.player2.move = move
    
    LOGGER.info("Received move [" + move + "] from user [" + user_name + "] for the session in chat [" + str(chat_id) + "]")

    context.bot.send_message(chat_id=user_id, text="You have made the move [" + move + "] for the game session in " \
                            + game_session.chat_name + "!")
    
    # DEBUG
    print(game_session)
    print("Current active sessions:")
    print(PLAYER_TO_ACTIVE_CHAT_ID)

    # Both players have made their moves: find the winner
    if game_session.player1.move and game_session.player2.move: 
        winner = find_winner(game_session.player1.move, game_session.player2.move)

        moves_text = game_session.player1.name + " played " + game_session.player1.move + " and " + \
                        game_session.player2.name + " played " + game_session.player2.move + "!"
        restart_game_text = "Try again? Enter /start to start a new game!"

        if winner == 0: # Tie
            context.bot.send_message(chat_id=chat_id, text="It's a tie!\n" + moves_text + "\n\n" + restart_game_text)
        elif winner == 1: # Player 1 wins
            context.bot.send_message(chat_id=chat_id, text=game_session.player1.name + " wins!\n" + \
                                        moves_text + "\n\n" + restart_game_text)
        elif winner == 2: # Player 2 wins
            context.bot.send_message(chat_id=chat_id, text=game_session.player2.name + " wins!\n" + \
                                        moves_text + "\n\n" + restart_game_text)

        # Clear game session
        del GAME_SESSIONS[chat_id]

    # Waiting for the other player
    else:
        if user_id == game_session.player1.id:
            other_player_name = game_session.player2.name
        else:
            other_player_name = game_session.player1.name
        context.bot.send_message(chat_id=chat_id, text=user_name + " has made a move! Waiting for " + other_player_name + "...")

def find_winner(player1_move, player2_move):
    '''
    Returns the winner (1 if player1, 2 if player2, 0 if tie) based on their moves.
    Assumes all moves are one of [SCISSORS, PAPER, STONE] (i.e. no invalid moves).
    '''
    # Tie
    if player1_move == player2_move:
        return 0
    
    # Player 1 wins
    if (player1_move == SCISSORS and player2_move == PAPER) or \
        (player1_move == STONE and player2_move == SCISSORS) or \
        (player1_move == PAPER and player2_move == STONE):
        return 1
    
    # Player 2 wins
    if (player2_move == SCISSORS and player1_move == PAPER) or \
        (player2_move == STONE and player1_move == SCISSORS) or \
        (player2_move == PAPER and player1_move == STONE):
        return 2

def send_private_chat_error_message(bot, chat_id):
    '''
    If any commands are sent on a private chat with the bot, send an error message.
    '''
    message_text = "You cannot start or join a game here. " \
                    "To start a game of scissors paper stone, add me to a group chat and type /start in the group chat. " \
                    "To join a game of scissors paper stone in a group chat, type /join in the group chat where I am in. " \
                    "If you still need help, type /help in the group chat where I am in."
    bot.send_message(chat_id=chat_id, text=message_text)
    
def main():
    updater = Updater(token=TOKEN, use_context=True)
    dispatcher = updater.dispatcher

    # Set up webhook/poll, depending on dev or prod mode
    if MODE == 'dev':
        # Use polling (i.e. getUpdates API method) if in development mode:
        # Periodically connects to Telegram's servers to check for new update
        LOGGER.info("Starting bot in development mode...")
        updater.start_polling()
    elif MODE == 'prod':
        # Use webhooks if in production mode:
        # Whenever a new update for our bot arrives, Telegram sends that update to a specified URL.
        LOGGER.info("Starting bot in production mode...")
        updater.start_webhook(listen='0.0.0.0', port=PORT, url_path=TOKEN)
        updater.bot.set_webhook('https://{}.herokuapp.com/{}'.format(HEROKU_APP_NAME, TOKEN))
        LOGGER.info("Webhook set at https://{}.herokuapp.com/<token>".format(HEROKU_APP_NAME))

    else:
        LOGGER.error("Invalid TELEGRAM_SPS_BOT_MODE value! Should be 'dev' or 'prod'.")
        sys.exit(1)

    # Register callback functions
    start_handler = CommandHandler('start', start)
    dispatcher.add_handler(start_handler)

    join_handler = CommandHandler('join', join)
    dispatcher.add_handler(join_handler)

    status_handler = CommandHandler('status', status)
    dispatcher.add_handler(status_handler)

    help_handler = CommandHandler('help', help)
    dispatcher.add_handler(help_handler)

    move_handler = MessageHandler(Filters.text([SCISSORS, PAPER, STONE]), handle_move)
    dispatcher.add_handler(move_handler)

    # Start the bot
    updater.start_polling()

if __name__ == '__main__':
    main()
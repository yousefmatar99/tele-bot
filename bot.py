import logging
import bot_secrets
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import TicTacToe
import FourInRow
import Trivia
import utils
import emoji
import rps_bot as Rps
import db_connect as db
import random


logging.basicConfig(
    format="[%(levelname)s %(asctime)s %(module)s:%(lineno)d] %(message)s",
    level=logging.INFO,
)

logger = logging.getLogger(__name__)

bot = telebot.TeleBot(bot_secrets.TOKEN)

games = {
    "Tic-Tac-Toe": TicTacToe,
    "4-In-A-Row": FourInRow,
    "Trivia": Trivia,
    "rock-paper-scissors": Rps,
}


def check_register(message: telebot.types.Message):
    user_id = message.from_user.id
    user = db.get_user_info("user_id", user_id)
    if not user:
        db.create_user(
            user_id,
            message.chat.id,
            message.from_user.username,
            random.choice(list(emoji.EMOJI_DATA.keys())),
        )


@bot.message_handler(commands=["start"])
def send_welcome(message: telebot.types.Message):
    logger.info(f"+ Start chat #{message.chat.id} from {message.chat.username}")
    check_register(message)

    user = db.get_user_info("user_id", message.chat.id)
    bot.reply_to(
        message,
        f"🤖 Welcome! 🤖\n"
        f"Your Name is: {user['user_name']}\n"
        f"Your emoji is: {user['emoji']}\n"
        f"use '/rename' or '/reemoji' to change them",
    )

    utils.send_main_menu(message.from_user.id, bot)


@bot.message_handler(commands=["exit"])
def main_screen(message: telebot.types.Message):
    logger.info(f"+ exit chat #{message.chat.id} from {message.chat.username}")
    bot.reply_to(message, "🤖 Hi again 🤖")
    utils.send_main_menu(message.from_user.id, bot)


@bot.callback_query_handler(func=lambda call: call.data == "Play")
def play_callback_query(call):
    utils.edit_selected_msg(call, bot)

    keyboard = InlineKeyboardMarkup(row_width=1)
    game_options = []

    for g in games.keys():
        game_options.append(InlineKeyboardButton(g, callback_data=g))
    keyboard.add(*game_options)

    bot.send_message(call.message.chat.id, "Choose a game:", reply_markup=keyboard)


@bot.callback_query_handler(func=lambda call: call.data == "Help")
def help_callback_query(call):
    utils.edit_selected_msg(call, bot)

    help(call.message)


@bot.callback_query_handler(func=lambda call: call.data == "LeaderBoards")
def scoreboard_callback_query(call: telebot.types.CallbackQuery):
    utils.edit_selected_msg(call, bot)

    scoreboard = "🏆 *Scoreboard* 🏆\n\n"
    for g in games:
        top = db.get_top_scorers(g)
        scoreboard += "*{}*:\n🥇 *{}*\n🥈 *{}*\n🥉 *{}*\n\n".format(g, *top)

    bot.send_message(call.message.chat.id, scoreboard, parse_mode="Markdown")
    utils.send_main_menu(call.message.chat.id, bot)


@bot.callback_query_handler(func=lambda call: call.data == "Features")
def features_callback_query(call: telebot.types.CallbackQuery):
    utils.edit_selected_msg(call, bot)

    msg = ""
    for g in games.values():
        msg += g.about()
        msg += "\n\n"

    bot.send_message(call.message.chat.id, msg, parse_mode="Markdown")
    utils.send_main_menu(call.message.chat.id, bot)


@bot.callback_query_handler(func=lambda call: call.data in games.keys())
def callback_query_for_choosing_game(call: telebot.types.CallbackQuery):
    game_type = call.data
    user_id = call.from_user.id
    chat_id = call.message.chat.id

    if game_type == "Trivia":
        state_in_game = games[game_type].init_state()
        state = db.create_state(user_id, user_id, game_type, state_in_game)
        games[game_type].start(state)
        return

    # check if a queue exists
    queue = db.get_queue_info("game_type", game_type)
    if queue:
        # Retrieve other player's data - no queues for single
        other_user_id = queue["user_id"]
        # Queue exists, delete it and create a new game
        db.delete_queue(other_user_id)
        state_in_game = games[game_type].init_state()
        state = db.create_state(user_id, other_user_id, game_type, state_in_game)
        games[game_type].start(state)
    else:
        # Queue does not exists, create one
        db.create_queue(user_id, chat_id, game_type)
        q_msg = "You have joined a queue, please wait for other players to play.\nyou can type '/exit' to return."
        bot.send_message(chat_id, q_msg, parse_mode="Markdown")


@bot.callback_query_handler(func=lambda call: True)
def callback_query_for_move(call: telebot.types.CallbackQuery):
    user_id = call.from_user.id
    state = db.get_state_info_by_ID(user_id)
    logger.info(f"call: {call.message.chat.id} - state = {state}")
    if state:
        game_type = state["game_type"]
        curr_game = games[game_type]  # current game module
        curr_game.callback_query(call, state)


# TO CHANGE - DONE
@bot.message_handler(commands=["rename"])
def raname(message: telebot.types.Message):
    logger.info(
        f"[#{message.chat.id}.{message.message_id} {message.chat.username!r}] {message.text!r}"
    )
    arr = message.text.split()
    if len(arr) != 2:
        bot.reply_to(
            message, "correct use:\n/rename <new_name>\nthe name cannot contain spaces"
        )
    else:  # correct behavior
        bot.reply_to(message, f"your new user name is: {arr[1]}")
        logger.info(
            f"[#{message.chat.id}.{message.message_id} {message.chat.username!r}] {message.text!r}"
        )
        # print('update DB')
        db.update_user_info(message.chat.id, {"user_name": arr[1]})
    utils.send_main_menu(message.chat.id, bot)


def is_emoji(s: str) -> bool:
    return s in emoji.EMOJI_DATA


# TO CHANGE - DONE
@bot.message_handler(commands=["reemoji"])
def reemoji(message: telebot.types.Message):
    logger.info(
        f"[#{message.chat.id}.{message.message_id} {message.chat.username!r}] {message.text!r}"
    )
    arr = message.text.split()
    if len(arr) != 2 or not is_emoji(arr[1]):
        bot.reply_to(message, "correct use:\n/reemoji <new_emoji>")
    else:  # correct behavior
        bot.reply_to(message, f"your new emoji is: {arr[1]}")
        logger.info(
            f"[#{message.chat.id}.{message.message_id} {message.chat.username!r}] {message.text!r}"
        )
        # print('update DB')
        db.update_user_info(message.chat.id, {"emoji": arr[1]})
    utils.send_main_menu(message.chat.id, bot)


@bot.message_handler(commands=["help", "h"])
def help(message: telebot.types.Message):
    help_str = """
🤖 *Bot Commands Help*:

🎮 *Game Commands*:
- `/start` - Start the bot
- `/exit` - Returns to main menu
- `/help` - Get help

🛠 *Settings*:
- `/rename <new_name>` - Change your username in the game
- `/reemoji <emoji>` - Change your game emoji

    """
    bot.send_message(message.chat.id, help_str, parse_mode="Markdown")
    utils.send_main_menu(message.chat.id, bot)


@bot.message_handler(func=lambda m: True)
def echo_all(message: telebot.types.Message):
    logger.info(
        f"[#{message.chat.id}.{message.message_id} {message.chat.username!r}] {message.text!r}"
    )
    bot.reply_to(message, f"You said: {message.text}")


logger.info("> Starting bot")
bot.infinity_polling()
logger.info("< Goodbye!")

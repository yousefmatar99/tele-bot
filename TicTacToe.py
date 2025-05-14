import logging

import bot_secrets
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import utils
import db_connect as db
import logging

logging.basicConfig(
    format="[%(levelname)s %(asctime)s %(module)s:%(lineno)d] %(message)s",
    level=logging.INFO,
)

logger = logging.getLogger(__name__)

EMPTY = " "
WAIT_MSG = "Wait for your opponent's move"
YOURS_MSG = "Your move!"

logging.basicConfig(
    format="[%(levelname)s %(asctime)s %(module)s:%(lineno)d] %(message)s",
    level=logging.INFO,
)

bot = telebot.TeleBot(bot_secrets.TOKEN)


def get_keyboard(game_state: list[str]) -> telebot.types.InlineKeyboardMarkup:
    keyboard = InlineKeyboardMarkup(row_width=3)

    buttons = []
    for i in range(9):
        buttons.append(InlineKeyboardButton(f"{game_state[i]}", callback_data=f"{i}"))
    keyboard.add(*buttons)

    return keyboard


def init_state():
    return [EMPTY] * 9


def start(state):
    users = state["user_id_arr"]
    turn = state["turn"]
    this_username = db.get_user_info("user_id", users[turn])["user_name"]
    other_username = db.get_user_info("user_id", users[1 - turn])["user_name"]

    msg = [None, None]
    m1 = bot.send_message(
        state["user_id_arr"][not turn],
        f"You are playing against: {this_username}\nGame Started, " + WAIT_MSG,
        reply_markup=get_keyboard(state["state"]),
    )
    m2 = bot.send_message(
        state["user_id_arr"][turn],
        f"You are playing against: {other_username}\nGame Started, " + YOURS_MSG,
        reply_markup=get_keyboard(state["state"]),
    )
    msg[not turn] = m1.id
    msg[turn] = m2.id
    db.update_state_info(users[0], {"msg_id_arr": msg})


def check_status(grid):
    winner: str = ""
    for i in range(3):
        if grid[3 * i] == grid[3 * i + 1] == grid[3 * i + 2] != EMPTY:
            winner = grid[3 * i]
            break
        if grid[i] == grid[i + 3] == grid[i + 6] != EMPTY:
            winner = grid[i]
            break
    if winner == "":
        if grid[0] == grid[4] == grid[8] != EMPTY:
            winner = grid[0][0]
        if grid[2] == grid[4] == grid[6] != EMPTY:
            winner = grid[2]
    return winner


def callback_query(call, state):
    turn = state["turn"]
    this_id, other_id = state["user_id_arr"][turn], state["user_id_arr"][1 - turn]
    this_msg_id, other_msg_id = state["msg_id_arr"][turn], state["msg_id_arr"][1 - turn]
    if call.from_user.id != this_id:
        bot.answer_callback_query(call.id, "It's not your turn")
        return
    # right player
    pos = int(call.data)
    over = False
    tmp_state = state["state"]
    if tmp_state[pos] != EMPTY:
        bot.answer_callback_query(call.id, "Not a legal move")
        return
    else:
        ch = db.getEmoji(this_id)
        tmp_state[pos] = ch

        if (w := check_status(tmp_state)) != "":  # noqa: F841
            bot.edit_message_text(
                "You Won :)", this_id, this_msg_id, InlineKeyboardMarkup()
            )
            bot.edit_message_text(
                "You Lost :(", other_id, other_msg_id, InlineKeyboardMarkup()
            )
            db.inc_score(this_id, 7, state["game_type"])
            over = True
        elif tmp_state.count(EMPTY) == 0:
            bot.edit_message_text(
                "Draw :|", this_id, this_msg_id, InlineKeyboardMarkup()
            )
            bot.edit_message_text(
                "Draw :|", other_id, other_msg_id, InlineKeyboardMarkup()
            )
            db.inc_score(this_id, 3, state["game_type"])
            db.inc_score(other_id, 3, state["game_type"])
            over = True

        if over:
            utils.send_main_menu(call.message.chat.id, bot)
            utils.send_main_menu(other_id, bot)
            return

    db.update_state_info(
        state["user_id_arr"][turn], {"state": tmp_state, "turn": int(1 - turn)}
    )

    bot.edit_message_text(
        WAIT_MSG,
        state["user_id_arr"][turn],
        state["msg_id_arr"][turn],
        reply_markup=get_keyboard(state["state"]),
    )
    bot.edit_message_text(
        YOURS_MSG,
        state["user_id_arr"][not turn],
        state["msg_id_arr"][not turn],
        reply_markup=get_keyboard(state["state"]),
    )

    bot.answer_callback_query(call.id)


def about():
    return (
        "⭕❌ * Tic Tac Toe * ❌⭕\n"
        " - duel game\n"
        "Think fast, line up three, and claim victory! 🏆\n"
        "Are you ready to outsmart your opponent? 🎯🔥"
    )

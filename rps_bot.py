import telebot
import bot_secrets
import logging
from rps_game import rps_game
import utils
import db_connect as db


logging.basicConfig(
    format="[%(levelname)s %(asctime)s %(module)s:%(lineno)d] %(message)s",
    level=logging.INFO,
)

logger = logging.getLogger(__name__)

bot = telebot.TeleBot(bot_secrets.TOKEN)


def init_state():
    return ["", ""]


def start(state):
    users_id = state["user_id_arr"]

    msg = []
    for i in [0, 1]:
        opponent = db.get_user_info("user_id", state["user_id_arr"][not i])["user_name"]
        msg.append(
            (bot.send_message(
                    state["user_id_arr"][i],
                    f"You are playing against: {opponent}\n"
                    f"Game Started, choose your move",
                    reply_markup=get_rps_buttons(),
                ).id
            )
        )

    db.update_state_info(users_id[0], {"msg_id_arr": msg})


def get_rps_buttons() -> telebot.types.InlineKeyboardMarkup:
    markup = telebot.types.InlineKeyboardMarkup(row_width=3)
    markup.add(
        telebot.types.InlineKeyboardButton("🧱", callback_data="🧱"),
        telebot.types.InlineKeyboardButton("📄", callback_data="📄"),
        telebot.types.InlineKeyboardButton("✂️", callback_data="✂️"),
    )
    # bot.send_message(chat_id=user_id, text="Choose your move:", reply_markup=markup)
    return markup


def callback_query(call: telebot.types.CallbackQuery, state):
    user_id = call.message.chat.id
    index = state["user_id_arr"].index(user_id)

    if state["state"][index]:
        bot.answer_callback_query(call.id, "wait for your opponents move.")
        return

    state["state"][index] = call.data
    db.update_state_info(state["user_id_arr"][0], {"state": state["state"]})

    if all(state["state"]):
        winner = rps_game(state["state"])

        if winner == 2:  # tie
            for i in [0, 1]:
                bot.edit_message_text(
                    f"It's a tie\nyou both have chosen {state["state"][0]}",
                    state["user_id_arr"][i],
                    state["msg_id_arr"][i],
                    reply_markup=telebot.types.InlineKeyboardMarkup(),
                )
                db.inc_score(state["user_id_arr"][i], 3, state["game_type"])
                utils.send_main_menu(state["user_id_arr"][i], bot)

        else:
            winner = db.get_user_info("user_id", state["user_id_arr"][index])["user_name"]

            msg = "{} won!\n you chose {}\n your opponent chose{}"

            bot.edit_message_text(
                msg.format(winner, state["state"][index], state["state"][not index]),
                state["user_id_arr"][index],
                state["msg_id_arr"][index],
                reply_markup=telebot.types.InlineKeyboardMarkup(),
            )
            db.inc_score(state["user_id_arr"][index], 7, state["game_type"])
            utils.send_main_menu(state["user_id_arr"][index], bot)

            bot.edit_message_text(
                msg.format(winner, state["state"][not index], state["state"][index]),
                state["user_id_arr"][not index],
                state["msg_id_arr"][not index],
                reply_markup=telebot.types.InlineKeyboardMarkup(),
            )
            utils.send_main_menu(state["user_id_arr"][not index], bot)


def about():
    return (
        "🪨✂️📜 * Rock Paper Scissors * 📜✂️🪨\n"
        " - duel game\n"
        "the ultimate battle of chance! Choose rock (🪨) to crush scissors, "
        "scissors (✂️) to cut paper, or paper (📜) to cover rock. "
        "Think fast, play smart, and outwit your opponent in this timeless showdown! 🎮🔥"
    )


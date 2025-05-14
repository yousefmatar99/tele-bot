import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import urllib.parse
import bot_secrets
import db_connect


def send_main_menu(user_id: int, bot: telebot.TeleBot):
    db_connect.delete_queue(user_id)
    db_connect.delete_state(user_id)

    share_message = f"Check out this awesome game bot!\nLet's play together: {bot_secrets.BOT_USERNAME}"
    encoded_share_message = urllib.parse.quote(share_message)

    keyboard = InlineKeyboardMarkup(row_width=1)
    keyboard.add(InlineKeyboardButton("Play a game", callback_data="Play"))
    keyboard.add(InlineKeyboardButton("Help", callback_data="Help"))
    keyboard.add(InlineKeyboardButton("LeaderBoards", callback_data="LeaderBoards"))
    keyboard.add(InlineKeyboardButton("Features", callback_data="Features"))
    keyboard.add(
        InlineKeyboardButton(
            "Share with Friends", url=f"tg://msg?text={encoded_share_message}"
        )
    )
    bot.send_message(user_id, "Choose an option:", reply_markup=keyboard)


def edit_selected_msg(call: telebot.types.CallbackQuery, bot: telebot.TeleBot):
    bot.edit_message_text(
        f"You selected: *{call.data}*",
        call.message.chat.id,
        call.message.message_id,
        reply_markup=InlineKeyboardMarkup(),
        parse_mode="Markdown",
    )

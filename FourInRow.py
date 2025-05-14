import random
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import bot_secrets
import utils
import logging
import db_connect as db

bot = telebot.TeleBot(bot_secrets.TOKEN)

logger = logging.getLogger(__name__)
logging.basicConfig(
    format="[%(levelname)s %(asctime)s %(module)s:%(lineno)d] %(message)s",
    level=logging.INFO,
)


WAIT_MSG = "Wait for your opponent's move"
YOURS_MSG = "Your move!"
ROWS, COLS = 6, 7
EMPTY = "⚪"


def init_state() -> list[list[str]]:
    return [[EMPTY] * COLS for _ in range(ROWS)]


def format_grid(grid: list[list[str]]) -> str:
    """Convert grid to a string for Telegram messages."""
    grid_str = "\n".join("".join(row) for row in grid)
    column_numbers = "1️⃣2️⃣3️⃣4️⃣5️⃣6️⃣7️⃣\n"
    return f"{grid_str}\n{column_numbers}"


def drop_piece(grid: list[list[str]], column: int, piece: str) -> bool:
    """Drop a piece into the column if possible."""
    for row in reversed(grid):
        if row[column] == EMPTY:
            row[column] = piece
            return True
    return False  # Column is full


def check_winner(grid: list[list[str]], piece: str) -> bool:
    """Check for a win (horizontal, vertical, diagonal)."""
    # Horizontal & Vertical
    for r in range(ROWS):
        for c in range(COLS - 3):
            if all(grid[r][c + i] == piece for i in range(4)):
                return True
    for r in range(ROWS - 3):
        for c in range(COLS):
            if all(grid[r + i][c] == piece for i in range(4)):
                return True
    # Diagonal (↘)
    for r in range(ROWS - 3):
        for c in range(COLS - 3):
            if all(grid[r + i][c + i] == piece for i in range(4)):
                return True
    # Diagonal (↙)
    for r in range(3, ROWS):
        for c in range(COLS - 3):
            if all(grid[r - i][c + i] == piece for i in range(4)):
                return True
    return False


def is_draw(grid: list[list[str]]) -> bool:
    """Check if the grid is full (draw)."""
    return all(cell != EMPTY for row in grid for cell in row)


def create_keyboard() -> InlineKeyboardMarkup:
    """Generate inline keyboard for column selection."""
    keyboard = InlineKeyboardMarkup()
    buttons = [
        InlineKeyboardButton(str(i + 1), callback_data=str(i)) for i in range(COLS)
    ]
    keyboard.add(*buttons)
    return keyboard


def start(state: dict):
    """Start a new 4-in-a-Row game."""
    users = state["user_id_arr"]
    turn = state["turn"]
    this_username = db.get_user_info("user_id", users[turn])["user_name"]
    other_username = db.get_user_info("user_id", users[1 - turn])["user_name"]

    turn = state["turn"]
    msg = [None, None]
    m1 = bot.send_message(
        state["user_id_arr"][not turn],
        f"You are playing against: {this_username}\nGame Started, {WAIT_MSG}\n"
        f"{format_grid(state['state'])}",
        reply_markup=create_keyboard(),
    )
    m2 = bot.send_message(
        state["user_id_arr"][turn],
        f"You are playing against: {other_username}\nGame Started, {YOURS_MSG}\n"
        f"{format_grid(state['state'])}",
        reply_markup=create_keyboard(),
    )
    msg[not turn] = m1.id
    msg[turn] = m2.id

    logger.info(f"starts {__name__} game, between: {state['user_id_arr']}")
    db.update_state_info(users[0], {"msg_id_arr": msg})


def callback_query(call: telebot.types.CallbackQuery, state: dict):
    """Handle player moves."""
    turn = state["turn"]
    if call.from_user.id != state["user_id_arr"][turn]:
        bot.answer_callback_query(call.id, "It's not your turn")
        return

    grid = state["state"]
    column = int(call.data)

    if not drop_piece(grid, column, db.getEmoji(state["user_id_arr"][turn])):
        bot.answer_callback_query(call.id, "Column is full! Choose another.")
        return

    if check_winner(grid, db.getEmoji(state["user_id_arr"][turn])):
        bot.edit_message_text(
            f"{format_grid(state['state'])}\n\n🎉 You Won!",
            state["user_id_arr"][turn],
            state["msg_id_arr"][turn],
            reply_markup=InlineKeyboardMarkup(),
        )
        db.inc_score(state["user_id_arr"][turn], 7, state["game_type"])

        bot.edit_message_text(
            f"{format_grid(state['state'])}\n\nYou Lost!",
            state["user_id_arr"][not turn],
            state["msg_id_arr"][not turn],
            reply_markup=InlineKeyboardMarkup(),
        )

        utils.send_main_menu(state["user_id_arr"][0], bot)
        utils.send_main_menu(state["user_id_arr"][1], bot)
        return

    if is_draw(grid):
        for i in [0, 1]:
            bot.edit_message_text(
                f"{format_grid(state['state'])}\n\nIts a Draw",
                state["user_id_arr"][i],
                state["msg_id_arr"][i],
                reply_markup=InlineKeyboardMarkup(),
            )
            db.inc_score(state["user_id_arr"][i], 3, state["game_type"])
            utils.send_main_menu(state["user_id_arr"][i], bot)
        return

    db.update_state_info(state["user_id_arr"][turn], {"state": grid, "turn": 1 - turn})
    logger.info(f"state after: {db.get_state_info_by_ID(state['user_id_arr'][turn])}")

    # bot.edit_message_text(format_grid(game["grid"]), chat_id, call.message.message_id, reply_markup=create_keyboard())

    bot.edit_message_text(
        f"{WAIT_MSG}\n{format_grid(state['state'])}",
        state["user_id_arr"][turn],
        state["msg_id_arr"][turn],
        reply_markup=create_keyboard(),
    )
    bot.edit_message_text(
        f"{YOURS_MSG}\n{format_grid(state['state'])}",
        state["user_id_arr"][not turn],
        state["msg_id_arr"][not turn],
        reply_markup=create_keyboard(),
    )


def about():
    return (
        "🔴🟡 * 4 in a Row * 🟡🔴\n"
        " - duel game\n"
        "Drop your pieces, connect four, and outplay your opponent! 🏆\n"
        "Think ahead, block their moves, and claim victory! 🎯🔥"
    )

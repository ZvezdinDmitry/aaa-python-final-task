#!/usr/bin/env python

"""
Bot for playing tic tac toe game with multiple CallbackQueryHandlers.
"""

import logging
import os
import random
from copy import deepcopy
from typing import Literal

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
)

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
# set higher logging level for httpx to avoid all GET and POST
# requests being logged
logging.getLogger("httpx").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)

# get token using BotFather
TOKEN = os.getenv("TG_TOKEN")

CONTINUE_GAME, FINISH_GAME = range(2)

FREE_SPACE = "."
CROSS = "X"
ZERO = "O"


DEFAULT_STATE = [[FREE_SPACE for _ in range(3)] for _ in range(3)]


def get_default_state():
    """Helper function to get default state of the game"""
    return deepcopy(DEFAULT_STATE)


def generate_keyboard(
    state: list[list[str]],
) -> list[list[InlineKeyboardButton]]:
    """Generate tic tac toe keyboard 3x3 (telegram buttons)"""
    return [
        [
            InlineKeyboardButton(state[r][c], callback_data=f"{r}{c}")
            for r in range(3)
        ]
        for c in range(3)
    ]


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Send message on `/start`."""
    context.user_data["keyboard_state"] = get_default_state()
    keyboard = generate_keyboard(context.user_data["keyboard_state"])
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "X (your) turn! Please, put X to the free place",
        reply_markup=reply_markup,
    )
    return CONTINUE_GAME


def ai_turn(field: list[list[str]]) -> list[list[str]]:
    """AI turn on random free cell.

    Args:
        field (list[list[str]]): Corrent game field.

    Returns:
        list[list[str]]: Changed game field.
    """

    free_cells = []
    for i, row in enumerate(field):
        for j, cell in enumerate(row):
            if cell == FREE_SPACE:
                free_cells.append((i, j))

    # choose random free cell
    ai_row, ai_col = random.choice(free_cells)
    field[ai_row][ai_col] = ZERO
    return field


def draw(field: list[list[str]]) -> bool:
    """Check if current state in game have no winners.

    Args:
        field (list[list[str]]): Corrent game field.

    Returns:
        bool: Draw or not.
    """

    for row in field:
        for cell in row:
            if cell == FREE_SPACE:
                return False

    return True


def won(field: list[list[str]], symbol: Literal["X", "O"]) -> bool:
    """Check if crosses or zeros have won the game.

    Args:
        field (list[list[str]]): Corrent game field.
        symbol (Literal["X", "O"]): Player or AI symbol

    Returns:
        bool: _description_
    """

    # check rows
    for row in field:
        row_cnt = 0
        for cell in row:
            if cell == symbol:
                row_cnt += 1

        if row_cnt == 3:
            return True

    # check cols
    for j in range(3):
        col_cnt = 0
        for i in range(3):
            if field[i][j] == symbol:
                col_cnt += 1

        if col_cnt == 3:
            return True

    # check 2 diagonals
    for direction in (0, 2):
        diag_cnt = 0
        for i in range(3):
            j = abs(direction - i)
            if field[i][j] == symbol:
                diag_cnt += 1
        if diag_cnt == 3:
            return True

    # no winning combinations
    return False


def check_game_status(
    field: list[list[str]], symbol: Literal["X", "O"]
) -> tuple[bool, str]:
    """Checks game status after player or AI turn,
    and generates message about draw, failure, win or game prociding.

    Args:
        field (list[list[str]]): Corrent game field.
        symbol (Literal[X, O]): Player or AI symbol.

    Returns:
        tuple[bool, str]: Current game status (finish od continue)
        and message.
    """

    if not isinstance(field, list) or not all(
        isinstance(row, list) for row in field
    ):
        raise TypeError("Wrong field type, must be list[list[str]]")
    if len(field) != 3 or len(field[0]) != 3:
        raise ValueError("Wrong field shape, must be 3x3")
    if symbol not in ("X", "O"):
        raise ValueError("Wrong field shape, must be 3x3")

    game_status = CONTINUE_GAME
    if won(field, symbol):
        if symbol == ZERO:
            text = "You failed... You can try again, just type /start"
        else:
            text = "YOU WIN!!! Maybe one more time? Just type /start"
        game_status = FINISH_GAME

    elif draw(field):
        text = "Nobody wins... You can try again, just type /start"
        game_status = FINISH_GAME

    else:
        text = "Nice turn! Lets continue"
        game_status = CONTINUE_GAME

    return game_status, text


async def game(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Main processing of the game"""
    row, col = map(int, list(update.callback_query.data))
    field = context.user_data["keyboard_state"]
    game_status = CONTINUE_GAME
    if field[row][col] == FREE_SPACE:
        field[row][col] = CROSS  # player turn
        # check win or draw
        game_status, text = check_game_status(field, CROSS)
        if game_status == CONTINUE_GAME:
            field = ai_turn(field)
            # check fail or draw
            game_status, text = check_game_status(field, ZERO)
    else:
        text = "Sorry :(, this cell is already occupied. Choose another one."

    field = generate_keyboard(field)
    reply_markup = InlineKeyboardMarkup(field)
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=text,
        reply_markup=reply_markup,
    )
    return game_status


async def end(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Returns `ConversationHandler.END`, which tells the
    ConversationHandler that the conversation is over.
    """
    # reset state to default so you can play again with /start
    context.user_data["keyboard_state"] = get_default_state()
    return ConversationHandler.END


def main() -> None:
    """Run the bot"""
    # Create the Application and pass it your bot's token.
    application = Application.builder().token(TOKEN).build()

    # Setup conversation handler with the states CONTINUE_GAME and FINISH_GAME
    # Use the pattern parameter to pass CallbackQueries with specific
    # data pattern to the corresponding handlers.
    # ^ means "start of line/string"
    # $ means "end of line/string"
    # So ^ABC$ will only allow 'ABC'
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            CONTINUE_GAME: [
                CallbackQueryHandler(game, pattern="^" + f"{r}{c}" + "$")
                for r in range(3)
                for c in range(3)
            ],
            FINISH_GAME: [
                CallbackQueryHandler(end, pattern="^" + f"{r}{c}" + "$")
                for r in range(3)
                for c in range(3)
            ],
        },
        fallbacks=[CommandHandler("start", start)],
    )

    # Add ConversationHandler to application that will be used for
    # handling updates
    application.add_handler(conv_handler)

    # Run the bot until the user presses Ctrl-C
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()

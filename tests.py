from unittest.mock import AsyncMock

import pytest

from main import ai_turn, check_game_status, draw, game, won


@pytest.mark.parametrize(
    "field,symbol,result",
    [
        (
            [["X", "O", "X"], ["O", ".", "X"], [".", "O", "X"]],
            "X",
            True,
        ),  # col
        (
            [["X", "O", "X"], ["O", ".", "X"], [".", "O", "X"]],
            "O",
            False,
        ),  # col
        (
            [["X", "X", "X"], ["O", ".", "X"], [".", "O", "O"]],
            "X",
            True,
        ),  # row
        (
            [["X", "O", "O"], ["O", "X", "X"], [".", "O", "X"]],
            "X",
            True,
        ),  # diag
        (
            [["X", "X", "O"], ["O", "O", "X"], ["O", "X", "X"]],
            "O",
            True,
        ),  # diag
    ],
)
def test_won(field, symbol, result):
    assert won(field, symbol) == result


def test_draw_true():
    field = [["X", "O", "X"], ["O", "X", "X"], ["O", "X", "O"]]
    assert draw(field)


def test_draw_false():
    field = [["X", ".", "X"], ["O", "X", "."], ["O", "X", "O"]]
    assert not draw(field)


def test_ai_turn():
    field = [["X", ".", "X"], ["O", "X", "."], ["O", "X", "O"]]
    mod_fields_gt = [
        [["X", ".", "X"], ["O", "X", "O"], ["O", "X", "O"]],
        [
            ["X", "O", "X"],
            ["O", "X", "."],
            ["O", "X", "O"],
        ],
    ]
    field_mod = ai_turn(field)
    assert field_mod == mod_fields_gt[0] or field_mod == mod_fields_gt[1]


def test_check_game_status_continue():
    field = [["X", ".", "X"], ["O", "X", "."], ["O", "X", "O"]]
    game_status_gt = 0
    text_gt = "Nice turn! Lets continue"
    game_status, text = check_game_status(field, "X")
    assert game_status == game_status_gt
    assert text == text_gt


def test_check_game_status_win():
    field = [["X", "X", "X"], ["O", ".", "."], ["O", "X", "O"]]
    game_status_gt = 1
    text_gt = "YOU WIN!!! Maybe one more time? Just type /start"
    game_status, text = check_game_status(field, "X")
    assert game_status == game_status_gt
    assert text == text_gt


def test_check_game_status_fail():
    field = [["X", ".", "O"], ["O", "O", "X"], ["O", "X", "X"]]
    game_status_gt = 1
    text_gt = "You failed... You can try again, just type /start"
    game_status, text = check_game_status(field, "O")
    assert game_status == game_status_gt
    assert text == text_gt


def test_check_game_status_draw():
    field = [["X", "O", "X"], ["O", "X", "X"], ["O", "X", "O"]]
    game_status_gt = 1
    text_gt = "Nobody wins... You can try again, just type /start"
    game_status, text = check_game_status(field, "X")
    assert game_status == game_status_gt
    assert text == text_gt


def test_check_game_status_value_error():
    with pytest.raises(ValueError):
        field = [
            [".", ".", "."],
            [".", ".", "."],
            [".", ".", "."],
            [".", ".", "."],
        ]
        check_game_status(field, "X")

    with pytest.raises(ValueError):
        field = [
            [".", ".", "."],
            [".", ".", "."],
            [".", ".", "."],
        ]
        check_game_status(field, ".")


def test_check_game_status_type_error():
    with pytest.raises(TypeError):
        field = (
            [".", ".", "."],
            [".", ".", "."],
            [".", ".", "."],
        )
        check_game_status(field, "X")

    with pytest.raises(TypeError):
        field = [
            (".", ".", "."),
            [".", ".", "."],
            [".", ".", "."],
        ]
        check_game_status(field, "X")


# test game function with mocking
@pytest.mark.asyncio
async def test_game_win():
    update = AsyncMock()
    update.callback_query.data = "22"
    update.effective_chat.id = 42
    update.callback_query.answer = AsyncMock()
    context = AsyncMock()
    field = [["X", "O", "O"], ["O", "X", "X"], ["O", "X", "."]]
    context.user_data = {"keyboard_state": field}
    context.bot.send_message = AsyncMock()
    gt_game_status = 1
    game_status = await game(update, context)
    call_kwargs = context.bot.send_message.call_args.kwargs
    assert gt_game_status == game_status
    assert (
        call_kwargs["text"]
        == "YOU WIN!!! Maybe one more time? Just type /start"
    )


@pytest.mark.asyncio
async def test_game_continue():
    update = AsyncMock()
    update.callback_query.data = "12"
    update.effective_chat.id = 42
    update.callback_query.answer = AsyncMock()
    context = AsyncMock()
    field = [["X", ".", "O"], ["O", "X", "."], ["O", "X", "."]]
    context.user_data = {"keyboard_state": field}
    context.bot.send_message = AsyncMock()
    gt_game_status = 0
    game_status = await game(update, context)
    call_kwargs = context.bot.send_message.call_args.kwargs
    assert gt_game_status == game_status
    assert call_kwargs["text"] == "Nice turn! Lets continue"

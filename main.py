import time
import curses
import asyncio
import random

from itertools import cycle
from curses_tools import draw_frame, read_controls, get_frame_size


TIC_TIMEOUT = 0.1
SYMBOLS = ['+', '*', '.', ':']


async def blink(canvas, row, column, symbol, offset_tics):
    while True:
        canvas.addstr(row, column, symbol, curses.A_DIM)
        for _ in range(offset_tics):
            await asyncio.sleep(0)

        canvas.addstr(row, column, symbol)
        for _ in range(3):
            await asyncio.sleep(0)

        canvas.addstr(row, column, symbol, curses.A_BOLD)
        for _ in range(5):
            await asyncio.sleep(0)

        canvas.addstr(row, column, symbol)
        for _ in range(3):
            await asyncio.sleep(0)


async def fire(canvas, start_row, start_column, rows_speed=-0.3, columns_speed=0):
    row, column = start_row, start_column

    canvas.addstr(round(row), round(column), '*')
    await asyncio.sleep(0)

    canvas.addstr(round(row), round(column), 'O')
    await asyncio.sleep(0)
    canvas.addstr(round(row), round(column), ' ')

    row += rows_speed
    column += columns_speed

    symbol = '-' if columns_speed else '|'

    rows, columns = canvas.getmaxyx()
    max_row, max_column = rows - 1, columns - 1

    curses.beep()

    while 0 < row < max_row and 0 < column < max_column:
        canvas.addstr(round(row), round(column), symbol)
        await asyncio.sleep(0)
        canvas.addstr(round(row), round(column), ' ')
        row += rows_speed
        column += columns_speed


async def animate_spaceship(canvas, row, column):
    spaceships = cycle(['rocket_frame_1.txt', 'rocket_frame_2.txt'])
    while True:
        spaceship = next(spaceships)
        with open(f"spaceship/{spaceship}", "r") as file:
            file_contents = file.read()
        draw_frame(canvas, row, column, file_contents)
        canvas.refresh()
        time.sleep(0.2)
        draw_frame(canvas, row, column, file_contents, negative=True)

        rows_dir, columns_dir, _ = read_controls(canvas)

        row += rows_dir * 1
        column += columns_dir * 1

        max_row, max_column = canvas.getmaxyx()

        rows, columns = get_frame_size(file_contents)

        row = min(max(row + rows_dir, 0), max_row - rows)
        column = min(max(column + columns_dir, 0), max_column - columns)


def draw(canvas):
    canvas.border()
    canvas.nodelay(True)
    curses.curs_set(False)
    max_row, max_column = canvas.getmaxyx()
    coroutines = []

    for _ in range(50):
        row = random.randint(1, max_row - 2)
        col = random.randint(1, max_column - 2)
        symbol = random.choice(SYMBOLS)
        coroutines.append(blink(canvas, row, col, symbol, random.randint(1, 20)))

    # coroutines.append(fire(canvas, max_row / 2, max_column / 2))
    coroutines.append(animate_spaceship(canvas, max_row / 2, max_column / 2, spaceship_frames))

    while True:
        for coroutine in coroutines.copy():
            try:
                coroutine.send(None)
                canvas.refresh()
            except StopIteration:
                coroutines.remove(coroutine)
        time.sleep(TIC_TIMEOUT)


if __name__ == '__main__':
    curses.update_lines_cols()
    curses.wrapper(draw)

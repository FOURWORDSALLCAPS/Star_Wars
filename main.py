import time
import curses
import asyncio
import random

from itertools import cycle
from curses_tools import draw_frame, read_controls, get_frame_size


TIC_TIMEOUT = 0.1
SYMBOLS = ['+', '*', '.', ':']


async def blink(canvas, row, column, symbol):
    while True:
        canvas.addstr(row, column, symbol, curses.A_DIM)
        for _ in range(random.randint(1, 20)):
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

        if row < 0:
            row = 0
        elif row + rows > max_row:
            row = max_row - rows

        if column < 0:
            column = 0
        elif column + columns > max_column:
            column = max_column - columns


async def animate_stars(canvas, num_stars=50):
    max_row, max_column = canvas.getmaxyx()
    coroutines = []

    for _ in range(num_stars):
        row = random.randint(1, max_row - 2)
        col = random.randint(1, max_column - 2)
        symbol = random.choice(SYMBOLS)
        coroutines.append(blink(canvas, row, col, symbol))

    # coroutines.append(fire(canvas, max_row / 2, max_column / 2))
    coroutines.append(animate_spaceship(canvas, max_row / 2, max_column / 2))

    while True:
        for coroutine in coroutines.copy():
            try:
                coroutine.send(None)
                canvas.refresh()
            except StopIteration:
                coroutines.remove(coroutine)
        await asyncio.sleep(TIC_TIMEOUT)


def draw(canvas):
    canvas.border()
    canvas.nodelay(True)
    curses.curs_set(False)
    asyncio.run(animate_stars(canvas))


if __name__ == '__main__':
    curses.update_lines_cols()
    curses.wrapper(draw)

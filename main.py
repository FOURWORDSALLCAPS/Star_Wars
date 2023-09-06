import time
import curses
import asyncio
import random

from obstacles import Obstacle, show_obstacles
from physics import update_speed
from itertools import cycle
from curses_tools import draw_frame, read_controls, get_frame_size


TIC_TIMEOUT = 0.1
SYMBOLS = ['+', '*', '.', ':']
COROUTINES = []
OBSTACLES = []
OBSTACLES_IN_LAST_COLLISIONS = []


async def sleep(tics):
    for _ in range(tics):
        await asyncio.sleep(0)


async def blink(canvas, row, column, symbol, offset_tics):
    while True:
        canvas.addstr(row, column, symbol, curses.A_DIM)
        await sleep(offset_tics)

        canvas.addstr(row, column, symbol)
        await sleep(3)

        canvas.addstr(row, column, symbol, curses.A_BOLD)
        await sleep(5)

        canvas.addstr(row, column, symbol)
        await sleep(3)


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

        for obstacle in OBSTACLES.copy():
            if obstacle.has_collision(round(row), round(column)):
                OBSTACLES.remove(obstacle)
                OBSTACLES_IN_LAST_COLLISIONS.append(obstacle)
                canvas.addstr(round(row), round(column), ' ')
                return

        await asyncio.sleep(0)
        canvas.addstr(round(row), round(column), ' ')
        row += rows_speed
        column += columns_speed

    canvas.addstr(round(row), round(column), ' ')


async def animate_spaceship(canvas, row, column, spaceship_frames):
    spaceships = cycle(spaceship_frames)
    row_speed = column_speed = 0
    while True:
        spaceship = next(spaceships)
        draw_frame(canvas, row, column, spaceship)
        await asyncio.sleep(0)
        draw_frame(canvas, row, column, spaceship, negative=True)
        rows_dir, columns_dir, space_pressed = read_controls(canvas)
        if space_pressed:
            COROUTINES.append(fire(canvas, row, column + 2))
        row_speed, column_speed = update_speed(row_speed, column_speed, rows_dir, columns_dir)

        max_row, max_column = canvas.getmaxyx()

        rows, columns = get_frame_size(spaceship)

        row += row_speed
        column += column_speed

        row = min(max(row + rows_dir, 0), max_row - rows)
        column = min(max(column + columns_dir, 0), max_column - columns)


async def fly_garbage(canvas, column, garbage_frame, speed=0.5):
    rows_number, columns_number = canvas.getmaxyx()

    column = max(column, 0)
    column = min(column, columns_number - 1)

    row = 0

    rows, columns = get_frame_size(garbage_frame)
    while row < rows_number:
        new_obstacle = Obstacle(row, column, rows, columns)
        OBSTACLES.append(new_obstacle)

        draw_frame(canvas, round(row), round(column), garbage_frame)
        await asyncio.sleep(0)
        draw_frame(canvas, round(row), round(column), garbage_frame, negative=True)
        row += speed

        for garbage in OBSTACLES_IN_LAST_COLLISIONS:
            if new_obstacle.has_collision(garbage.row, garbage.column):
                OBSTACLES_IN_LAST_COLLISIONS.remove(garbage)
                canvas.addstr(round(new_obstacle.row), round(new_obstacle.column), ' ')
                return

        if new_obstacle in OBSTACLES:
            OBSTACLES.remove(new_obstacle)


async def fill_orbit_with_garbage(canvas, garbage_frames):
    max_row, max_column = canvas.getmaxyx()
    distance_from_borders_min = 5
    distance_from_borders_max = 15

    while True:
        garbage_frame = random.choice(garbage_frames)

        col = random.randint(distance_from_borders_min, max_column - distance_from_borders_max)
        COROUTINES.append(fly_garbage(canvas, col, garbage_frame))

        await sleep(12)

        col = random.randint(distance_from_borders_min, max_column - distance_from_borders_max)
        COROUTINES.append(fly_garbage(canvas, col, garbage_frame))
        await sleep(12)


def draw(canvas):
    canvas.border()
    canvas.nodelay(True)
    curses.curs_set(False)
    max_row, max_column = canvas.getmaxyx()
    distance_from_borders_min = 1
    distance_from_borders_max = 2
    spaceship_frames = []
    garbage_frames = []
    for spaceship in ['rocket_frame_1.txt', 'rocket_frame_1.txt', 'rocket_frame_2.txt', 'rocket_frame_2.txt']:
        with open(f"spaceship/{spaceship}", "r") as spaceship_file:
            spaceship_frames.append(spaceship_file.read())
    for garbage in ['trash_large.txt', 'trash_small.txt', 'trash_xl.txt']:
        with open(f"garbage/{garbage}", "r") as garbage_file:
            garbage_frames.append(garbage_file.read())
    for _ in range(80):
        row = random.randint(distance_from_borders_min, max_row - distance_from_borders_max)
        col = random.randint(distance_from_borders_min, max_column - distance_from_borders_max)
        symbol = random.choice(SYMBOLS)
        COROUTINES.append(blink(canvas, row, col, symbol, random.randint(1, 20)))
    COROUTINES.append(animate_spaceship(canvas, max_row / 2, max_column / 2, spaceship_frames))
    COROUTINES.append(fill_orbit_with_garbage(canvas, garbage_frames))
    COROUTINES.append(show_obstacles(canvas, OBSTACLES))
    while True:
        for coroutine in COROUTINES.copy():
            try:
                coroutine.send(None)
            except StopIteration:
                COROUTINES.remove(coroutine)
        canvas.refresh()
        time.sleep(TIC_TIMEOUT)


if __name__ == '__main__':
    curses.update_lines_cols()
    curses.wrapper(draw)

import curses
import time
import random

# Einstellungen
PADDLE_HEIGHT = 4
BALL_DELAY = 0.05


def main(stdscr):
    curses.curs_set(0)
    stdscr.nodelay(True)
    stdscr.timeout(30)

    sh, sw = stdscr.getmaxyx()
    paddle1_x = 2
    paddle2_x = sw - 3

    paddle1_y = sh // 2 - PADDLE_HEIGHT // 2
    paddle2_y = sh // 2 - PADDLE_HEIGHT // 2

    ball_y = sh // 2
    ball_x = sw // 2
    ball_dir_y = random.choice([-1, 1])
    ball_dir_x = random.choice([-1, 1])

    score1 = 0
    score2 = 0

    while True:
        stdscr.clear()

        # Paddles zeichnen
        for i in range(PADDLE_HEIGHT):
            stdscr.addch(paddle1_y + i, paddle1_x, '|')
            stdscr.addch(paddle2_y + i, paddle2_x, '|')

        # Ball zeichnen
        stdscr.addch(ball_y, ball_x, 'O')

        # Punkte anzeigen
        stdscr.addstr(1, sw//2 - 5, f'{score1} : {score2}')

        stdscr.refresh()

        key = stdscr.getch()

        # Spielersteuerung
        if key == ord('w') and paddle1_y > 1:
            paddle1_y -= 1
        elif key == ord('s') and paddle1_y < sh - PADDLE_HEIGHT - 1:
            paddle1_y += 1
        elif key == curses.KEY_UP and paddle2_y > 1:
            paddle2_y -= 1
        elif key == curses.KEY_DOWN and paddle2_y < sh - PADDLE_HEIGHT - 1:
            paddle2_y += 1

        # Ballbewegung
        ball_y += ball_dir_y
        ball_x += ball_dir_x

        # Kollision mit Wänden
        if ball_y <= 0 or ball_y >= sh - 1:
            ball_dir_y *= -1

        # Kollision mit Paddle 1
        if ball_x == paddle1_x + 1 and paddle1_y <= ball_y < paddle1_y + PADDLE_HEIGHT:
            ball_dir_x *= -1
        # Kollision mit Paddle 2
        elif ball_x == paddle2_x - 1 and paddle2_y <= ball_y < paddle2_y + PADDLE_HEIGHT:
            ball_dir_x *= -1

        # Punkte
        if ball_x <= 0:
            score2 += 1
            ball_x, ball_y = sw // 2, sh // 2
            ball_dir_x = 1
        elif ball_x >= sw - 1:
            score1 += 1
            ball_x, ball_y = sw // 2, sh // 2
            ball_dir_x = -1

        time.sleep(BALL_DELAY)


if __name__ == "__main__":
    curses.wrapper(main)

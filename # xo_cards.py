import pygame
import random
import sys

pygame.init()

WIDTH, HEIGHT = 600, 750
WIN = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Cyberpunk Card XO - Smart AI")

FONT = pygame.font.SysFont("consolas", 26)
BIG = pygame.font.SysFont("consolas", 40, bold=True)

CYBER_BLUE = (0, 255, 255)
CYBER_PINK = (255, 60, 180)
BG = (10, 10, 20)
GRID_COLOR = (60, 220, 200)

# کارت‌های قابل انتخاب برای بازیکن X
CARD_TYPES_X = [
    {"name": "X", "cost": 1},
    {"name": "FLIP", "cost": 2},
    {"name": "REMOVE", "cost": 2},
    {"name": "SWAP", "cost": 3},
]

# کارت‌های قابل انتخاب برای بازیکن O
CARD_TYPES_O = [
    {"name": "O", "cost": 1},
    {"name": "FLIP", "cost": 2},
    {"name": "REMOVE", "cost": 2},
    {"name": "SWAP", "cost": 3},
]

# کارت رایگان
FREE_X = {"name": "X", "cost": 0}
FREE_O = {"name": "O", "cost": 0}

CARD_Y = 600
CARD_W, CARD_H = 120, 120

board = [["" for _ in range(3)] for _ in range(3)]

player_turn = "X"
mana = 3
hand = []
selected_card = None
card_positions = {}

highlight_cell = None
highlight_alpha = 0
highlight_fade_in = True

game_over = False
winner_text = ""

swap_first_cell = None


def draw_text(text, x, y, color=(255, 255, 255), font=FONT):
    render = font.render(text, True, color)
    WIN.blit(render, (x, y))


def give_cards():
    global hand

    if player_turn == "X":
        base_cards = CARD_TYPES_X
    else:
        base_cards = CARD_TYPES_O

    hand = [random.choice(base_cards) for _ in range(3)]
    hand.append(FREE_X if player_turn == "X" else FREE_O)

    for i in range(len(hand)):
        card_positions[i] = -CARD_H


def slide_in_cards():
    for i in card_positions:
        if card_positions[i] < CARD_Y:
            card_positions[i] += 20
            if card_positions[i] > CARD_Y:
                card_positions[i] = CARD_Y


def draw_cards():
    for idx, card in enumerate(hand):
        x = 30 + idx * (CARD_W + 10)
        y = card_positions.get(idx, CARD_Y)

        pygame.draw.rect(WIN, (30, 30, 50), (x, y, CARD_W, CARD_H))
        pygame.draw.rect(WIN, CYBER_BLUE, (x, y, CARD_W, CARD_H), 3)

        if selected_card == idx:
            pygame.draw.rect(WIN, CYBER_PINK, (x - 4, y - 4, CARD_W + 8, CARD_H + 8), 4)

        draw_text(card["name"], x + 15, y + 15, CYBER_BLUE)
        draw_text(f"Cost: {card['cost']}", x + 15, y + 70, CYBER_PINK)


def draw_board():
    global highlight_alpha, highlight_fade_in

    cell_size = 180
    offset = 30

    if highlight_cell:
        r, c = highlight_cell
        x = offset + r * cell_size
        y = offset + c * cell_size

        glow_surface = pygame.Surface((cell_size, cell_size), pygame.SRCALPHA)
        pygame.draw.rect(glow_surface, (0, 255, 255, highlight_alpha), (0, 0, cell_size, cell_size))
        WIN.blit(glow_surface, (x, y))

        if highlight_fade_in:
            highlight_alpha += 8
            if highlight_alpha >= 120:
                highlight_fade_in = False
        else:
            highlight_alpha -= 8
            if highlight_alpha <= 0:
                highlight_fade_in = True

    for i in range(1, 3):
        pygame.draw.line(WIN, GRID_COLOR, (30, 30 + cell_size * i), (570, 30 + cell_size * i), 3)
        pygame.draw.line(WIN, GRID_COLOR, (30 + cell_size * i, 30), (30 + cell_size * i, 570), 3)

    for r in range(3):
        for c in range(3):
            mark = board[r][c]
            if mark != "":
                draw_text(mark, 90 + r * cell_size, 90 + c * cell_size, CYBER_PINK, BIG)

    if selected_card is not None and hand[selected_card]["name"] == "SWAP" and swap_first_cell:
        r, c = swap_first_cell
        x = 30 + r * cell_size
        y = 30 + c * cell_size
        pygame.draw.rect(WIN, CYBER_PINK, (x, y, cell_size, cell_size), 4)


def check_win():
    lines = []

    for i in range(3):
        lines.append(board[i])
        lines.append([board[0][i], board[1][i], board[2][i]])

    lines.append([board[0][0], board[1][1], board[2][2]])
    lines.append([board[2][0], board[1][1], board[0][2]])

    for line in lines:
        if line == ["X", "X", "X"]:
            return "X"
        if line == ["O", "O", "O"]:
            return "O"
    return None


def play_card(card, pos):
    global highlight_cell, swap_first_cell

    r, c = pos
    name = card["name"]

    if name in ["X", "O"]:
        if board[r][c] != "":
            return False
        board[r][c] = name
        highlight_cell = (r, c)
        return True

    if name == "FLIP":
        if board[r][c] == "":
            return False
        board[r][c] = "O" if board[r][c] == "X" else "X"
        highlight_cell = (r, c)
        return True

    if name == "REMOVE":
        if board[r][c] == "":
            return False
        board[r][c] = ""
        highlight_cell = (r, c)
        return True

    if name == "SWAP":
        if not swap_first_cell:
            if board[r][c] == "":
                return False
            swap_first_cell = (r, c)
            return None
        else:
            r1, c1 = swap_first_cell
            board[r1][c1], board[r][c] = board[r][c], board[r1][c1]
            highlight_cell = (r, c)
            swap_first_cell = None
            return True

    return False


def ai_make_move():
    global player_turn, mana, hand, selected_card, highlight_cell, swap_first_cell

    pygame.time.delay(400)

    # AI tries to win
    for r in range(3):
        for c in range(3):
            if board[r][c] == "":
                board[r][c] = "O"
                if check_win() == "O":
                    highlight_cell = (r, c)
                    player_turn = "X"
                    mana = 3
                    give_cards()
                    return
                board[r][c] = ""

    # AI tries to block X
    for r in range(3):
        for c in range(3):
            if board[r][c] == "":
                board[r][c] = "X"
                if check_win() == "X":
                    board[r][c] = "O"
                    highlight_cell = (r, c)
                    player_turn = "X"
                    mana = 3
                    give_cards()
                    return
                board[r][c] = ""

    # Else random move
    empty = [(r, c) for r in range(3) for c in range(3) if board[r][c] == ""]
    if empty:
        r, c = random.choice(empty)
        board[r][c] = "O"
        highlight_cell = (r, c)

    player_turn = "X"
    mana = 3
    give_cards()
    selected_card = None
    swap_first_cell = None


def can_play_any_card():
    for card in hand:
        if card["cost"] <= mana:
            name = card["name"]
            if name in ["X", "O"]:
                for r in range(3):
                    for c in range(3):
                        if board[r][c] == "":
                            return True
            elif name == "FLIP":
                for r in range(3):
                    for c in range(3):
                        if board[r][c] != "":
                            return True
            elif name == "REMOVE":
                for r in range(3):
                    for c in range(3):
                        if board[r][c] != "":
                            return True
            elif name == "SWAP":
                occupied = [(r, c) for r in range(3) for c in range(3) if board[r][c] != ""]
                if len(occupied) >= 2:
                    return True
    return False


def reset_game():
    global board, mana, player_turn, hand, selected_card, game_over, winner_text
    global highlight_cell, highlight_alpha, highlight_fade_in, swap_first_cell

    board = [["" for _ in range(3)] for _ in range(3)]
    mana = 3
    player_turn = "X"
    give_cards()
    selected_card = None
    game_over = False
    winner_text = ""
    highlight_cell = None
    highlight_alpha = 0
    highlight_fade_in = True
    swap_first_cell = None


give_cards()
clock = pygame.time.Clock()
running = True

while running:
    clock.tick(60)
    WIN.fill(BG)

    slide_in_cards()
    draw_text(f"Turn: {player_turn}", 20, 5, CYBER_BLUE)
    draw_text(f"Mana: {mana}", 460, 5, CYBER_PINK)

    draw_board()
    draw_cards()

    if game_over:
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        WIN.blit(overlay, (0, 0))
        draw_text(winner_text, 150, 320, CYBER_PINK, BIG)
        draw_text("Press R to Restart", 180, 380, CYBER_BLUE)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        if game_over:
            if event.type == pygame.KEYDOWN and event.key == pygame.K_r:
                reset_game()
            continue

        if event.type == pygame.MOUSEBUTTONDOWN:
            mx, my = pygame.mouse.get_pos()

            clicked_card_idx = None
            for i in range(len(hand)):
                x = 30 + i * (CARD_W + 10)
                y = card_positions.get(i, CARD_Y)
                if x <= mx <= x + CARD_W and y <= my <= y + CARD_H:
                    clicked_card_idx = i
                    break

            if clicked_card_idx is not None:
                selected_card = clicked_card_idx
                swap_first_cell = None
                continue

            if selected_card is not None and 30 <= mx <= 570 and 30 <= my <= 570:
                r = (mx - 30) // 180
                c = (my - 30) // 180
                card = hand[selected_card]

                if mana < card["cost"]:
                    continue

                res = play_card(card, (r, c))

                if res is False:
                    continue
                elif res is None:
                    continue

                mana -= card["cost"]
                hand.pop(selected_card)
                selected_card = None
                swap_first_cell = None

                winner = check_win()
                if winner:
                    game_over = True
                    winner_text = "🎉 You Win!" if winner == "X" else "❌ You Lose!"
                else:
                    if not can_play_any_card():
                        hand.append(FREE_X if player_turn == "X" else FREE_O)
                        card_positions[len(hand) - 1] = -CARD_H

                    player_turn = "O"
                    mana = 3
                    give_cards()
                    selected_card = None
                    swap_first_cell = None

    if player_turn == "O" and not game_over:
        ai_make_move()
        winner = check_win()
        if winner:
            game_over = True
            winner_text = "🎉 You Win!" if winner == "X" else "❌ You Lose!"

    pygame.display.update()

pygame.quit()
sys.exit()

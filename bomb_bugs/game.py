import pygame

from .config import ENEMY_COLOR, ENEMY_MAX_HP, ENEMY_SIZE, HEIGHT, SQUARE_COLOR, SQUARE_SIZE, WIDTH
from .gameplay import (
    handle_input_event,
    handle_respawns,
    resolve_combat,
    tick_timers,
    update_enemy,
    update_particles,
    update_player,
)
from .models import Actor, EnemyAI, PlayerState
from .rendering import draw_pause_overlay, render_frame
from .ui import create_pixel_font
from .world import make_platforms


def run_game() -> None:
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Bomb Bugs - Movement Prototype")
    clock = pygame.time.Clock()
    font = pygame.font.SysFont(None, 32)
    floating_text_font = create_pixel_font(30)
    pause_font = create_pixel_font(64)

    platforms = make_platforms()

    player_spawn = (int((WIDTH - SQUARE_SIZE) / 2), int(platforms[0].top - SQUARE_SIZE))
    enemy_spawn = (680, int(platforms[0].top - ENEMY_SIZE))

    player = Actor(
        rect=pygame.Rect(player_spawn[0], player_spawn[1], SQUARE_SIZE, SQUARE_SIZE),
        color=SQUARE_COLOR,
        facing_dir=1,
    )
    enemy = Actor(
        rect=pygame.Rect(enemy_spawn[0], enemy_spawn[1], ENEMY_SIZE, ENEMY_SIZE),
        color=ENEMY_COLOR,
        hp=ENEMY_MAX_HP,
        max_hp=ENEMY_MAX_HP,
        facing_dir=-1,
    )

    player_state = PlayerState()
    enemy_ai = EnemyAI(
        patrol_min=float(enemy_spawn[0] - 180),
        patrol_max=float(enemy_spawn[0] + 180),
        patrol_dir=-1,
    )

    running = True
    paused = False
    while running:
        dt = clock.tick(60) / 1000.0

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_p:
                paused = not paused
            else:
                if not paused:
                    handle_input_event(event, player, enemy, player_state, platforms)

        if paused:
            render_frame(screen, font, floating_text_font, platforms, player, enemy, player_state, present=False)
            draw_pause_overlay(screen, pause_font)
            pygame.display.flip()
            continue

        tick_timers(player, enemy, player_state, dt)
        update_particles(player, enemy, player_state, dt)
        handle_respawns(player, enemy, player_state, enemy_ai, player_spawn, enemy_spawn, dt)

        keys = pygame.key.get_pressed()
        update_player(player, player_state, keys, platforms, dt)
        update_enemy(enemy, enemy_ai, player, platforms, dt)
        resolve_combat(player, enemy, player_state)

        render_frame(screen, font, floating_text_font, platforms, player, enemy, player_state)

    pygame.quit()

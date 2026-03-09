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
from .rendering import draw_main_menu, draw_pause_overlay, render_frame
from .ui import create_pixel_font
from .world import make_platforms


def _reset_combat_state(
    player: Actor,
    enemy: Actor,
    player_spawn: tuple[int, int],
    enemy_spawn: tuple[int, int],
) -> tuple[PlayerState, EnemyAI]:
    player.rect.topleft = player_spawn
    player.hp = player.max_hp
    player.alive = True
    player.respawn_timer = 0.0
    player.slash_time_left = 0.0
    player.slash_cooldown_left = 0.0
    player.facing_dir = 1
    player.death_particles.clear()
    player.respawn_particles.clear()

    enemy.rect.topleft = enemy_spawn
    enemy.hp = enemy.max_hp
    enemy.alive = True
    enemy.respawn_timer = 0.0
    enemy.slash_time_left = 0.0
    enemy.slash_cooldown_left = 0.0
    enemy.facing_dir = -1
    enemy.death_particles.clear()
    enemy.respawn_particles.clear()

    player_state = PlayerState()
    enemy_ai = EnemyAI(
        patrol_min=float(enemy_spawn[0] - 180),
        patrol_max=float(enemy_spawn[0] + 180),
        patrol_dir=-1,
    )
    return player_state, enemy_ai


def run_game() -> None:
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Bomb Bugs - Movement Prototype")
    clock = pygame.time.Clock()
    font = pygame.font.SysFont(None, 32)
    floating_text_font = create_pixel_font(30)
    pause_font = create_pixel_font(64)
    menu_title_font = create_pixel_font(76)
    menu_option_font = create_pixel_font(34)

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

    player_state, enemy_ai = _reset_combat_state(player, enemy, player_spawn, enemy_spawn)

    running = True
    paused = False
    in_menu = True
    while running:
        dt = clock.tick(60) / 1000.0
        mouse_pos = pygame.mouse.get_pos()

        play_button_rect = pygame.Rect(0, 0, 0, 0)
        leave_button_rect = pygame.Rect(0, 0, 0, 0)
        if in_menu:
            probe_label = menu_option_font.render("Play", False, (255, 255, 255))
            play_button_rect = probe_label.get_rect(center=(WIDTH // 2, 300)).inflate(44, 26)
        if paused and not in_menu:
            leave_probe_label = menu_option_font.render("Leave", False, (255, 255, 255))
            leave_button_rect = leave_probe_label.get_rect(center=(WIDTH // 2, 210)).inflate(44, 26)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif in_menu and event.type == pygame.KEYDOWN and event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                in_menu = False
                paused = False
                player_state, enemy_ai = _reset_combat_state(player, enemy, player_spawn, enemy_spawn)
            elif in_menu and event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if play_button_rect.collidepoint(event.pos):
                    in_menu = False
                    paused = False
                    player_state, enemy_ai = _reset_combat_state(player, enemy, player_spawn, enemy_spawn)
            elif not in_menu and paused and event.type == pygame.KEYDOWN and event.key == pygame.K_l:
                in_menu = True
                paused = False
            elif not in_menu and paused and event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if leave_button_rect.collidepoint(event.pos):
                    in_menu = True
                    paused = False
            elif not in_menu and event.type == pygame.KEYDOWN and event.key == pygame.K_p:
                paused = not paused
            else:
                if not in_menu and not paused:
                    handle_input_event(event, player, enemy, player_state, platforms)

        if in_menu:
            draw_main_menu(
                screen,
                menu_title_font,
                menu_option_font,
                play_button_rect.collidepoint(mouse_pos),
            )
            continue

        if paused:
            render_frame(screen, font, floating_text_font, platforms, player, enemy, player_state, present=False)
            draw_pause_overlay(
                screen,
                pause_font,
                menu_option_font,
                leave_button_rect.collidepoint(mouse_pos),
            )
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

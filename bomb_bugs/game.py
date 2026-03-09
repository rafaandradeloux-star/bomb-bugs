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
from .rendering import draw_character_select, draw_main_menu, draw_pause_overlay, render_frame
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
    selected_character = "mantis"
    character_colors = {
        "mantis": SQUARE_COLOR,
        "spider": (180, 142, 97),
        "rhino_beetle": (34, 60, 126),
    }
    character_slash_damage = {
        "mantis": 2,
        "spider": 1,
        "rhino_beetle": 1,
    }
    character_move_speed = {
        "mantis": 420.0,
        "spider": 360.0,
        "rhino_beetle": 300.0,
    }
    character_dash_duration = {
        "mantis": 0.22,
        "spider": 0.18,
        "rhino_beetle": 0.14,
    }
    character_bomb_damage = {
        "mantis": 3,
        "spider": 4,
        "rhino_beetle": 5,
    }
    character_ground_pound_damage = {
        "mantis": 3,
        "spider": 4,
        "rhino_beetle": 5,
    }
    character_special_stun_duration = {
        "mantis": 0.0,
        "spider": 1.5,
        "rhino_beetle": 0.0,
    }
    character_special_hits_required = {
        "mantis": 0.0,
        "spider": 6.5,
        "rhino_beetle": 0.0,
    }
    character_max_hp = {
        "mantis": 10,
        "spider": 10,
        "rhino_beetle": 15,
    }
    player.max_hp = character_max_hp[selected_character]
    player.hp = player.max_hp
    player.color = character_colors[selected_character]
    player.slash_damage = character_slash_damage[selected_character]
    player.move_speed = character_move_speed[selected_character]
    player.dash_duration = character_dash_duration[selected_character]
    player.bomb_damage = character_bomb_damage[selected_character]
    player.ground_pound_damage = character_ground_pound_damage[selected_character]
    player.bomb_charge_hits = player.bomb_hits_required
    player.ground_pound_charge_hits = player.ground_pound_hits_required
    player.special_stun_duration = character_special_stun_duration[selected_character]
    player.special_hits_required = character_special_hits_required[selected_character]
    player.special_charge_hits = player.special_hits_required

    running = True
    paused = False
    in_menu = True
    in_character_select = False
    while running:
        dt = clock.tick(60) / 1000.0
        mouse_pos = pygame.mouse.get_pos()

        play_button_rect = pygame.Rect(0, 0, 0, 0)
        character_select_button_rect = pygame.Rect(0, 0, 0, 0)
        character_select_back_rect = pygame.Rect(0, 0, 0, 0)
        mantis_card_rect = pygame.Rect(0, 0, 0, 0)
        spider_card_rect = pygame.Rect(0, 0, 0, 0)
        rhino_card_rect = pygame.Rect(0, 0, 0, 0)
        leave_button_rect = pygame.Rect(0, 0, 0, 0)
        if in_menu:
            probe_label = menu_option_font.render("Play", False, (255, 255, 255))
            play_button_rect = probe_label.get_rect(center=(WIDTH // 2, 300)).inflate(44, 26)
            character_select_probe_label = menu_option_font.render("Character select", False, (255, 255, 255))
            character_select_button_rect = character_select_probe_label.get_rect(center=(WIDTH // 2, 360)).inflate(44, 26)
        if in_character_select:
            back_probe_label = menu_option_font.render("Back", False, (255, 255, 255))
            character_select_back_rect = back_probe_label.get_rect(center=(WIDTH // 2, 470)).inflate(44, 26)
            mantis_card_rect = pygame.Rect(0, 0, 220, 250)
            mantis_card_rect.center = (WIDTH // 2 - 250, 255)
            spider_card_rect = pygame.Rect(0, 0, 220, 250)
            spider_card_rect.center = (WIDTH // 2, 255)
            rhino_card_rect = pygame.Rect(0, 0, 220, 250)
            rhino_card_rect.center = (WIDTH // 2 + 250, 255)
        if paused and not in_menu:
            leave_probe_label = menu_option_font.render("Leave", False, (255, 255, 255))
            leave_button_rect = leave_probe_label.get_rect(center=(WIDTH // 2, 210)).inflate(44, 26)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif in_menu and event.type == pygame.KEYDOWN and event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                in_menu = False
                in_character_select = False
                paused = False
                player_state, enemy_ai = _reset_combat_state(player, enemy, player_spawn, enemy_spawn)
            elif in_menu and event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if play_button_rect.collidepoint(event.pos):
                    in_menu = False
                    in_character_select = False
                    paused = False
                    player_state, enemy_ai = _reset_combat_state(player, enemy, player_spawn, enemy_spawn)
                elif character_select_button_rect.collidepoint(event.pos):
                    in_menu = False
                    in_character_select = True
                    paused = False
            elif in_character_select and event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                in_character_select = False
                in_menu = True
                paused = False
            elif in_character_select and event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if mantis_card_rect.collidepoint(event.pos):
                    selected_character = "mantis"
                    player.max_hp = character_max_hp[selected_character]
                    player.hp = min(player.hp, player.max_hp)
                    player.color = character_colors[selected_character]
                    player.slash_damage = character_slash_damage[selected_character]
                    player.move_speed = character_move_speed[selected_character]
                    player.dash_duration = character_dash_duration[selected_character]
                    player.bomb_damage = character_bomb_damage[selected_character]
                    player.ground_pound_damage = character_ground_pound_damage[selected_character]
                    player.bomb_charge_hits = player.bomb_hits_required
                    player.ground_pound_charge_hits = player.ground_pound_hits_required
                    player.special_stun_duration = character_special_stun_duration[selected_character]
                    player.special_hits_required = character_special_hits_required[selected_character]
                    player.special_charge_hits = player.special_hits_required
                elif spider_card_rect.collidepoint(event.pos):
                    selected_character = "spider"
                    player.max_hp = character_max_hp[selected_character]
                    player.hp = min(player.hp, player.max_hp)
                    player.color = character_colors[selected_character]
                    player.slash_damage = character_slash_damage[selected_character]
                    player.move_speed = character_move_speed[selected_character]
                    player.dash_duration = character_dash_duration[selected_character]
                    player.bomb_damage = character_bomb_damage[selected_character]
                    player.ground_pound_damage = character_ground_pound_damage[selected_character]
                    player.bomb_charge_hits = player.bomb_hits_required
                    player.ground_pound_charge_hits = player.ground_pound_hits_required
                    player.special_stun_duration = character_special_stun_duration[selected_character]
                    player.special_hits_required = character_special_hits_required[selected_character]
                    player.special_charge_hits = player.special_hits_required
                elif rhino_card_rect.collidepoint(event.pos):
                    selected_character = "rhino_beetle"
                    player.max_hp = character_max_hp[selected_character]
                    player.hp = min(player.hp, player.max_hp)
                    player.color = character_colors[selected_character]
                    player.slash_damage = character_slash_damage[selected_character]
                    player.move_speed = character_move_speed[selected_character]
                    player.dash_duration = character_dash_duration[selected_character]
                    player.bomb_damage = character_bomb_damage[selected_character]
                    player.ground_pound_damage = character_ground_pound_damage[selected_character]
                    player.bomb_charge_hits = player.bomb_hits_required
                    player.ground_pound_charge_hits = player.ground_pound_hits_required
                    player.special_stun_duration = character_special_stun_duration[selected_character]
                    player.special_hits_required = character_special_hits_required[selected_character]
                    player.special_charge_hits = player.special_hits_required
                elif character_select_back_rect.collidepoint(event.pos):
                    in_character_select = False
                    in_menu = True
                    paused = False
            elif not in_menu and paused and event.type == pygame.KEYDOWN and event.key == pygame.K_l:
                in_menu = True
                in_character_select = False
                paused = False
            elif not in_menu and paused and event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if leave_button_rect.collidepoint(event.pos):
                    in_menu = True
                    in_character_select = False
                    paused = False
            elif (
                not in_menu
                and not in_character_select
                and event.type == pygame.KEYDOWN
                and event.key == pygame.K_ESCAPE
            ):
                paused = not paused
            else:
                if not in_menu and not in_character_select and not paused:
                    handle_input_event(event, player, enemy, enemy_ai, player_state, platforms)

        if in_menu:
            draw_main_menu(
                screen,
                menu_title_font,
                menu_option_font,
                play_button_rect.collidepoint(mouse_pos),
                character_select_button_rect.collidepoint(mouse_pos),
            )
            continue

        if in_character_select:
            draw_character_select(
                screen,
                pause_font,
                menu_option_font,
                selected_character,
                mantis_card_rect.collidepoint(mouse_pos),
                spider_card_rect.collidepoint(mouse_pos),
                rhino_card_rect.collidepoint(mouse_pos),
                character_select_back_rect.collidepoint(mouse_pos),
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
        update_particles(player, enemy, enemy_ai, player_state, dt)
        handle_respawns(player, enemy, player_state, enemy_ai, player_spawn, enemy_spawn, dt)

        keys = pygame.key.get_pressed()
        update_player(player, player_state, keys, platforms, dt)
        update_enemy(enemy, enemy_ai, player, player_state, platforms, dt)
        resolve_combat(player, enemy, enemy_ai, player_state)

        render_frame(screen, font, floating_text_font, platforms, player, enemy, player_state)

    pygame.quit()

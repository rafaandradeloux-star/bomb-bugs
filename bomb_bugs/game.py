import pygame

from .character_profiles import apply_character_profile
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
    player.special_counter_active = False
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
    end_font = create_pixel_font(78)

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
        bomb_damage=3,
        facing_dir=-1,
    )

    player_state, enemy_ai = _reset_combat_state(player, enemy, player_spawn, enemy_spawn)
    selected_character = "mantis"
    apply_character_profile(player, selected_character, refill_hp=True)

    running = True
    paused = False
    in_menu = True
    in_character_select = False
    score_target = 5
    player_kills = 0
    player_deaths = 0
    counter_pulse_duration = 0.9
    left_counter_pulse = 0.0
    right_counter_pulse = 0.0
    enemy_death_counted = False
    player_death_counted = False
    end_state_pending = False
    end_state_pending_timer = 0.0
    end_state_duration = 3.5
    end_state_fade_in_time = 0.45
    end_state_active = False
    end_state_timer = 0.0
    end_state_text = ""
    while running:
        dt = clock.tick(60) / 1000.0
        mouse_pos = pygame.mouse.get_pos()
        left_counter_pulse = max(0.0, left_counter_pulse - dt)
        right_counter_pulse = max(0.0, right_counter_pulse - dt)

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
                end_state_active = False
                end_state_pending = False
                end_state_pending_timer = 0.0
                end_state_timer = 0.0
                end_state_text = ""
                player_kills = 0
                player_deaths = 0
                left_counter_pulse = 0.0
                right_counter_pulse = 0.0
                enemy_death_counted = False
                player_death_counted = False
                player_state, enemy_ai = _reset_combat_state(player, enemy, player_spawn, enemy_spawn)
            elif in_menu and event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if play_button_rect.collidepoint(event.pos):
                    in_menu = False
                    in_character_select = False
                    paused = False
                    end_state_active = False
                    end_state_pending = False
                    end_state_pending_timer = 0.0
                    end_state_timer = 0.0
                    end_state_text = ""
                    player_kills = 0
                    player_deaths = 0
                    left_counter_pulse = 0.0
                    right_counter_pulse = 0.0
                    enemy_death_counted = False
                    player_death_counted = False
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
                    apply_character_profile(player, selected_character)
                    in_character_select = False
                    in_menu = True
                    paused = False
                elif spider_card_rect.collidepoint(event.pos):
                    selected_character = "spider"
                    apply_character_profile(player, selected_character)
                    in_character_select = False
                    in_menu = True
                    paused = False
                elif rhino_card_rect.collidepoint(event.pos):
                    selected_character = "rhino_beetle"
                    apply_character_profile(player, selected_character)
                    in_character_select = False
                    in_menu = True
                    paused = False
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
                and not end_state_active
            ):
                paused = not paused
            else:
                if not in_menu and not in_character_select and not paused and not end_state_active:
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
            render_frame(
                screen,
                font,
                floating_text_font,
                platforms,
                player,
                enemy,
                enemy_ai,
                player_state,
                left_score=player_kills,
                right_score=player_deaths,
                score_target=score_target,
                left_pulse_time=left_counter_pulse,
                right_pulse_time=right_counter_pulse,
                pulse_duration=counter_pulse_duration,
                present=False,
            )
            draw_pause_overlay(
                screen,
                pause_font,
                menu_option_font,
                leave_button_rect.collidepoint(mouse_pos),
            )
            pygame.display.flip()
            continue

        if end_state_pending and not end_state_active:
            end_state_pending_timer = max(0.0, end_state_pending_timer - dt)
            if end_state_pending_timer <= 0.0:
                end_state_pending = False
                end_state_active = True
                end_state_timer = end_state_duration

        if end_state_active:
            render_frame(
                screen,
                font,
                floating_text_font,
                platforms,
                player,
                enemy,
                enemy_ai,
                player_state,
                left_score=player_kills,
                right_score=player_deaths,
                score_target=score_target,
                left_pulse_time=left_counter_pulse,
                right_pulse_time=right_counter_pulse,
                pulse_duration=counter_pulse_duration,
                present=False,
            )
            elapsed = end_state_duration - end_state_timer
            fade_ratio = 1.0 if end_state_fade_in_time <= 0.0 else max(0.0, min(1.0, elapsed / end_state_fade_in_time))
            shade = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
            shade.fill((0, 0, 0, int(140 * fade_ratio)))
            screen.blit(shade, (0, 0))
            result_label = end_font.render(end_state_text, False, (255, 255, 255))
            result_outline = end_font.render(end_state_text, False, (26, 26, 26))
            result_label.set_alpha(int(255 * fade_ratio))
            result_outline.set_alpha(int(255 * fade_ratio))
            result_rect = result_label.get_rect(center=(WIDTH // 2, HEIGHT // 2))
            for ox, oy in ((-3, 0), (3, 0), (0, -3), (0, 3), (-3, -3), (3, 3), (-3, 3), (3, -3)):
                screen.blit(result_outline, (result_rect.x + ox, result_rect.y + oy))
            screen.blit(result_label, result_rect)
            pygame.display.flip()
            end_state_timer = max(0.0, end_state_timer - dt)
            if end_state_timer <= 0.0:
                in_menu = True
                in_character_select = False
                paused = False
                end_state_active = False
                end_state_pending = False
                end_state_pending_timer = 0.0
                end_state_text = ""
                player_kills = 0
                player_deaths = 0
                left_counter_pulse = 0.0
                right_counter_pulse = 0.0
                enemy_death_counted = False
                player_death_counted = False
                player_state, enemy_ai = _reset_combat_state(player, enemy, player_spawn, enemy_spawn)
            continue

        tick_timers(player, enemy, player_state, dt)
        update_particles(player, enemy, enemy_ai, player_state, dt)
        handle_respawns(player, enemy, player_state, enemy_ai, player_spawn, enemy_spawn, dt)

        keys = pygame.key.get_pressed()
        update_player(player, player_state, keys, platforms, dt)
        update_enemy(enemy, enemy_ai, player, player_state, platforms, dt)
        resolve_combat(player, enemy, enemy_ai, player_state)

        if not enemy.alive and not enemy_death_counted:
            player_kills = min(score_target, player_kills + 1)
            left_counter_pulse = counter_pulse_duration
            enemy_death_counted = True
        if enemy.alive:
            enemy_death_counted = False

        if not player.alive and not player_death_counted:
            player_deaths = min(score_target, player_deaths + 1)
            right_counter_pulse = counter_pulse_duration
            player_death_counted = True
        if player.alive:
            player_death_counted = False

        if not end_state_pending and not end_state_active and (player_kills >= score_target or player_deaths >= score_target):
            end_state_pending = True
            end_state_pending_timer = 0.6
            end_state_text = "YOU WIN" if player_kills >= score_target else "GAME OVER"
            paused = False

        render_frame(
            screen,
            font,
            floating_text_font,
            platforms,
            player,
            enemy,
            enemy_ai,
            player_state,
            left_score=player_kills,
            right_score=player_deaths,
            score_target=score_target,
            left_pulse_time=left_counter_pulse,
            right_pulse_time=right_counter_pulse,
            pulse_duration=counter_pulse_duration,
        )

    pygame.quit()

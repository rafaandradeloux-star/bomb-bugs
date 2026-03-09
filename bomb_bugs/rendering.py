import pygame
import math

from .config import (
    BACKGROUND,
    BOMB_RADIUS,
    PLATFORM_COLOR,
    RESPAWN_ANIM_TIME,
    SCREEN_SHAKE_DURATION,
    SCREEN_SHAKE_INTENSITY,
    SQUARE_COLOR,
    WEB_UNWRAP_BLIP_DURATION,
)
from .effects import (
    draw_crescent_slash,
    draw_dash_trail,
    draw_dust_particles,
    draw_ground_dents,
    draw_ground_pound_dive,
    draw_ground_spikes,
    draw_heal_splashes,
    draw_mushroom_clouds,
    draw_respawn_particles,
    draw_rubble_particles,
)
from .models import Actor, EnemyAI, PlayerState
from .ui import draw_ability_boxes, draw_floating_texts, draw_health_bar


def render_frame(
    screen: pygame.Surface,
    font: pygame.font.Font,
    floating_text_font: pygame.font.Font,
    platforms: list[pygame.Rect],
    player: Actor,
    enemy: Actor,
    enemy_ai: EnemyAI,
    player_state: PlayerState,
    present: bool = True,
) -> None:
    scene = pygame.Surface(screen.get_size())
    scene.fill(BACKGROUND)
    for platform in platforms:
        pygame.draw.rect(scene, PLATFORM_COLOR, platform)

    draw_dash_trail(scene, player_state.dash_trail, player.rect.width, player.color)
    draw_dash_trail(scene, player_state.bomb_trail, BOMB_RADIUS * 2, (45, 45, 45))
    draw_heal_splashes(scene, player_state.heal_splashes)
    draw_ground_dents(scene, player_state.ground_dents)
    draw_ground_spikes(scene, player_state.ground_spikes)
    draw_rubble_particles(scene, player_state.rubble_particles)
    draw_mushroom_clouds(scene, player_state.mushroom_clouds)
    special_icon = None
    if player.special_stun_duration > 0.0:
        special_icon = "web"
    elif player.special_invincible_duration > 0.0:
        special_icon = "shield"
    draw_ability_boxes(
        scene,
        player_state.dash_cooldown_left,
        player_state.heal_cooldown_left,
        player.bomb_charge_hits,
        player.bomb_hits_required,
        player.ground_pound_charge_hits,
        player.ground_pound_hits_required,
        player.special_charge_hits,
        player.special_hits_required,
        special_icon,
    )

    for bomb in player_state.bombs:
        radius = int(bomb.radius)
        pygame.draw.circle(scene, (28, 28, 28), (int(bomb.x), int(bomb.y)), radius)
        pygame.draw.circle(scene, (250, 160, 40), (int(bomb.x - radius * 0.2), int(bomb.y - radius * 0.6)), 2)
    for web in player_state.web_projectiles:
        cx, cy = int(web.x), int(web.y)
        radius = int(web.radius)
        pygame.draw.circle(scene, (245, 245, 245), (cx, cy), radius, 2)
        pygame.draw.line(scene, (245, 245, 245), (cx - radius, cy), (cx + radius, cy), 1)
        pygame.draw.line(scene, (245, 245, 245), (cx, cy - radius), (cx, cy + radius), 1)
        d = max(2, int(radius * 0.72))
        pygame.draw.line(scene, (245, 245, 245), (cx - d, cy - d), (cx + d, cy + d), 1)
        pygame.draw.line(scene, (245, 245, 245), (cx - d, cy + d), (cx + d, cy - d), 1)

    player_walking_in = _is_respawn_walking(player)
    if player.alive or player_walking_in:
        player_draw_color = _flash_tinted_color(player.color, player.hit_flash_time, player.hit_flash_duration)
        pygame.draw.rect(scene, player_draw_color, player.rect)
        if player.alive:
            draw_health_bar(scene, player.rect, player.hp, player.max_hp)
        if player.alive and player_state.ground_pound_active:
            draw_ground_pound_dive(scene, player.rect, player_state.velocity_y)
    enemy_walking_in = _is_respawn_walking(enemy)
    if enemy.alive or enemy_walking_in:
        enemy_draw_color = _flash_tinted_color(enemy.color, enemy.hit_flash_time, enemy.hit_flash_duration)
        pygame.draw.rect(scene, enemy_draw_color, enemy.rect)
        wrap_alpha = 0
        if enemy_ai.stun_time_left > 0.0:
            wrap_alpha = 255
        elif enemy_ai.web_unwrap_blip_time > 0.0:
            wrap_alpha = int(255 * (enemy_ai.web_unwrap_blip_time / WEB_UNWRAP_BLIP_DURATION))
        if wrap_alpha > 0:
            _draw_web_wrap_overlay(scene, enemy.rect, wrap_alpha)
        if enemy.alive:
            draw_health_bar(scene, enemy.rect, enemy.hp, enemy.max_hp)

    draw_dust_particles(scene, player.death_particles, (170, 150, 130))
    draw_dust_particles(scene, enemy.death_particles, (170, 150, 130))
    draw_respawn_particles(scene, player.respawn_particles)
    draw_respawn_particles(scene, enemy.respawn_particles)

    if player.alive and player.slash_time_left > 0.0:
        draw_crescent_slash(scene, player.rect, player.facing_dir, player.slash_time_left)
    if enemy.alive and enemy.slash_time_left > 0.0:
        draw_crescent_slash(scene, enemy.rect, enemy.facing_dir, enemy.slash_time_left)

    draw_floating_texts(scene, floating_text_font, player_state.floating_texts)

    shake_x, shake_y = _screen_shake_offset(player_state.shake_time_left, player_state.shake_phase)
    screen.fill(BACKGROUND)
    screen.blit(scene, (shake_x, shake_y))

    if present:
        pygame.display.flip()


def _screen_shake_offset(time_left: float, phase: float) -> tuple[int, int]:
    if time_left <= 0.0:
        return 0, 0
    strength = (time_left / SCREEN_SHAKE_DURATION) * SCREEN_SHAKE_INTENSITY
    x = int(math.sin(phase * 1.1) * strength)
    y = int(math.cos(phase * 0.9) * strength * 0.55)
    return x, y


def _flash_tinted_color(base: tuple[int, int, int], time_left: float, duration: float) -> tuple[int, int, int]:
    if duration <= 0.0 or time_left <= 0.0:
        return base
    t = max(0.0, min(1.0, time_left / duration))
    flash = (255, 255, 255)
    return (
        int(base[0] * (1.0 - t) + flash[0] * t),
        int(base[1] * (1.0 - t) + flash[1] * t),
        int(base[2] * (1.0 - t) + flash[2] * t),
    )


def _is_respawn_walking(actor: Actor) -> bool:
    return not actor.alive and 0.0 < actor.respawn_timer <= RESPAWN_ANIM_TIME


def _draw_web_wrap_overlay(surface: pygame.Surface, rect: pygame.Rect, alpha: int) -> None:
    alpha = max(0, min(255, alpha))
    if alpha <= 0:
        return
    overlay = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
    overlay.fill((246, 246, 246, alpha))

    # Layered texture panels to suggest stacked web wraps.
    panel_alpha = min(255, int(alpha * 0.72))
    pygame.draw.rect(overlay, (228, 228, 228, panel_alpha), pygame.Rect(3, 3, rect.width - 6, rect.height - 6), 2)
    pygame.draw.rect(overlay, (236, 236, 236, panel_alpha), pygame.Rect(8, 8, rect.width - 16, rect.height - 16), 2)
    pygame.draw.rect(overlay, (220, 220, 220, panel_alpha), pygame.Rect(13, 13, rect.width - 26, rect.height - 26), 1)

    # Strands crossing to create a layered cocoon look.
    strand_alpha = min(255, int(alpha * 0.85))
    w, h = rect.width, rect.height
    pygame.draw.line(overlay, (255, 255, 255, strand_alpha), (0, h // 2), (w, h // 2), 2)
    pygame.draw.line(overlay, (244, 244, 244, strand_alpha), (w // 2, 0), (w // 2, h), 2)
    pygame.draw.line(overlay, (250, 250, 250, strand_alpha), (2, 2), (w - 2, h - 2), 1)
    pygame.draw.line(overlay, (250, 250, 250, strand_alpha), (2, h - 2), (w - 2, 2), 1)

    surface.blit(overlay, rect.topleft)


def draw_pause_overlay(
    screen: pygame.Surface,
    pause_font: pygame.font.Font,
    option_font: pygame.font.Font,
    leave_hovered: bool,
) -> pygame.Rect:
    shade = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
    shade.fill((0, 0, 0, 110))
    screen.blit(shade, (0, 0))

    label = pause_font.render("PAUSED", False, (255, 255, 255))
    outline = pause_font.render("PAUSED", False, (36, 36, 36))
    x = (screen.get_width() - label.get_width()) // 2
    y = 34

    # Pixel bubble-style outline
    for ox, oy in ((-2, 0), (2, 0), (0, -2), (0, 2), (-2, -2), (2, 2), (-2, 2), (2, -2)):
        screen.blit(outline, (x + ox, y + oy))
    screen.blit(label, (x, y))

    leave_label = option_font.render("Leave", False, (255, 255, 255) if leave_hovered else (230, 230, 230))
    leave_outline = option_font.render("Leave", False, (24, 24, 24))
    leave_rect = leave_label.get_rect(center=(screen.get_width() // 2, 210))
    box = leave_rect.inflate(44, 26)
    fill = (124, 86, 58) if leave_hovered else (98, 67, 46)
    pygame.draw.rect(screen, fill, box)
    pygame.draw.rect(screen, (34, 24, 17), box, 4)
    for ox, oy in ((-2, 0), (2, 0), (0, -2), (0, 2)):
        screen.blit(leave_outline, (leave_rect.x + ox, leave_rect.y + oy))
    screen.blit(leave_label, leave_rect)

    return box


def draw_main_menu(
    screen: pygame.Surface,
    title_font: pygame.font.Font,
    option_font: pygame.font.Font,
    play_hovered: bool,
    character_select_hovered: bool,
) -> None:
    screen.fill(BACKGROUND)

    title = title_font.render("BOMB BUGS", False, (255, 255, 255))
    title_outline = title_font.render("BOMB BUGS", False, (38, 38, 38))
    title_x = (screen.get_width() - title.get_width()) // 2
    title_y = 112
    for ox, oy in ((-3, 0), (3, 0), (0, -3), (0, 3), (-3, -3), (3, 3), (-3, 3), (3, -3)):
        screen.blit(title_outline, (title_x + ox, title_y + oy))
    screen.blit(title, (title_x, title_y))

    play_label = option_font.render("Play", False, (255, 255, 255) if play_hovered else (230, 230, 230))
    play_outline = option_font.render("Play", False, (24, 24, 24))
    play_rect = play_label.get_rect(center=(screen.get_width() // 2, 300))
    box = play_rect.inflate(44, 26)
    fill = (124, 86, 58) if play_hovered else (98, 67, 46)
    pygame.draw.rect(screen, fill, box)
    pygame.draw.rect(screen, (34, 24, 17), box, 4)
    for ox, oy in ((-2, 0), (2, 0), (0, -2), (0, 2)):
        screen.blit(play_outline, (play_rect.x + ox, play_rect.y + oy))
    screen.blit(play_label, play_rect)

    select_label = option_font.render(
        "Character select",
        False,
        (255, 255, 255) if character_select_hovered else (230, 230, 230),
    )
    select_outline = option_font.render("Character select", False, (24, 24, 24))
    select_rect = select_label.get_rect(center=(screen.get_width() // 2, 360))
    select_box = select_rect.inflate(44, 26)
    select_fill = (124, 86, 58) if character_select_hovered else (98, 67, 46)
    pygame.draw.rect(screen, select_fill, select_box)
    pygame.draw.rect(screen, (34, 24, 17), select_box, 4)
    for ox, oy in ((-2, 0), (2, 0), (0, -2), (0, 2)):
        screen.blit(select_outline, (select_rect.x + ox, select_rect.y + oy))
    screen.blit(select_label, select_rect)

    pygame.display.flip()


def draw_character_select(
    screen: pygame.Surface,
    title_font: pygame.font.Font,
    option_font: pygame.font.Font,
    selected_character: str,
    mantis_hovered: bool,
    spider_hovered: bool,
    rhino_hovered: bool,
    back_hovered: bool,
) -> None:
    screen.fill(BACKGROUND)

    title = title_font.render("Character Select", False, (255, 255, 255))
    title_outline = title_font.render("Character Select", False, (38, 38, 38))
    title_x = (screen.get_width() - title.get_width()) // 2
    title_y = 80
    for ox, oy in ((-3, 0), (3, 0), (0, -3), (0, 3), (-3, -3), (3, 3), (-3, 3), (3, -3)):
        screen.blit(title_outline, (title_x + ox, title_y + oy))
    screen.blit(title, (title_x, title_y))

    card_size = (220, 250)
    mantis_card = pygame.Rect(0, 0, card_size[0], card_size[1])
    mantis_card.center = (screen.get_width() // 2 - 250, 255)
    spider_card = pygame.Rect(0, 0, card_size[0], card_size[1])
    spider_card.center = (screen.get_width() // 2, 255)
    rhino_card = pygame.Rect(0, 0, card_size[0], card_size[1])
    rhino_card.center = (screen.get_width() // 2 + 250, 255)

    _draw_character_card(
        screen,
        option_font,
        mantis_card,
        SQUARE_COLOR,
        "mantis",
        selected_character == "mantis",
        mantis_hovered,
    )
    _draw_character_card(
        screen,
        option_font,
        spider_card,
        (180, 142, 97),
        "spider",
        selected_character == "spider",
        spider_hovered,
    )
    _draw_character_card(
        screen,
        option_font,
        rhino_card,
        (34, 60, 126),
        "rhino beetle",
        selected_character == "rhino_beetle",
        rhino_hovered,
    )

    back_label = option_font.render("Back", False, (255, 255, 255) if back_hovered else (230, 230, 230))
    back_outline = option_font.render("Back", False, (24, 24, 24))
    back_rect = back_label.get_rect(center=(screen.get_width() // 2, 470))
    back_box = back_rect.inflate(44, 26)
    back_fill = (124, 86, 58) if back_hovered else (98, 67, 46)
    pygame.draw.rect(screen, back_fill, back_box)
    pygame.draw.rect(screen, (34, 24, 17), back_box, 4)
    for ox, oy in ((-2, 0), (2, 0), (0, -2), (0, 2)):
        screen.blit(back_outline, (back_rect.x + ox, back_rect.y + oy))
    screen.blit(back_label, back_rect)

    pygame.display.flip()


def _draw_character_card(
    screen: pygame.Surface,
    option_font: pygame.font.Font,
    card: pygame.Rect,
    square_color: tuple[int, int, int],
    label_text: str,
    selected: bool,
    hovered: bool,
) -> None:
    card_fill = (111, 78, 54) if hovered else (98, 67, 46)
    pygame.draw.rect(screen, card_fill, card)
    border_color = (255, 224, 130) if selected else (34, 24, 17)
    border_width = 5 if selected else 4
    pygame.draw.rect(screen, border_color, card, border_width)

    square_box = pygame.Rect(0, 0, 128, 128)
    square_box.center = (card.centerx, card.top + 86)
    pygame.draw.rect(screen, (122, 94, 70), square_box)
    pygame.draw.rect(screen, (34, 24, 17), square_box, 3)
    sprite = pygame.Rect(0, 0, 74, 74)
    sprite.center = square_box.center
    pygame.draw.rect(screen, square_color, sprite)

    label = option_font.render(label_text, False, (245, 245, 245))
    label_rect = label.get_rect(center=(card.centerx, card.top + 186))
    outline = option_font.render(label_text, False, (24, 24, 24))
    for ox, oy in ((-2, 0), (2, 0), (0, -2), (0, 2)):
        screen.blit(outline, (label_rect.x + ox, label_rect.y + oy))
    screen.blit(label, label_rect)

import pygame
import math

from .config import BACKGROUND, BOMB_RADIUS, MAX_HP, PLATFORM_COLOR, SCREEN_SHAKE_DURATION, SCREEN_SHAKE_INTENSITY
from .effects import (
    draw_crescent_slash,
    draw_dash_trail,
    draw_dust_particles,
    draw_heal_splashes,
    draw_mushroom_clouds,
    draw_respawn_particles,
)
from .models import Actor, PlayerState
from .ui import draw_ability_boxes, draw_floating_texts, draw_health_bar


def render_frame(
    screen: pygame.Surface,
    font: pygame.font.Font,
    floating_text_font: pygame.font.Font,
    platforms: list[pygame.Rect],
    player: Actor,
    enemy: Actor,
    player_state: PlayerState,
) -> None:
    scene = pygame.Surface(screen.get_size())
    scene.fill(BACKGROUND)
    for platform in platforms:
        pygame.draw.rect(scene, PLATFORM_COLOR, platform)

    draw_dash_trail(scene, player_state.dash_trail, player.rect.width, player.color)
    draw_dash_trail(scene, player_state.bomb_trail, BOMB_RADIUS * 2, (45, 45, 45))
    draw_heal_splashes(scene, player_state.heal_splashes)
    draw_mushroom_clouds(scene, player_state.mushroom_clouds)
    draw_ability_boxes(
        scene,
        player_state.dash_cooldown_left,
        player_state.heal_cooldown_left,
        player_state.bomb_cooldown_left,
    )

    for bomb in player_state.bombs:
        radius = int(bomb.radius)
        pygame.draw.circle(scene, (28, 28, 28), (int(bomb.x), int(bomb.y)), radius)
        pygame.draw.circle(scene, (250, 160, 40), (int(bomb.x - radius * 0.2), int(bomb.y - radius * 0.6)), 2)

    if player.alive:
        pygame.draw.rect(scene, player.color, player.rect)
        draw_health_bar(scene, player.rect, player.hp, MAX_HP)
    if enemy.alive:
        pygame.draw.rect(scene, enemy.color, enemy.rect)
        draw_health_bar(scene, enemy.rect, enemy.hp, MAX_HP)

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

    pygame.display.flip()


def _screen_shake_offset(time_left: float, phase: float) -> tuple[int, int]:
    if time_left <= 0.0:
        return 0, 0
    strength = (time_left / SCREEN_SHAKE_DURATION) * SCREEN_SHAKE_INTENSITY
    x = int(math.sin(phase * 1.1) * strength)
    y = int(math.cos(phase * 0.9) * strength * 0.55)
    return x, y

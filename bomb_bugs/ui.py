import pygame

from .config import HEALTH_BAR_HEIGHT, HEALTH_BAR_WIDTH, TEXT_COLOR
from .models import FloatingText


def draw_health_bar(surface: pygame.Surface, entity_rect: pygame.Rect, hp: int, max_hp: int) -> None:
    health_ratio = max(0.0, min(1.0, hp / max_hp))
    bar_x = entity_rect.centerx - HEALTH_BAR_WIDTH // 2
    bar_y = entity_rect.top - 16
    pygame.draw.rect(surface, (60, 20, 20), (bar_x, bar_y, HEALTH_BAR_WIDTH, HEALTH_BAR_HEIGHT))
    pygame.draw.rect(
        surface,
        (40, 200, 70),
        (bar_x, bar_y, int(HEALTH_BAR_WIDTH * health_ratio), HEALTH_BAR_HEIGHT),
    )
    pygame.draw.rect(surface, (20, 20, 20), (bar_x, bar_y, HEALTH_BAR_WIDTH, HEALTH_BAR_HEIGHT), 2)


def draw_debug_hud(
    surface: pygame.Surface,
    font: pygame.font.Font,
    player_pos: tuple[int, int],
    dash_cooldown: float,
    heal_cooldown: float,
    bomb_cooldown: float,
    player_slash_cd: float,
    enemy_slash_cd: float,
    player_hp: int,
    enemy_hp: int,
    player_alive: bool,
    enemy_alive: bool,
    player_respawn_timer: float,
    enemy_respawn_timer: float,
) -> None:
    lines = [
        f"Cube position: x={player_pos[0]}, y={player_pos[1]}",
        f"Dash cooldown: {dash_cooldown:.2f}s",
        f"Heal cooldown: {heal_cooldown:.2f}s",
        f"Bomb cooldown: {bomb_cooldown:.2f}s",
        f"Player slash cd: {player_slash_cd:.2f}s",
        f"Enemy slash cd: {enemy_slash_cd:.2f}s",
        f"Player HP: {player_hp}",
        f"Enemy HP: {enemy_hp}",
        f"Player respawn: {player_respawn_timer:.1f}s" if not player_alive else "Player respawn: ready",
        f"Enemy respawn: {enemy_respawn_timer:.1f}s" if not enemy_alive else "Enemy respawn: ready",
    ]

    y = 16
    for line in lines:
        text = font.render(line, True, TEXT_COLOR)
        surface.blit(text, (16, y))
        y += 32


def create_pixel_font(size: int = 18) -> pygame.font.Font:
    for name in ("pressstart2p", "silkscreen", "pixelmix"):
        path = pygame.font.match_font(name)
        if path:
            return pygame.font.Font(path, size)
    return pygame.font.Font(None, size)


def draw_floating_texts(surface: pygame.Surface, font: pygame.font.Font, texts: list[FloatingText]) -> None:
    for text in texts:
        alpha = int(255 * (text.life / text.max_life))
        glyph = font.render(text.text, False, text.color)
        glyph.set_alpha(alpha)
        surface.blit(glyph, (int(text.x), int(text.y)))

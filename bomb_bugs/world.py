import pygame

from .config import FLOOR_HEIGHT, HEIGHT, WIDTH


def make_platforms() -> list[pygame.Rect]:
    return [
        pygame.Rect(0, HEIGHT - FLOOR_HEIGHT, WIDTH, FLOOR_HEIGHT),
        pygame.Rect(120, 380, 220, 24),
        pygame.Rect(430, 315, 220, 24),
        pygame.Rect(735, 255, 170, 24),
    ]


def resolve_platform_landing(
    rect: pygame.Rect,
    previous_bottom: float,
    velocity_y: float,
    platforms: list[pygame.Rect],
) -> tuple[int, float, bool]:
    if velocity_y < 0:
        return rect.y, velocity_y, False

    landing_top = None
    for platform in platforms:
        crosses_top = previous_bottom <= platform.top and rect.bottom >= platform.top
        overlaps_x = rect.right > platform.left and rect.left < platform.right
        if crosses_top and overlaps_x:
            if landing_top is None or platform.top < landing_top:
                landing_top = platform.top

    if landing_top is None:
        return rect.y, velocity_y, False

    return landing_top - rect.height, 0.0, True

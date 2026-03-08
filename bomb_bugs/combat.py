import pygame

from .config import SLASH_HEIGHT, SLASH_RANGE_X


def build_slash_rect(entity_rect: pygame.Rect, facing_dir: int) -> pygame.Rect:
    slash_top = entity_rect.centery - SLASH_HEIGHT // 2
    if facing_dir >= 0:
        return pygame.Rect(entity_rect.right, slash_top, SLASH_RANGE_X, SLASH_HEIGHT)
    return pygame.Rect(entity_rect.left - SLASH_RANGE_X, slash_top, SLASH_RANGE_X, SLASH_HEIGHT)

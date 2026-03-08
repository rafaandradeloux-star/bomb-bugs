import math
import random

import pygame

from .config import (
    DUST_COUNT,
    DUST_DRIFT_X,
    DUST_DRIFT_Y,
    DUST_LIFETIME_MAX,
    DUST_LIFETIME_MIN,
    HEIGHT,
    MOON_MAX_RADIUS,
    MOON_MIN_RADIUS,
    MUSHROOM_CLOUD_LIFETIME,
    RESPAWN_ANIM_TIME,
    HEAL_SPLASH_TIME,
    SLASH_ACTIVE_TIME,
    SLASH_COLOR,
    TRAIL_LIFETIME,
    WIDTH,
)
from .models import DustParticle, HealSplash, MushroomCloud, RespawnParticle


def make_dust_particles(rect: pygame.Rect) -> list[DustParticle]:
    particles: list[DustParticle] = []
    for _ in range(DUST_COUNT):
        life = random.uniform(DUST_LIFETIME_MIN, DUST_LIFETIME_MAX)
        particles.append(
            DustParticle(
                x=float(random.uniform(rect.left, rect.right)),
                y=float(random.uniform(rect.top, rect.bottom)),
                vx=float(random.uniform(-DUST_DRIFT_X, DUST_DRIFT_X)),
                vy=float(random.uniform(-DUST_DRIFT_Y, DUST_DRIFT_Y * 0.5)),
                life=life,
                max_life=life,
                size=float(random.uniform(1.5, 4.0)),
            )
        )
    return particles


def make_trail_particle(x: float, y: float) -> DustParticle:
    return DustParticle(
        x=x,
        y=y,
        vx=0.0,
        vy=0.0,
        life=TRAIL_LIFETIME,
        max_life=TRAIL_LIFETIME,
        size=12.0,
    )


def update_dust_particles(particles: list[DustParticle], dt: float) -> list[DustParticle]:
    for particle in particles:
        particle.life -= dt
        particle.vx *= 0.985
        particle.vy *= 0.985
        particle.x += particle.vx * dt
        particle.y += particle.vy * dt
    return [particle for particle in particles if particle.life > 0.0]


def draw_dust_particles(surface: pygame.Surface, particles: list[DustParticle], color: tuple[int, int, int]) -> None:
    for particle in particles:
        life_ratio = particle.life / particle.max_life
        alpha = int(200 * life_ratio)
        size = max(1, int(particle.size * (0.55 + 0.45 * life_ratio)))
        pygame.draw.circle(surface, (*color, alpha), (int(particle.x), int(particle.y)), size)


def draw_dash_trail(surface: pygame.Surface, particles: list[DustParticle], size: int, color: tuple[int, int, int]) -> None:
    for particle in particles:
        life_ratio = particle.life / particle.max_life
        alpha = int(150 * life_ratio)
        ghost_surface = pygame.Surface((size, size), pygame.SRCALPHA)
        ghost_surface.fill((*color, alpha))
        surface.blit(ghost_surface, (int(particle.x), int(particle.y)))


def make_respawn_particles(rect: pygame.Rect, color: tuple[int, int, int]) -> list[RespawnParticle]:
    particles: list[RespawnParticle] = []
    for _ in range(DUST_COUNT):
        tx = float(random.uniform(rect.left, rect.right))
        ty = float(random.uniform(rect.top, rect.bottom))
        angle = random.uniform(0.0, math.tau)
        dist = random.uniform(36.0, 130.0)
        sx = tx + math.cos(angle) * dist
        sy = ty + math.sin(angle) * dist
        particles.append(
            RespawnParticle(
                sx=sx,
                sy=sy,
                tx=tx,
                ty=ty,
                life=RESPAWN_ANIM_TIME,
                max_life=RESPAWN_ANIM_TIME,
                size=float(random.uniform(1.8, 4.4)),
                r=float(color[0]),
                g=float(color[1]),
                b=float(color[2]),
            )
        )
    return particles


def update_respawn_particles(particles: list[RespawnParticle], dt: float) -> list[RespawnParticle]:
    for particle in particles:
        particle.life -= dt
    return [particle for particle in particles if particle.life > 0.0]


def draw_respawn_particles(surface: pygame.Surface, particles: list[RespawnParticle]) -> None:
    for particle in particles:
        progress = 1.0 - (particle.life / particle.max_life)
        progress = max(0.0, min(1.0, progress))
        x = particle.sx + (particle.tx - particle.sx) * progress
        y = particle.sy + (particle.ty - particle.sy) * progress
        alpha = int(220 * progress)
        size = max(1, int(particle.size * (1.0 - 0.25 * progress)))
        pygame.draw.circle(surface, (int(particle.r), int(particle.g), int(particle.b), alpha), (int(x), int(y)), size)


def draw_crescent_slash(surface: pygame.Surface, entity_rect: pygame.Rect, facing_dir: int, slash_time_left: float) -> None:
    slash_progress = 1.0 - (slash_time_left / SLASH_ACTIVE_TIME)
    slash_progress = max(0.0, min(1.0, slash_progress))

    pulse = math.sin(math.pi * slash_progress)  # 0 -> 1 -> 0
    moon_radius = int(MOON_MIN_RADIUS + (MOON_MAX_RADIUS - MOON_MIN_RADIUS) * pulse)
    moon_alpha = int(230 * pulse)
    glow_alpha = int(110 * pulse)

    center_x = int(entity_rect.centerx + facing_dir * (18 + 34 * slash_progress))
    center_y = int(entity_rect.centery)
    inner_radius = int(moon_radius * 0.78)
    inner_x = center_x - facing_dir * int(moon_radius * 0.42)

    slash_surface = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    pygame.draw.circle(slash_surface, (*SLASH_COLOR, glow_alpha), (center_x, center_y), moon_radius + 10)
    pygame.draw.circle(slash_surface, (*SLASH_COLOR, moon_alpha), (center_x, center_y), moon_radius)
    pygame.draw.circle(slash_surface, (0, 0, 0, 0), (inner_x, center_y), inner_radius)
    surface.blit(slash_surface, (0, 0))


def make_heal_splash(x: float, y: float, max_radius: float = 58.0) -> HealSplash:
    return HealSplash(x=x, y=y, life=HEAL_SPLASH_TIME, max_life=HEAL_SPLASH_TIME, max_radius=max_radius)


def update_heal_splashes(splashes: list[HealSplash], dt: float) -> list[HealSplash]:
    for splash in splashes:
        splash.life -= dt
    return [splash for splash in splashes if splash.life > 0.0]


def draw_heal_splashes(surface: pygame.Surface, splashes: list[HealSplash]) -> None:
    for splash in splashes:
        progress = 1.0 - (splash.life / splash.max_life)
        progress = max(0.0, min(1.0, progress))
        splash_surface = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        # New style: pulse ring + vertical mist columns.
        alpha = int(210 * (1.0 - progress))
        ring_radius = int(8 + splash.max_radius * progress)
        ring_thickness = max(2, int(10 * (1.0 - progress)))

        pygame.draw.circle(
            splash_surface,
            (60, 230, 110, alpha),
            (int(splash.x), int(splash.y)),
            ring_radius,
            ring_thickness,
        )

        core_alpha = int(120 * (1.0 - progress))
        pygame.draw.circle(
            splash_surface,
            (35, 170, 80, core_alpha),
            (int(splash.x), int(splash.y)),
            max(3, ring_radius // 4),
        )

        mist_count = 9
        for i in range(mist_count):
            offset = -30 + (60 / (mist_count - 1)) * i
            lift = 6 + 34 * progress + 8 * math.sin(progress * math.pi + i * 0.45)
            mx = splash.x + offset
            my = splash.y - lift
            size = max(2, int(6 - progress * 3))
            pygame.draw.circle(
                splash_surface,
                (85, 245, 140, int(alpha * 0.55)),
                (int(mx), int(my)),
                size,
            )
        surface.blit(splash_surface, (0, 0))


def make_mushroom_cloud(x: float, y: float) -> MushroomCloud:
    return MushroomCloud(x=x, y=y, life=MUSHROOM_CLOUD_LIFETIME, max_life=MUSHROOM_CLOUD_LIFETIME)


def update_mushroom_clouds(clouds: list[MushroomCloud], dt: float) -> list[MushroomCloud]:
    for cloud in clouds:
        cloud.life -= dt
    return [cloud for cloud in clouds if cloud.life > 0.0]


def draw_mushroom_clouds(surface: pygame.Surface, clouds: list[MushroomCloud]) -> None:
    for cloud in clouds:
        progress = 1.0 - (cloud.life / cloud.max_life)
        progress = max(0.0, min(1.0, progress))

        # End-of-life "blip away" behavior: rapid flicker, then hard vanish.
        if progress > 0.82:
            flicker = int(cloud.life * 95)
            if flicker % 3 == 0:
                continue
            if progress > 0.94 and flicker % 2 == 0:
                continue

        # Rising stem.
        stem_height = int(8 + 72 * progress)
        stem_width = int(6 + 12 * progress)
        stem_alpha = int(220 * (1.0 - progress * 0.55))
        stem_rect = pygame.Rect(
            int(cloud.x - stem_width / 2),
            int(cloud.y - stem_height),
            stem_width,
            stem_height,
        )
        cloud_surface = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        pygame.draw.ellipse(cloud_surface, (120, 96, 78, stem_alpha), stem_rect)

        # Top cap expands like a mushroom dome.
        cap_radius = int(14 + 44 * progress)
        cap_center = (int(cloud.x), int(cloud.y - stem_height))
        cap_alpha = int(235 * (1.0 - progress * 0.5))
        pygame.draw.circle(cloud_surface, (168, 136, 108, cap_alpha), cap_center, cap_radius)
        pygame.draw.circle(
            cloud_surface,
            (208, 182, 148, int(cap_alpha * 0.65)),
            (cap_center[0] + int(cap_radius * 0.15), cap_center[1] - int(cap_radius * 0.12)),
            int(cap_radius * 0.62),
        )

        # Ground shock ring / dust.
        ring_radius = int(8 + 68 * progress)
        ring_alpha = int(160 * (1.0 - progress))
        pygame.draw.circle(
            cloud_surface,
            (180, 146, 116, ring_alpha),
            (int(cloud.x), int(cloud.y)),
            ring_radius,
            max(2, int(8 * (1.0 - progress))),
        )

        # Pixelate by scaling the local effect area down and back up.
        bounds_radius = ring_radius + 24
        effect_rect = pygame.Rect(
            int(cloud.x - bounds_radius),
            int(cloud.y - stem_height - bounds_radius),
            int(bounds_radius * 2),
            int(bounds_radius * 2 + stem_height),
        )
        effect_rect = effect_rect.clip(pygame.Rect(0, 0, WIDTH, HEIGHT))
        if effect_rect.width <= 0 or effect_rect.height <= 0:
            continue

        patch = cloud_surface.subsurface(effect_rect).copy()
        pixel_step = 5
        small_w = max(1, effect_rect.width // pixel_step)
        small_h = max(1, effect_rect.height // pixel_step)
        patch_small = pygame.transform.scale(patch, (small_w, small_h))
        patch_pixel = pygame.transform.scale(patch_small, (effect_rect.width, effect_rect.height))
        surface.blit(patch_pixel, effect_rect.topleft)

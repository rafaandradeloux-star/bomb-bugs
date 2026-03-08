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
    GROUND_SPIKE_LIFETIME,
    GROUND_DENT_LIFETIME,
    GROUND_DENT_MAX_DEPTH,
    RUBBLE_COUNT,
    RUBBLE_GRAVITY,
    RUBBLE_LIFETIME_MAX,
    RUBBLE_LIFETIME_MIN,
    RUBBLE_SPEED_X,
    RUBBLE_SPEED_Y,
    SLASH_ACTIVE_TIME,
    SLASH_COLOR,
    TRAIL_LIFETIME,
    WIDTH,
)
from .models import (
    DustParticle,
    GroundDent,
    GroundSpike,
    HealSplash,
    MushroomCloud,
    RespawnParticle,
    RubbleParticle,
)


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

    left = min(center_x, inner_x) - (moon_radius + 14)
    top = center_y - (moon_radius + 14)
    size = (moon_radius + 14) * 2
    effect_rect = pygame.Rect(left, top, max(1, size + abs(center_x - inner_x)), max(1, size))
    _blit_pixelated_patch(surface, slash_surface, effect_rect, pixel_step=4)


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


def make_ground_spike(x: float, y: float) -> GroundSpike:
    return GroundSpike(x=x, y=y, life=GROUND_SPIKE_LIFETIME, max_life=GROUND_SPIKE_LIFETIME)


def update_ground_spikes(spikes: list[GroundSpike], dt: float) -> list[GroundSpike]:
    for spike in spikes:
        spike.life -= dt
    return [spike for spike in spikes if spike.life > 0.0]


def draw_ground_spikes(surface: pygame.Surface, spikes: list[GroundSpike]) -> None:
    for spike in spikes:
        progress = 1.0 - (spike.life / spike.max_life)
        progress = max(0.0, min(1.0, progress))
        grow = math.sin(progress * math.pi)
        if grow <= 0.01:
            continue

        spike_surface = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        spike_height = int(16 + 38 * grow)
        spike_width = int(12 + 20 * grow)
        base_y = int(spike.y)
        center_x = int(spike.x)
        alpha = int(210 * (1.0 - progress * 0.65))

        # Center spike.
        pygame.draw.polygon(
            spike_surface,
            (198, 166, 132, alpha),
            [
                (center_x, base_y - spike_height),
                (center_x - spike_width // 2, base_y),
                (center_x + spike_width // 2, base_y),
            ],
        )
        # Side spikes.
        for direction in (-1, 1):
            ox = center_x + direction * int(spike_width * 0.85)
            oh = int(spike_height * 0.66)
            ow = int(spike_width * 0.75)
            pygame.draw.polygon(
                spike_surface,
                (168, 138, 108, int(alpha * 0.92)),
                [
                    (ox, base_y - oh),
                    (ox - ow // 2, base_y),
                    (ox + ow // 2, base_y),
                ],
            )

        # Small dust ring to sell the impact.
        ring_r = int(12 + 42 * progress)
        pygame.draw.circle(
            spike_surface,
            (170, 140, 108, int(120 * (1.0 - progress))),
            (center_x, base_y),
            ring_r,
            max(2, int(6 * (1.0 - progress))),
        )

        surface.blit(spike_surface, (0, 0))


def make_ground_dent(x: float, y: float) -> GroundDent:
    return GroundDent(x=x, y=y, life=GROUND_DENT_LIFETIME, max_life=GROUND_DENT_LIFETIME)


def update_ground_dents(dents: list[GroundDent], dt: float) -> list[GroundDent]:
    for dent in dents:
        dent.life -= dt
    return [dent for dent in dents if dent.life > 0.0]


def draw_ground_dents(surface: pygame.Surface, dents: list[GroundDent]) -> None:
    for dent in dents:
        progress = 1.0 - (dent.life / dent.max_life)
        progress = max(0.0, min(1.0, progress))
        # Deep at impact, then slowly returns to flat ground.
        strength = (1.0 - progress) ** 0.65
        if strength <= 0.01:
            continue

        half_w = int(38 + 22 * strength)
        depth = max(2, int(GROUND_DENT_MAX_DEPTH * strength))
        cx = int(dent.x)
        y = int(dent.y)

        dent_surface = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        dent_rect = pygame.Rect(cx - half_w, y - depth // 2, half_w * 2, depth)
        pygame.draw.ellipse(dent_surface, (118, 92, 68, int(175 * strength)), dent_rect)
        pygame.draw.arc(
            dent_surface,
            (165, 135, 108, int(140 * strength)),
            pygame.Rect(cx - half_w, y - depth, half_w * 2, depth * 2),
            math.pi,
            2 * math.pi,
            2,
        )
        surface.blit(dent_surface, (0, 0))


def make_rubble_particles(x: float, y: float) -> list[RubbleParticle]:
    particles: list[RubbleParticle] = []
    for _ in range(RUBBLE_COUNT):
        life = random.uniform(RUBBLE_LIFETIME_MIN, RUBBLE_LIFETIME_MAX)
        particles.append(
            RubbleParticle(
                x=x + random.uniform(-18.0, 18.0),
                y=y - random.uniform(0.0, 6.0),
                vx=random.uniform(-RUBBLE_SPEED_X, RUBBLE_SPEED_X),
                vy=-random.uniform(RUBBLE_SPEED_Y * 0.45, RUBBLE_SPEED_Y),
                life=life,
                max_life=life,
                size=random.uniform(3.0, 7.0),
            )
        )
    return particles


def update_rubble_particles(particles: list[RubbleParticle], dt: float) -> list[RubbleParticle]:
    for particle in particles:
        particle.life -= dt
        particle.vy += RUBBLE_GRAVITY * dt
        particle.vx *= 0.985
        particle.x += particle.vx * dt
        particle.y += particle.vy * dt
    return [particle for particle in particles if particle.life > 0.0]


def draw_rubble_particles(surface: pygame.Surface, particles: list[RubbleParticle]) -> None:
    for particle in particles:
        life_ratio = max(0.0, min(1.0, particle.life / particle.max_life))
        alpha = int(215 * life_ratio)
        size = max(2, int(particle.size * (0.65 + 0.35 * life_ratio)))
        rubble_surface = pygame.Surface((size, size), pygame.SRCALPHA)
        rubble_surface.fill((156, 126, 98, alpha))
        surface.blit(rubble_surface, (int(particle.x), int(particle.y)))


def draw_ground_pound_dive(surface: pygame.Surface, entity_rect: pygame.Rect, velocity_y: float) -> None:
    slash_surface = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    speed_ratio = max(0.0, min(1.0, velocity_y / 1800.0))
    cx = entity_rect.centerx
    cy = entity_rect.bottom + int(18 + 24 * speed_ratio)

    # Bigger downward crescent slash.
    outer_r = int(entity_rect.width * (0.95 + 0.5 * speed_ratio))
    inner_r = int(outer_r * 0.68)
    glow_r = outer_r + int(10 + 8 * speed_ratio)
    inner_y = cy - int(outer_r * 0.58)  # shift up so the crescent points downward

    pygame.draw.circle(slash_surface, (255, 240, 210, int(90 + 85 * speed_ratio)), (cx, cy), glow_r)
    pygame.draw.circle(slash_surface, (255, 255, 255, int(165 + 80 * speed_ratio)), (cx, cy), outer_r)
    pygame.draw.circle(slash_surface, (0, 0, 0, 0), (cx, inner_y), inner_r)

    # Downward trail so motion reads clearly.
    trail_h = int(entity_rect.height * (1.0 + 1.1 * speed_ratio))
    trail_w = int(entity_rect.width * 0.46)
    pygame.draw.ellipse(
        slash_surface,
        (255, 244, 216, int(105 + 80 * speed_ratio)),
        pygame.Rect(cx - trail_w // 2, entity_rect.bottom - 2, trail_w, trail_h),
    )
    left = cx - glow_r - 10
    top = min(cy - glow_r - 10, entity_rect.bottom - 4)
    width = (glow_r + 10) * 2
    height = (cy - top) + glow_r + 10
    trail_rect = pygame.Rect(cx - trail_w // 2 - 4, entity_rect.bottom - 4, trail_w + 8, trail_h + 8)
    effect_rect = pygame.Rect(left, top, width, height).union(trail_rect)
    _blit_pixelated_patch(surface, slash_surface, effect_rect, pixel_step=5)


def _blit_pixelated_patch(
    surface: pygame.Surface,
    effect_surface: pygame.Surface,
    effect_rect: pygame.Rect,
    pixel_step: int,
) -> None:
    clip_rect = effect_rect.clip(pygame.Rect(0, 0, WIDTH, HEIGHT))
    if clip_rect.width <= 0 or clip_rect.height <= 0:
        return
    patch = effect_surface.subsurface(clip_rect).copy()
    small_w = max(1, clip_rect.width // max(1, pixel_step))
    small_h = max(1, clip_rect.height // max(1, pixel_step))
    patch_small = pygame.transform.scale(patch, (small_w, small_h))
    patch_pixel = pygame.transform.scale(patch_small, (clip_rect.width, clip_rect.height))
    surface.blit(patch_pixel, clip_rect.topleft)

import math
import random
import sys

import pygame


WIDTH, HEIGHT = 960, 540
BACKGROUND = (135, 206, 235)  # sky blue
SQUARE_COLOR = (255, 200, 80)
ENEMY_COLOR = (180, 70, 70)
TEXT_COLOR = (20, 20, 20)
PLATFORM_COLOR = (205, 170, 125)  # light brown
SLASH_COLOR = (255, 255, 255)

SQUARE_SIZE = 64
ENEMY_SIZE = 56
MAX_HP = 10

SPEED = 420  # pixels/second
ENEMY_SPEED = 120  # pixels/second
GRAVITY = 1700  # pixels/second^2
JUMP_VELOCITY = -700  # pixels/second
FLOOR_HEIGHT = 80

DASH_SPEED = 980  # pixels/second
DASH_DURATION = 0.14  # seconds
DASH_COOLDOWN = 0.45  # seconds
TRAIL_LIFETIME = 0.12  # seconds
TRAIL_SPAWN_INTERVAL = 0.08  # seconds (lower trail FPS = choppier look)

SLASH_RANGE_X = 90
SLASH_HEIGHT = 70
SLASH_ACTIVE_TIME = 0.08  # seconds
PLAYER_SLASH_COOLDOWN = 0.20  # seconds
ENEMY_SLASH_COOLDOWN = 0.55  # seconds
MOON_MIN_RADIUS = 14
MOON_MAX_RADIUS = 60

RESPAWN_DELAY = 5.0  # seconds
RESPAWN_ANIM_TIME = 0.9  # seconds
DUST_COUNT = 140
DUST_LIFETIME_MIN = 0.7  # seconds
DUST_LIFETIME_MAX = 1.5  # seconds
DUST_DRIFT_X = 140  # pixels/second
DUST_DRIFT_Y = 90  # pixels/second

HEALTH_BAR_WIDTH = 64
HEALTH_BAR_HEIGHT = 8


def build_slash_rect(entity_rect: pygame.Rect, facing_dir: int) -> pygame.Rect:
    slash_top = entity_rect.centery - SLASH_HEIGHT // 2
    if facing_dir >= 0:
        return pygame.Rect(entity_rect.right, slash_top, SLASH_RANGE_X, SLASH_HEIGHT)
    return pygame.Rect(entity_rect.left - SLASH_RANGE_X, slash_top, SLASH_RANGE_X, SLASH_HEIGHT)


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


def draw_crescent_slash(
    surface: pygame.Surface,
    entity_rect: pygame.Rect,
    facing_dir: int,
    slash_time_left: float,
) -> None:
    slash_progress = 1.0 - (slash_time_left / SLASH_ACTIVE_TIME)
    slash_progress = max(0.0, min(1.0, slash_progress))

    # Crescent slash that grows then decays over the slash window.
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
    # Carve inside to create a moon/crescent shape.
    pygame.draw.circle(slash_surface, (0, 0, 0, 0), (inner_x, center_y), inner_radius)
    surface.blit(slash_surface, (0, 0))


def make_dust_particles(rect: pygame.Rect) -> list[dict[str, float]]:
    particles: list[dict[str, float]] = []
    for _ in range(DUST_COUNT):
        life = random.uniform(DUST_LIFETIME_MIN, DUST_LIFETIME_MAX)
        particles.append(
            {
                "x": float(random.uniform(rect.left, rect.right)),
                "y": float(random.uniform(rect.top, rect.bottom)),
                "vx": float(random.uniform(-DUST_DRIFT_X, DUST_DRIFT_X)),
                "vy": float(random.uniform(-DUST_DRIFT_Y, DUST_DRIFT_Y * 0.5)),
                "life": float(life),
                "max_life": float(life),
                "size": float(random.uniform(1.5, 4.0)),
            }
        )
    return particles


def update_dust_particles(particles: list[dict[str, float]], dt: float) -> list[dict[str, float]]:
    for particle in particles:
        particle["life"] -= dt
        # Dust drifts and slows down over time.
        particle["vx"] *= 0.985
        particle["vy"] *= 0.985
        particle["x"] += particle["vx"] * dt
        particle["y"] += particle["vy"] * dt
    return [particle for particle in particles if particle["life"] > 0.0]


def draw_dust_particles(surface: pygame.Surface, particles: list[dict[str, float]], color: tuple[int, int, int]) -> None:
    for particle in particles:
        life_ratio = particle["life"] / particle["max_life"]
        alpha = int(200 * life_ratio)
        size = max(1, int(particle["size"] * (0.55 + 0.45 * life_ratio)))
        pygame.draw.circle(
            surface,
            (*color, alpha),
            (int(particle["x"]), int(particle["y"])),
            size,
        )


def make_respawn_particles(rect: pygame.Rect, color: tuple[int, int, int]) -> list[dict[str, float]]:
    particles: list[dict[str, float]] = []
    for _ in range(DUST_COUNT):
        tx = float(random.uniform(rect.left, rect.right))
        ty = float(random.uniform(rect.top, rect.bottom))
        angle = random.uniform(0.0, math.tau)
        dist = random.uniform(36.0, 130.0)
        sx = tx + math.cos(angle) * dist
        sy = ty + math.sin(angle) * dist
        particles.append(
            {
                "sx": sx,
                "sy": sy,
                "tx": tx,
                "ty": ty,
                "life": RESPAWN_ANIM_TIME,
                "max_life": RESPAWN_ANIM_TIME,
                "size": float(random.uniform(1.8, 4.4)),
                "r": float(color[0]),
                "g": float(color[1]),
                "b": float(color[2]),
            }
        )
    return particles


def update_respawn_particles(particles: list[dict[str, float]], dt: float) -> list[dict[str, float]]:
    for particle in particles:
        particle["life"] -= dt
    return [particle for particle in particles if particle["life"] > 0.0]


def draw_respawn_particles(surface: pygame.Surface, particles: list[dict[str, float]]) -> None:
    for particle in particles:
        progress = 1.0 - (particle["life"] / particle["max_life"])
        progress = max(0.0, min(1.0, progress))
        x = particle["sx"] + (particle["tx"] - particle["sx"]) * progress
        y = particle["sy"] + (particle["ty"] - particle["sy"]) * progress
        alpha = int(220 * progress)
        size = max(1, int(particle["size"] * (1.0 - 0.25 * progress)))
        pygame.draw.circle(
            surface,
            (int(particle["r"]), int(particle["g"]), int(particle["b"]), alpha),
            (int(x), int(y)),
            size,
        )


def main() -> None:
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Bomb Bugs - Movement Prototype")
    clock = pygame.time.Clock()
    font = pygame.font.SysFont(None, 32)

    platforms = [
        pygame.Rect(0, HEIGHT - FLOOR_HEIGHT, WIDTH, FLOOR_HEIGHT),
        pygame.Rect(120, 380, 220, 24),
        pygame.Rect(430, 315, 220, 24),
        pygame.Rect(735, 255, 170, 24),
    ]

    player_spawn_x = (WIDTH - SQUARE_SIZE) / 2
    player_spawn_y = platforms[0].top - SQUARE_SIZE
    x = player_spawn_x
    y = player_spawn_y
    velocity_y = 0.0
    is_grounded = True
    player_alive = True
    player_hp = MAX_HP
    player_respawn_timer = 0.0
    player_death_particles: list[dict[str, float]] = []
    player_respawn_particles: list[dict[str, float]] = []

    facing_dir = 1
    dash_dir = 0
    dash_time_left = 0.0
    dash_cooldown_left = 0.0
    dash_trail: list[dict[str, float]] = []
    trail_spawn_timer = 0.0

    player_slash_time_left = 0.0
    player_slash_cooldown_left = 0.0

    enemy_spawn_pos = (680.0, float(platforms[0].top - ENEMY_SIZE))
    enemy_x = enemy_spawn_pos[0]
    enemy_y = enemy_spawn_pos[1]
    enemy_alive = True
    enemy_hp = MAX_HP
    enemy_respawn_timer = 0.0
    enemy_death_particles: list[dict[str, float]] = []
    enemy_respawn_particles: list[dict[str, float]] = []

    enemy_dir = -1
    enemy_facing_dir = -1
    enemy_patrol_min = enemy_spawn_pos[0] - 180
    enemy_patrol_max = enemy_spawn_pos[0] + 180
    enemy_slash_time_left = 0.0
    enemy_slash_cooldown_left = 0.0

    running = True
    while running:
        dt = clock.tick(60) / 1000.0

        # Timers
        dash_time_left = max(0.0, dash_time_left - dt)
        dash_cooldown_left = max(0.0, dash_cooldown_left - dt)
        trail_spawn_timer = max(0.0, trail_spawn_timer - dt)
        player_slash_time_left = max(0.0, player_slash_time_left - dt)
        player_slash_cooldown_left = max(0.0, player_slash_cooldown_left - dt)
        enemy_slash_time_left = max(0.0, enemy_slash_time_left - dt)
        enemy_slash_cooldown_left = max(0.0, enemy_slash_cooldown_left - dt)

        # Particle simulation
        dash_trail = update_dust_particles(dash_trail, dt)
        player_death_particles = update_dust_particles(player_death_particles, dt)
        enemy_death_particles = update_dust_particles(enemy_death_particles, dt)
        player_respawn_particles = update_respawn_particles(player_respawn_particles, dt)
        enemy_respawn_particles = update_respawn_particles(enemy_respawn_particles, dt)

        # Respawn logic: death delay + reverse-dust animation.
        if not player_alive:
            player_respawn_timer = max(0.0, player_respawn_timer - dt)
            if player_respawn_timer <= RESPAWN_ANIM_TIME and not player_respawn_particles:
                spawn_rect = pygame.Rect(int(player_spawn_x), int(player_spawn_y), SQUARE_SIZE, SQUARE_SIZE)
                player_respawn_particles = make_respawn_particles(spawn_rect, SQUARE_COLOR)
            if player_respawn_timer <= 0.0:
                player_alive = True
                player_hp = MAX_HP
                x = player_spawn_x
                y = player_spawn_y
                velocity_y = 0.0
                is_grounded = True
                player_death_particles.clear()
                player_respawn_particles.clear()
                player_slash_time_left = 0.0
                player_slash_cooldown_left = 0.0
                dash_time_left = 0.0

        if not enemy_alive:
            enemy_respawn_timer = max(0.0, enemy_respawn_timer - dt)
            if enemy_respawn_timer <= RESPAWN_ANIM_TIME and not enemy_respawn_particles:
                spawn_rect = pygame.Rect(int(enemy_spawn_pos[0]), int(enemy_spawn_pos[1]), ENEMY_SIZE, ENEMY_SIZE)
                enemy_respawn_particles = make_respawn_particles(spawn_rect, ENEMY_COLOR)
            if enemy_respawn_timer <= 0.0:
                enemy_alive = True
                enemy_hp = MAX_HP
                enemy_x = enemy_spawn_pos[0]
                enemy_y = enemy_spawn_pos[1]
                enemy_death_particles.clear()
                enemy_respawn_particles.clear()
                enemy_slash_time_left = 0.0
                enemy_slash_cooldown_left = 0.0

        # Use fresh rects for current frame interactions.
        player_rect = pygame.Rect(int(x), int(y), SQUARE_SIZE, SQUARE_SIZE)
        enemy_rect = pygame.Rect(int(enemy_x), int(enemy_y), ENEMY_SIZE, ENEMY_SIZE)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN and (
                event.key == pygame.K_SPACE
                or event.key == pygame.K_w
                or event.key == pygame.K_UP
            ):
                if player_alive and is_grounded:
                    velocity_y = JUMP_VELOCITY
                    is_grounded = False
            elif event.type == pygame.KEYDOWN and (
                event.key == pygame.K_LSHIFT or event.key == pygame.K_RSHIFT
            ):
                if player_alive and dash_time_left <= 0.0 and dash_cooldown_left <= 0.0:
                    keys = pygame.key.get_pressed()
                    input_dir = 0
                    if keys[pygame.K_LEFT] or keys[pygame.K_a]:
                        input_dir -= 1
                    if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
                        input_dir += 1
                    dash_dir = input_dir if input_dir != 0 else facing_dir
                    if dash_dir != 0:
                        dash_time_left = DASH_DURATION
                        dash_cooldown_left = DASH_COOLDOWN
                        trail_spawn_timer = 0.0
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if player_alive and player_slash_cooldown_left <= 0.0:
                    player_rect = pygame.Rect(int(x), int(y), SQUARE_SIZE, SQUARE_SIZE)
                    player_slash_rect = build_slash_rect(player_rect, facing_dir)
                    player_slash_time_left = SLASH_ACTIVE_TIME
                    player_slash_cooldown_left = PLAYER_SLASH_COOLDOWN

                    if enemy_alive and player_slash_rect.colliderect(enemy_rect):
                        enemy_hp = max(0, enemy_hp - 1)
                        if enemy_hp == 0:
                            enemy_alive = False
                            enemy_respawn_timer = RESPAWN_DELAY + RESPAWN_ANIM_TIME
                            enemy_death_particles = make_dust_particles(enemy_rect)
                            enemy_respawn_particles.clear()
                            enemy_slash_time_left = 0.0

        keys = pygame.key.get_pressed()

        # Player movement + physics
        if player_alive:
            direction = 0
            if keys[pygame.K_LEFT] or keys[pygame.K_a]:
                direction -= 1
            if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
                direction += 1
            if direction != 0:
                facing_dir = direction

            if dash_time_left > 0.0:
                x += dash_dir * DASH_SPEED * dt
                if trail_spawn_timer <= 0.0:
                    dash_trail.append({"x": x, "y": y, "life": TRAIL_LIFETIME, "max_life": TRAIL_LIFETIME, "vx": 0.0, "vy": 0.0, "size": 12.0})
                    trail_spawn_timer = TRAIL_SPAWN_INTERVAL
            else:
                x += direction * SPEED * dt
            x = max(0, min(x, WIDTH - SQUARE_SIZE))

            previous_bottom = y + SQUARE_SIZE
            velocity_y += GRAVITY * dt
            y += velocity_y * dt
            is_grounded = False

            player_rect = pygame.Rect(int(x), int(y), SQUARE_SIZE, SQUARE_SIZE)
            if velocity_y >= 0:
                landing_top = None
                for platform in platforms:
                    crosses_top = previous_bottom <= platform.top and player_rect.bottom >= platform.top
                    overlaps_x = player_rect.right > platform.left and player_rect.left < platform.right
                    if crosses_top and overlaps_x:
                        if landing_top is None or platform.top < landing_top:
                            landing_top = platform.top
                if landing_top is not None:
                    y = landing_top - SQUARE_SIZE
                    velocity_y = 0.0
                    is_grounded = True

            player_rect = pygame.Rect(int(x), int(y), SQUARE_SIZE, SQUARE_SIZE)

        # Enemy movement + attack AI
        if enemy_alive:
            enemy_x += enemy_dir * ENEMY_SPEED * dt
            if enemy_x < enemy_patrol_min:
                enemy_x = enemy_patrol_min
                enemy_dir = 1
            elif enemy_x > enemy_patrol_max:
                enemy_x = enemy_patrol_max
                enemy_dir = -1

            enemy_rect = pygame.Rect(int(enemy_x), int(enemy_y), ENEMY_SIZE, ENEMY_SIZE)

            if player_alive:
                dx = player_rect.centerx - enemy_rect.centerx
                if abs(dx) > 8:
                    enemy_facing_dir = 1 if dx > 0 else -1

                in_attack_x = abs(dx) <= (SLASH_RANGE_X + 10)
                in_attack_y = abs(player_rect.centery - enemy_rect.centery) <= 70
                if in_attack_x and in_attack_y and enemy_slash_cooldown_left <= 0.0:
                    enemy_slash_rect = build_slash_rect(enemy_rect, enemy_facing_dir)
                    enemy_slash_time_left = SLASH_ACTIVE_TIME
                    enemy_slash_cooldown_left = ENEMY_SLASH_COOLDOWN

                    if player_alive and enemy_slash_rect.colliderect(player_rect):
                        player_hp = max(0, player_hp - 1)
                        if player_hp == 0:
                            player_alive = False
                            player_respawn_timer = RESPAWN_DELAY + RESPAWN_ANIM_TIME
                            player_death_particles = make_dust_particles(player_rect)
                            player_respawn_particles.clear()
                            player_slash_time_left = 0.0
                            dash_time_left = 0.0

        # Render
        screen.fill(BACKGROUND)
        for platform in platforms:
            pygame.draw.rect(screen, PLATFORM_COLOR, platform)

        # Player dash ghost
        for ghost in dash_trail:
            life_ratio = ghost["life"] / ghost["max_life"]
            alpha = int(150 * life_ratio)
            ghost_surface = pygame.Surface((SQUARE_SIZE, SQUARE_SIZE), pygame.SRCALPHA)
            ghost_surface.fill((255, 200, 80, alpha))
            screen.blit(ghost_surface, (int(ghost["x"]), int(ghost["y"])))

        # Alive entities + bars
        if player_alive:
            pygame.draw.rect(screen, SQUARE_COLOR, player_rect)
            draw_health_bar(screen, player_rect, player_hp, MAX_HP)
        if enemy_alive:
            pygame.draw.rect(screen, ENEMY_COLOR, enemy_rect)
            draw_health_bar(screen, enemy_rect, enemy_hp, MAX_HP)

        # Death and respawn FX
        draw_dust_particles(screen, player_death_particles, (170, 150, 130))
        draw_dust_particles(screen, enemy_death_particles, (170, 150, 130))
        draw_respawn_particles(screen, player_respawn_particles)
        draw_respawn_particles(screen, enemy_respawn_particles)

        # Attack FX (same style for both)
        if player_alive and player_slash_time_left > 0.0:
            draw_crescent_slash(screen, player_rect, facing_dir, player_slash_time_left)
        if enemy_alive and enemy_slash_time_left > 0.0:
            draw_crescent_slash(screen, enemy_rect, enemy_facing_dir, enemy_slash_time_left)

        position_text = font.render(f"Cube position: x={int(x)}, y={int(y)}", True, TEXT_COLOR)
        dash_text = font.render(f"Dash cooldown: {dash_cooldown_left:.2f}s", True, TEXT_COLOR)
        slash_text = font.render(f"Player slash cd: {player_slash_cooldown_left:.2f}s", True, TEXT_COLOR)
        enemy_slash_text = font.render(f"Enemy slash cd: {enemy_slash_cooldown_left:.2f}s", True, TEXT_COLOR)
        player_hp_text = font.render(f"Player HP: {player_hp}", True, TEXT_COLOR)
        enemy_hp_text = font.render(f"Enemy HP: {enemy_hp}", True, TEXT_COLOR)
        player_respawn_text = font.render(
            f"Player respawn: {player_respawn_timer:.1f}s" if not player_alive else "Player respawn: ready",
            True,
            TEXT_COLOR,
        )
        enemy_respawn_text = font.render(
            f"Enemy respawn: {enemy_respawn_timer:.1f}s" if not enemy_alive else "Enemy respawn: ready",
            True,
            TEXT_COLOR,
        )
        screen.blit(position_text, (16, 16))
        screen.blit(dash_text, (16, 48))
        screen.blit(slash_text, (16, 80))
        screen.blit(enemy_slash_text, (16, 112))
        screen.blit(player_hp_text, (16, 144))
        screen.blit(enemy_hp_text, (16, 176))
        screen.blit(player_respawn_text, (16, 208))
        screen.blit(enemy_respawn_text, (16, 240))

        pygame.display.flip()

    pygame.quit()
    sys.exit(0)


if __name__ == "__main__":
    main()

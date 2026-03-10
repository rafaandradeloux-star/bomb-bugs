import math
import random

import pygame


def draw_menu_pixel_background(screen: pygame.Surface, title_rect: pygame.Rect) -> None:
    now = pygame.time.get_ticks() / 1000.0
    w = screen.get_width()
    h = screen.get_height()

    # Gentle horizon strips for depth.
    pygame.draw.rect(screen, (164, 221, 250), pygame.Rect(0, int(h * 0.42), w, int(h * 0.22)))
    pygame.draw.rect(screen, (122, 195, 110), pygame.Rect(0, int(h * 0.64), w, int(h * 0.24)))
    pygame.draw.rect(screen, (102, 165, 92), pygame.Rect(0, int(h * 0.85), w, int(h * 0.15)))

    cloud_specs = [
        (1.0, 38, 62, 0.9),
        (1.9, 66, 96, 1.0),
        (2.7, 102, 80, 0.85),
        (3.8, 146, 58, 1.05),
        (4.6, 74, 72, 0.95),
    ]
    for seed, base_y, size, speed in cloud_specs:
        x = int((seed * 230.0 + now * 16.0 * speed) % (w + 160) - 120)
        _draw_pixel_cloud(screen, x, base_y, size=size)
        if x > w - 60:
            _draw_pixel_cloud(screen, x - (w + 160), base_y, size=size)

    tree_specs = [
        (0.0, 0.78, 1.0),
        (0.9, 0.81, 1.1),
        (1.8, 0.79, 0.95),
        (2.9, 0.82, 1.2),
        (3.7, 0.8, 1.05),
        (4.6, 0.84, 1.15),
    ]
    for seed, y_ratio, scale in tree_specs:
        x = int((seed * 210.0 + now * 5.0 * (0.8 + 0.15 * scale)) % (w + 180) - 90)
        y = int(h * y_ratio)
        _draw_pixel_tree(screen, x, y, scale=scale)
        if x > w - 40:
            _draw_pixel_tree(screen, x - (w + 180), y, scale=scale)

    _draw_menu_birds(screen, title_rect)


def _draw_pixel_cloud(screen: pygame.Surface, x: int, y: int, size: int = 80) -> None:
    px = max(2, size // 16)
    c1 = (248, 250, 252)
    c2 = (236, 240, 245)
    c3 = (219, 228, 238)
    chunks = [
        (0, 2, 5, 2, c2),
        (1, 1, 7, 3, c1),
        (3, 0, 6, 3, c1),
        (6, 1, 6, 3, c1),
        (9, 2, 4, 2, c2),
        (2, 3, 8, 2, c3),
    ]
    for cx, cy, cw, ch, color in chunks:
        pygame.draw.rect(screen, color, pygame.Rect(x + cx * px, y + cy * px, cw * px, ch * px))


def _draw_pixel_tree(screen: pygame.Surface, x: int, y: int, scale: float = 1.0) -> None:
    px = max(2, int(4 * scale))
    trunk = (110, 78, 50)
    leaf_dark = (44, 132, 66)
    leaf_mid = (58, 156, 74)
    leaf_light = (82, 182, 96)

    pygame.draw.rect(screen, trunk, pygame.Rect(x + 8 * px, y + 10 * px, 3 * px, 11 * px))

    canopy = [
        (6, 0, 6, 2, leaf_dark),
        (4, 2, 10, 2, leaf_mid),
        (3, 4, 12, 2, leaf_dark),
        (2, 6, 14, 2, leaf_mid),
        (1, 8, 16, 2, leaf_dark),
        (2, 10, 14, 2, leaf_mid),
        (3, 12, 12, 2, leaf_dark),
        (5, 1, 3, 1, leaf_light),
        (10, 1, 3, 1, leaf_light),
        (7, 3, 4, 1, leaf_light),
        (6, 7, 5, 1, leaf_light),
    ]
    for cx, cy, cw, ch, color in canopy:
        pygame.draw.rect(screen, color, pygame.Rect(x + cx * px, y + cy * px, cw * px, ch * px))


def _draw_menu_birds(screen: pygame.Surface, title_rect: pygame.Rect) -> None:
    now = pygame.time.get_ticks() / 1000.0
    birds = _get_menu_birds_state(screen, title_rect, now)
    for bird in birds:
        _update_menu_bird(bird, title_rect, now)
        _draw_pixel_bird(screen, bird, now)


def _get_menu_birds_state(screen: pygame.Surface, title_rect: pygame.Rect, now: float) -> list[dict[str, float]]:
    state = getattr(_draw_menu_birds, "_state", None)
    if state is None:
        state = {
            "last_time": now,
            "next_perch_time": now + 2.8,
            "birds": [],
        }
        w = screen.get_width()
        for i in range(4):
            direction = -1.0 if i % 2 == 0 else 1.0
            start_x = float(w + 40 + i * 70) if direction < 0.0 else float(-60 - i * 70)
            state["birds"].append(
                {
                    "x": start_x,
                    "y": float(42 + i * 26),
                    "base_y": float(42 + i * 26),
                    "world_w": float(w),
                    "vx": float(direction * (34 + i * 8)),
                    "dir": float(direction),
                    "phase": float(i * 1.6),
                    "state": "flying",
                    "target_x": float(title_rect.centerx),
                    "target_y": float(title_rect.top + 12),
                    "perch_timer": 0.0,
                }
            )
        _draw_menu_birds._state = state

    dt = max(0.0, min(0.08, now - float(state["last_time"])))
    state["last_time"] = now

    perched_exists = any(b["state"] == "perched" for b in state["birds"])
    if now >= float(state["next_perch_time"]) and not perched_exists:
        flying_candidates = [b for b in state["birds"] if b["state"] == "flying"]
        if flying_candidates:
            bird = random.choice(flying_candidates)
            bird["state"] = "approach"
            bird["target_x"] = float(random.randint(title_rect.left + 18, title_rect.right - 18))
            bird["target_y"] = float(title_rect.top - random.randint(2, 5))
            bird["perch_timer"] = 0.0
        state["next_perch_time"] = now + random.uniform(3.0, 5.8)

    state["dt"] = dt
    return state["birds"]


def _update_menu_bird(bird: dict[str, float], title_rect: pygame.Rect, now: float) -> None:
    bird_state = str(bird["state"])
    dt = float(getattr(_draw_menu_birds, "_state", {}).get("dt", 0.016))
    world_w = float(bird.get("world_w", 960.0))

    if bird_state == "flying":
        bird["x"] += bird["vx"] * dt
        bird["y"] = bird["base_y"] + math.sin(now * 3.4 + bird["phase"]) * 5.0
        bird["dir"] = 1.0 if bird["vx"] >= 0.0 else -1.0
        if bird["x"] > world_w + 120:
            bird["x"] = -80.0
            bird["base_y"] = float(random.randint(34, 168))
            bird["vx"] = float(-abs(bird["vx"]))
        if bird["x"] < -140:
            bird["x"] = float(world_w + 160)
            bird["base_y"] = float(random.randint(34, 168))
            bird["vx"] = float(abs(bird["vx"]))
        return

    if bird_state == "approach":
        dx = bird["target_x"] - bird["x"]
        dy = bird["target_y"] - bird["y"]
        dist = math.hypot(dx, dy)
        if dist <= 4.0:
            bird["state"] = "perched"
            bird["x"] = bird["target_x"]
            bird["y"] = bird["target_y"]
            bird["perch_timer"] = random.uniform(1.1, 2.0)
            bird["vx"] = 0.0
            return
        bird["dir"] = 1.0 if dx >= 0.0 else -1.0
        speed = max(36.0, min(72.0, abs(float(bird.get("vx", 48.0))) * 1.02))
        step = min(dist, speed * dt)
        if dist > 0.0:
            bird["x"] += (dx / dist) * step
            bird["y"] += (dy / dist) * step
        return

    if bird_state == "perched":
        bird["perch_timer"] -= dt
        if bird["perch_timer"] <= 0.0:
            bird["state"] = "leaving"
            bird["vx"] = random.choice([-1.0, 1.0]) * random.uniform(90.0, 118.0)
            bird["dir"] = 1.0 if bird["vx"] >= 0.0 else -1.0
            bird["base_y"] = float(random.randint(42, 178))
        return

    if bird_state == "leaving":
        bird["x"] += bird["vx"] * dt
        bird["y"] -= 26.0 * dt
        bird["dir"] = 1.0 if bird["vx"] >= 0.0 else -1.0
        if bird["x"] < -120 or bird["x"] > world_w + 140 or bird["y"] < 20:
            bird["state"] = "flying"
            if bird["x"] < 0:
                bird["x"] = float(world_w + 120)
                bird["vx"] = -abs(random.uniform(38.0, 70.0))
            else:
                bird["x"] = -80.0
                bird["vx"] = abs(random.uniform(38.0, 70.0))
            bird["dir"] = 1.0 if bird["vx"] >= 0.0 else -1.0
            bird["base_y"] = float(random.randint(34, 180))


def _draw_pixel_bird(screen: pygame.Surface, bird: dict[str, float], now: float) -> None:
    x = int(bird["x"])
    y = int(bird["y"])
    px = 3
    body = (38, 38, 42)
    wing = (56, 56, 62)
    belly = (214, 214, 220)
    beak = (238, 172, 66)

    perched = str(bird["state"]) == "perched"
    flap_cycle = 0.0 if perched else (0.5 + 0.5 * math.sin(now * 13.0 + bird["phase"]))
    wing_up = flap_cycle > 0.55
    facing = 1 if float(bird.get("dir", 1.0)) >= 0.0 else -1

    pygame.draw.rect(screen, body, pygame.Rect(x, y, 4 * px, 2 * px))
    pygame.draw.rect(screen, belly, pygame.Rect(x + px, y + px, 2 * px, px))

    if wing_up:
        pygame.draw.rect(screen, wing, pygame.Rect(x - px, y - px, 2 * px, px))
        pygame.draw.rect(screen, wing, pygame.Rect(x + 3 * px, y - px, 2 * px, px))
    else:
        pygame.draw.rect(screen, wing, pygame.Rect(x - px, y + px, 2 * px, px))
        pygame.draw.rect(screen, wing, pygame.Rect(x + 3 * px, y + px, 2 * px, px))

    head_x = x + (3 * px if facing > 0 else -px)
    pygame.draw.rect(screen, body, pygame.Rect(head_x, y - px, px, px))
    beak_x = head_x + (px if facing > 0 else -px)
    pygame.draw.rect(screen, beak, pygame.Rect(beak_x, y - px, px, px))

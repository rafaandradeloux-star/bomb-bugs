import sys

import pygame


WIDTH, HEIGHT = 960, 540
BACKGROUND = (135, 206, 235)  # sky blue
SQUARE_COLOR = (255, 200, 80)
TEXT_COLOR = (20, 20, 20)
SQUARE_SIZE = 64
SPEED = 420  # pixels/second
GRAVITY = 1700  # pixels/second^2
JUMP_VELOCITY = -700  # pixels/second
FLOOR_OFFSET = 80
DASH_SPEED = 980  # pixels/second
DASH_DURATION = 0.14  # seconds
DASH_COOLDOWN = 0.45  # seconds


def main() -> None:
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Bomb Bugs - Movement Prototype")
    clock = pygame.time.Clock()
    font = pygame.font.SysFont(None, 32)

    x = (WIDTH - SQUARE_SIZE) / 2
    ground_y = HEIGHT - SQUARE_SIZE - FLOOR_OFFSET
    y = ground_y
    velocity_y = 0.0
    facing_dir = 1
    dash_dir = 0
    dash_time_left = 0.0
    dash_cooldown_left = 0.0

    running = True
    while running:
        dt = clock.tick(60) / 1000.0

        dash_time_left = max(0.0, dash_time_left - dt)
        dash_cooldown_left = max(0.0, dash_cooldown_left - dt)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN and (
                event.key == pygame.K_SPACE
                or event.key == pygame.K_w
                or event.key == pygame.K_UP
            ):
                if y >= ground_y:
                    velocity_y = JUMP_VELOCITY
            elif event.type == pygame.KEYDOWN and (
                event.key == pygame.K_LSHIFT or event.key == pygame.K_RSHIFT
            ):
                if dash_time_left <= 0.0 and dash_cooldown_left <= 0.0:
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

        keys = pygame.key.get_pressed()
        direction = 0
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            direction -= 1
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            direction += 1
        if direction != 0:
            facing_dir = direction

        if dash_time_left > 0.0:
            x += dash_dir * DASH_SPEED * dt
        else:
            x += direction * SPEED * dt
        x = max(0, min(x, WIDTH - SQUARE_SIZE))

        velocity_y += GRAVITY * dt
        y += velocity_y * dt
        if y > ground_y:
            y = ground_y
            velocity_y = 0.0

        screen.fill(BACKGROUND)
        pygame.draw.rect(screen, SQUARE_COLOR, (int(x), int(y), SQUARE_SIZE, SQUARE_SIZE))
        position_text = font.render(f"Cube position: x={int(x)}, y={int(y)}", True, TEXT_COLOR)
        dash_text = font.render(f"Dash cooldown: {dash_cooldown_left:.2f}s", True, TEXT_COLOR)
        screen.blit(position_text, (16, 16))
        screen.blit(dash_text, (16, 48))
        pygame.display.flip()

    pygame.quit()
    sys.exit(0)


if __name__ == "__main__":
    main()

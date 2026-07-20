"""
A Simple Mario-Like Platformer Game
------------------------------------
Built with pygame. Run with: python mario_like_game.py

Controls:
    LEFT / RIGHT ARROW KEYS - Move
    SPACE / UP ARROW        - Jump
    R                       - Restart after Game Over / Win
    ESC                     - Quit
"""

import sys
import pygame

# ----------------------------------------------------------------------
# Global Constants
# ----------------------------------------------------------------------
SCREEN_WIDTH = 900
SCREEN_HEIGHT = 550
FPS = 60

GRAVITY = 0.8
JUMP_STRENGTH = -16
PLAYER_SPEED = 5
MAX_FALL_SPEED = 18

# Colors (R, G, B)
SKY_BLUE = (107, 175, 255)
GROUND_BROWN = (155, 103, 60)
GROUND_GREEN = (86, 168, 76)
PLAYER_RED = (214, 40, 40)
PLAYER_SKIN = (250, 200, 152)
PLAYER_BLUE = (40, 70, 200)
PLATFORM_COLOR = (140, 90, 50)
COIN_YELLOW = (255, 210, 30)
ENEMY_COLOR = (120, 60, 30)
FLAG_POLE_COLOR = (90, 90, 90)
FLAG_COLOR = (230, 30, 30)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
DARK_RED = (150, 20, 20)


# ----------------------------------------------------------------------
# Player Class
# ----------------------------------------------------------------------
class Player:
    """Represents the playable character and handles physics/animation."""

    def __init__(self, x, y):
        self.width = 34
        self.height = 46
        self.rect = pygame.Rect(x, y, self.width, self.height)
        self.vel_x = 0
        self.vel_y = 0
        self.on_ground = False
        self.facing_right = True
        self.alive = True
        self.walk_timer = 0
        self.walk_frame = 0

    def handle_input(self, keys):
        """Reads keyboard state and sets horizontal velocity / jumping."""
        self.vel_x = 0

        if keys[pygame.K_LEFT]:
            self.vel_x = -PLAYER_SPEED
            self.facing_right = False
        if keys[pygame.K_RIGHT]:
            self.vel_x = PLAYER_SPEED
            self.facing_right = True

        if (keys[pygame.K_SPACE] or keys[pygame.K_UP]) and self.on_ground:
            self.vel_y = JUMP_STRENGTH
            self.on_ground = False

    def apply_physics(self):
        """Applies gravity and clamps fall speed."""
        self.vel_y += GRAVITY
        if self.vel_y > MAX_FALL_SPEED:
            self.vel_y = MAX_FALL_SPEED

    def update_animation(self):
        """Cycles a simple walking animation while moving on the ground."""
        if self.vel_x != 0 and self.on_ground:
            self.walk_timer += 1
            if self.walk_timer >= 6:
                self.walk_timer = 0
                self.walk_frame = (self.walk_frame + 1) % 2
        else:
            self.walk_frame = 0

    def draw(self, surface, camera_x):
        """Draws a small blocky character resembling a plumber hero."""
        x = self.rect.x - camera_x
        y = self.rect.y
        leg_offset = 4 if self.walk_frame == 1 else -4

        # Legs
        pygame.draw.rect(surface, PLAYER_BLUE, (x + 4, y + 34 + max(leg_offset, 0), 10, 12))
        pygame.draw.rect(surface, PLAYER_BLUE, (x + 20, y + 34 - min(leg_offset, 0), 10, 12))

        # Body/overalls
        pygame.draw.rect(surface, PLAYER_BLUE, (x + 2, y + 20, self.width - 4, 18))

        # Shirt/arms
        pygame.draw.rect(surface, PLAYER_RED, (x, y + 14, self.width, 10))

        # Head
        pygame.draw.rect(surface, PLAYER_SKIN, (x + 5, y, self.width - 10, 16))

        # Cap
        pygame.draw.rect(surface, PLAYER_RED, (x + 3, y - 6, self.width - 6, 8))
        cap_bill_x = x + self.width - 8 if self.facing_right else x - 2
        pygame.draw.rect(surface, PLAYER_RED, (cap_bill_x, y, 8, 4))


# ----------------------------------------------------------------------
# Platform Class
# ----------------------------------------------------------------------
class Platform:
    """A solid rectangular block the player can stand on."""

    def __init__(self, x, y, width, height, color=PLATFORM_COLOR):
        self.rect = pygame.Rect(x, y, width, height)
        self.color = color

    def draw(self, surface, camera_x):
        pygame.draw.rect(
            surface, self.color,
            (self.rect.x - camera_x, self.rect.y, self.rect.width, self.rect.height)
        )
        pygame.draw.rect(
            surface, BLACK,
            (self.rect.x - camera_x, self.rect.y, self.rect.width, self.rect.height), 2
        )


# ----------------------------------------------------------------------
# Coin Class
# ----------------------------------------------------------------------
class Coin:
    """A collectible coin that adds to the player's score."""

    def __init__(self, x, y):
        self.rect = pygame.Rect(x, y, 18, 18)
        self.collected = False
        self.bob_timer = 0

    def update(self):
        self.bob_timer += 1

    def draw(self, surface, camera_x):
        if self.collected:
            return
        bob = int(3 * pygame.math.Vector2(0, 1).rotate(self.bob_timer * 6).y)
        center = (self.rect.centerx - camera_x, self.rect.centery + bob)
        pygame.draw.circle(surface, COIN_YELLOW, center, 9)
        pygame.draw.circle(surface, BLACK, center, 9, 2)


# ----------------------------------------------------------------------
# Enemy Class
# ----------------------------------------------------------------------
class Enemy:
    """A simple patrolling enemy that moves between two x boundaries."""

    def __init__(self, x, y, left_bound, right_bound, speed=2):
        self.rect = pygame.Rect(x, y, 28, 28)
        self.left_bound = left_bound
        self.right_bound = right_bound
        self.speed = speed
        self.alive = True

    def update(self):
        if not self.alive:
            return
        self.rect.x += self.speed
        if self.rect.left <= self.left_bound or self.rect.right >= self.right_bound:
            self.speed *= -1

    def draw(self, surface, camera_x):
        if not self.alive:
            return
        x = self.rect.x - camera_x
        y = self.rect.y
        pygame.draw.ellipse(surface, ENEMY_COLOR, (x, y, self.rect.width, self.rect.height))
        # Eyes
        pygame.draw.circle(surface, WHITE, (x + 8, y + 10), 4)
        pygame.draw.circle(surface, WHITE, (x + 20, y + 10), 4)
        pygame.draw.circle(surface, BLACK, (x + 8, y + 10), 2)
        pygame.draw.circle(surface, BLACK, (x + 20, y + 10), 2)


# ----------------------------------------------------------------------
# Level Data
# ----------------------------------------------------------------------
def build_level():
    """Constructs and returns all platforms, coins, and enemies for the level."""
    platforms = [
        Platform(0, 500, 2400, 50, GROUND_GREEN),      # Main ground
        Platform(300, 400, 120, 20),
        Platform(500, 340, 120, 20),
        Platform(700, 420, 100, 20),
        Platform(900, 350, 150, 20),
        Platform(1150, 460, 100, 20),
        Platform(1350, 380, 130, 20),
        Platform(1600, 300, 100, 20),
        Platform(1800, 420, 150, 20),
        Platform(2050, 350, 120, 20),
    ]

    coins = [
        Coin(340, 360), Coin(540, 300), Coin(730, 380),
        Coin(950, 310), Coin(1180, 420), Coin(1400, 340),
        Coin(1630, 260), Coin(1840, 380), Coin(2080, 310),
    ]

    enemies = [
        Enemy(600, 470, 550, 850, speed=2),
        Enemy(1200, 470, 1150, 1400, speed=2),
        Enemy(1900, 470, 1800, 2100, speed=3),
    ]

    level_end_x = 2350
    return platforms, coins, enemies, level_end_x


# ----------------------------------------------------------------------
# Collision Helpers
# ----------------------------------------------------------------------
def resolve_horizontal_collisions(player, platforms):
    """Moves player horizontally and resolves collisions with platforms."""
    player.rect.x += player.vel_x
    for platform in platforms:
        if player.rect.colliderect(platform.rect):
            if player.vel_x > 0:
                player.rect.right = platform.rect.left
            elif player.vel_x < 0:
                player.rect.left = platform.rect.right


def resolve_vertical_collisions(player, platforms):
    """Moves player vertically and resolves collisions with platforms."""
    player.rect.y += player.vel_y
    player.on_ground = False
    for platform in platforms:
        if player.rect.colliderect(platform.rect):
            if player.vel_y > 0:
                player.rect.bottom = platform.rect.top
                player.vel_y = 0
                player.on_ground = True
            elif player.vel_y < 0:
                player.rect.top = platform.rect.bottom
                player.vel_y = 0


def check_enemy_collisions(player, enemies):
    """Checks if player stomps an enemy (from above) or dies (from side)."""
    for enemy in enemies:
        if not enemy.alive:
            continue
        if player.rect.colliderect(enemy.rect):
            falling_onto_enemy = player.vel_y > 0 and player.rect.bottom - enemy.rect.top < 20
            if falling_onto_enemy:
                enemy.alive = False
                player.vel_y = JUMP_STRENGTH / 1.5
            else:
                return True  # Player was hit
    return False


def check_coin_collisions(player, coins, score):
    """Checks if the player collects any coins and returns updated score."""
    for coin in coins:
        if not coin.collected and player.rect.colliderect(coin.rect):
            coin.collected = True
            score += 10
    return score


# ----------------------------------------------------------------------
# Drawing Helpers
# ----------------------------------------------------------------------
def draw_background(surface, camera_x):
    """Draws a simple parallax-style sky with clouds and hills."""
    surface.fill(SKY_BLUE)

    # Distant hills (slow parallax)
    hill_offset = camera_x * 0.3
    for i in range(6):
        hx = i * 400 - hill_offset % 400 - 200
        pygame.draw.circle(surface, GROUND_GREEN, (int(hx), 470), 90)

    # Clouds (slower parallax)
    cloud_offset = camera_x * 0.5
    for i in range(8):
        cx = i * 300 - cloud_offset % 300
        cy = 60 + (i % 3) * 40
        pygame.draw.ellipse(surface, WHITE, (cx, cy, 70, 30))
        pygame.draw.ellipse(surface, WHITE, (cx + 20, cy - 10, 60, 30))


def draw_hud(surface, score, font):
    """Draws the score display in the top-left corner."""
    text = font.render(f"Score: {score}", True, WHITE)
    outline = font.render(f"Score: {score}", True, BLACK)
    surface.blit(outline, (22, 22))
    surface.blit(text, (20, 20))


def draw_flag(surface, x, camera_x):
    """Draws the level-end flagpole."""
    pole_x = x - camera_x
    pygame.draw.rect(surface, FLAG_POLE_COLOR, (pole_x, 260, 6, 240))
    pygame.draw.polygon(
        surface, FLAG_COLOR,
        [(pole_x + 6, 265), (pole_x + 40, 280), (pole_x + 6, 295)]
    )


def draw_center_message(surface, lines, font, big_font):
    """Draws a semi-transparent overlay with centered text lines."""
    overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 160))
    surface.blit(overlay, (0, 0))

    total_height = len(lines) * 50
    start_y = SCREEN_HEIGHT // 2 - total_height // 2

    for i, (text, use_big) in enumerate(lines):
        chosen_font = big_font if use_big else font
        rendered = chosen_font.render(text, True, WHITE)
        rect = rendered.get_rect(center=(SCREEN_WIDTH // 2, start_y + i * 50))
        surface.blit(rendered, rect)


# ----------------------------------------------------------------------
# Main Game Loop
# ----------------------------------------------------------------------
def main():
    pygame.init()
    pygame.display.set_caption("Mario-Like Adventure")
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    clock = pygame.time.Clock()

    font = pygame.font.SysFont("arial", 26, bold=True)
    big_font = pygame.font.SysFont("arial", 44, bold=True)

    def new_game():
        """Resets all game state to start a fresh run."""
        platforms, coins, enemies, level_end_x = build_level()
        player = Player(50, 400)
        return {
            "player": player,
            "platforms": platforms,
            "coins": coins,
            "enemies": enemies,
            "level_end_x": level_end_x,
            "score": 0,
            "game_over": False,
            "win": False,
        }

    state = new_game()
    running = True

    while running:
        clock.tick(FPS)

        # -------------------- Event Handling --------------------
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                if event.key == pygame.K_r and (state["game_over"] or state["win"]):
                    state = new_game()

        keys = pygame.key.get_pressed()
        player = state["player"]

        # -------------------- Update --------------------
        if not state["game_over"] and not state["win"]:
            player.handle_input(keys)
            player.apply_physics()

            resolve_horizontal_collisions(player, state["platforms"])
            resolve_vertical_collisions(player, state["platforms"])

            player.update_animation()

            for coin in state["coins"]:
                coin.update()
            for enemy in state["enemies"]:
                enemy.update()

            state["score"] = check_coin_collisions(player, state["coins"], state["score"])

            if check_enemy_collisions(player, state["enemies"]):
                state["game_over"] = True

            if player.rect.top > SCREEN_HEIGHT:
                state["game_over"] = True

            if player.rect.x >= state["level_end_x"]:
                state["win"] = True

        # -------------------- Camera --------------------
        camera_x = max(0, player.rect.centerx - SCREEN_WIDTH // 2)
        camera_x = min(camera_x, state["level_end_x"] + 200 - SCREEN_WIDTH)
        camera_x = max(camera_x, 0)

        # -------------------- Draw --------------------
        draw_background(screen, camera_x)

        for platform in state["platforms"]:
            platform.draw(screen, camera_x)
        for coin in state["coins"]:
            coin.draw(screen, camera_x)
        for enemy in state["enemies"]:
            enemy.draw(screen, camera_x)

        draw_flag(screen, state["level_end_x"], camera_x)
        player.draw(screen, camera_x)
        draw_hud(screen, state["score"], font)

        if state["game_over"]:
            draw_center_message(
                screen,
                [("GAME OVER", True), (f"Final Score: {state['score']}", False),
                 ("Press R to Restart", False)],
                font, big_font
            )
        elif state["win"]:
            draw_center_message(
                screen,
                [("LEVEL COMPLETE!", True), (f"Final Score: {state['score']}", False),
                 ("Press R to Play Again", False)],
                font, big_font
            )

        pygame.display.flip()

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()

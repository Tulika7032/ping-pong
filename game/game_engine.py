import pygame

WHITE = (255, 255, 255)

# Paddle class
class Paddle:
    def __init__(self, x, y, width, height, speed=7):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.speed = speed

    def move(self, dy, screen_height):
        self.y += dy
        if self.y < 0:
            self.y = 0
        elif self.y + self.height > screen_height:
            self.y = screen_height - self.height

    def auto_track(self, ball, screen_height):
        target_y = ball.y + ball.height / 2 - self.height / 2
        if target_y > self.y:
            self.move(min(self.speed, target_y - self.y), screen_height)
        else:
            self.move(max(-self.speed, target_y - self.y), screen_height)

    def rect(self):
        return pygame.Rect(self.x, self.y, self.width, self.height)

# Ball class
class Ball:
    def __init__(self, x, y, width, height, screen_width, screen_height, paddle_hit_sound, wall_bounce_sound):
        self.width = width
        self.height = height
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.paddle_hit_sound = paddle_hit_sound
        self.wall_bounce_sound = wall_bounce_sound
        self.reset(x, y)

    def reset(self, x=None, y=None):
        self.x = x if x is not None else self.screen_width // 2
        self.y = y if y is not None else self.screen_height // 2
        self.velocity_x = 7
        self.velocity_y = 7

    def move(self, player=None, ai=None):
        self.x += self.velocity_x
        self.y += self.velocity_y

        # Bounce top/bottom
        if self.y <= 0 or self.y + self.height >= self.screen_height:
            self.velocity_y *= -1
            self.wall_bounce_sound.play()

        # Paddle collisions
        ball_rect = self.rect()
        if player and ball_rect.colliderect(player.rect()):
            self.velocity_x *= -1
            self.x = player.x + player.width
            self.paddle_hit_sound.play()
        elif ai and ball_rect.colliderect(ai.rect()):
            self.velocity_x *= -1
            self.x = ai.x - self.width
            self.paddle_hit_sound.play()

    def rect(self):
        return pygame.Rect(self.x, self.y, self.width, self.height)


# Game Engine
class GameEngine:
    MENU = 0
    PLAYING = 1
    GAME_OVER = 2

    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.paddle_width = 10
        self.paddle_height = 100

        pygame.mixer.init()
        self.paddle_hit_sound = pygame.mixer.Sound("sounds/paddle_hit.wav")
        self.wall_bounce_sound = pygame.mixer.Sound("sounds/wall_bounce.wav")
        self.score_sound = pygame.mixer.Sound("sounds/score.wav")

        self.player = Paddle(10, height // 2 - 50, self.paddle_width, self.paddle_height)
        self.ai = Paddle(width - 20, height // 2 - 50, self.paddle_width, self.paddle_height)
        self.ball = Ball(width // 2, height // 2, 10, 10, width, height,
                         self.paddle_hit_sound, self.wall_bounce_sound)

        # Series tracking
        self.player_points = 0
        self.ai_points = 0
        self.player_wins = 0
        self.ai_wins = 0

        self.font = pygame.font.SysFont("Arial", 30)
        self.game_state = self.MENU
        self.winner_text = ""
        self.series_target = 5  # Best-of-N default
        self.game_winning_score = 5  # points per game

    def handle_input(self):
        keys = pygame.key.get_pressed()

        # Player movement
        if self.game_state == self.PLAYING:
            if keys[pygame.K_w]:
                self.player.move(-10, self.height)
            if keys[pygame.K_s]:
                self.player.move(10, self.height)

        # Menu / Game over selection
        if self.game_state in [self.MENU, self.GAME_OVER]:
            if keys[pygame.K_3]:
                self.series_target = 2
                self.start_series()
            elif keys[pygame.K_5]:
                self.series_target = 3
                self.start_series()
            elif keys[pygame.K_7]:
                self.series_target = 4
                self.start_series()
            elif keys[pygame.K_ESCAPE]:
                pygame.quit()
                exit()

    def start_series(self):
        self.player_wins = 0
        self.ai_wins = 0
        self.start_game()

    def start_game(self):
        self.player_points = 0
        self.ai_points = 0
        self.ball.reset()
        self.game_state = self.PLAYING
        self.winner_text = ""

    def update(self):
        if self.game_state != self.PLAYING:
            return

        # Move ball
        self.ball.move(self.player, self.ai)

        # Update points
        if self.ball.x <= 0:
            self.ai_points += 1
            self.score_sound.play()
            self.ball.reset()
        elif self.ball.x >= self.width:
            self.player_points += 1
            self.score_sound.play()
            self.ball.reset()

        # Move AI
        self.ai.auto_track(self.ball, self.height)

        # Check game win
        if self.player_points >= self.game_winning_score:
            self.player_wins += 1
            if self.player_wins >= self.series_target:
                self.winner_text = "Player Wins Series!"
                self.game_state = self.GAME_OVER
            else:
                self.start_game()
        elif self.ai_points >= self.game_winning_score:
            self.ai_wins += 1
            if self.ai_wins >= self.series_target:
                self.winner_text = "AI Wins Series!"
                self.game_state = self.GAME_OVER
            else:
                self.start_game()

    def render(self, screen):
        screen.fill((0, 0, 0))

        if self.game_state == self.MENU:
            text = self.font.render("Press 3/5/7 for Best-of-N or ESC to Exit", True, WHITE)
            rect = text.get_rect(center=(self.width // 2, self.height // 2))
            screen.blit(text, rect)

        elif self.game_state == self.PLAYING:
            pygame.draw.rect(screen, WHITE, self.player.rect())
            pygame.draw.rect(screen, WHITE, self.ai.rect())
            pygame.draw.ellipse(screen, WHITE, self.ball.rect())
            pygame.draw.aaline(screen, WHITE, (self.width // 2, 0), (self.width // 2, self.height))

            # Display points (current game) and series wins
            player_text = self.font.render(f"{self.player_points} ({self.player_wins})", True, WHITE)
            ai_text = self.font.render(f"{self.ai_points} ({self.ai_wins})", True, WHITE)
            screen.blit(player_text, (self.width // 4, 20))
            screen.blit(ai_text, (self.width * 3 // 4, 20))

        elif self.game_state == self.GAME_OVER:
            winner_surface = self.font.render(self.winner_text, True, WHITE)
            rect = winner_surface.get_rect(center=(self.width // 2, self.height // 2 - 40))
            screen.blit(winner_surface, rect)

            # Replay menu
            menu_lines = [
                "Press 3 for Best of 3",
                "Press 5 for Best of 5",
                "Press 7 for Best of 7",
                "Press ESC to Exit"
            ]
            for i, line in enumerate(menu_lines):
                text = self.font.render(line, True, WHITE)
                rect = text.get_rect(center=(self.width // 2, self.height // 2 + i * 30 + 20))
                screen.blit(text, rect)

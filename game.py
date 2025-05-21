import pygame
import random
from typing import List
from constants import SYMBOLS, EMOJIS, WEIGHTS, SYMBOL_BY_EMOJI


def random_grid(rows=5, cols=5):
    choose = random.choices
    return [[choose(EMOJIS, WEIGHTS)[0] for _ in range(cols)] for _ in range(rows)]


class Particle:
    def __init__(self, x, y, color):
        self.x = x
        self.y = y
        self.dx = random.uniform(-2, 2)
        self.dy = random.uniform(-2, 2)
        self.color = color
        self.life = 255
        self.size = random.randint(2, 4)

    def update(self):
        self.x += self.dx
        self.y += self.dy
        self.life -= 5
        return self.life > 0

    def draw(self, screen):
        alpha = max(0, min(255, self.life))
        s = pygame.Surface((self.size * 2, self.size * 2))
        s.set_alpha(alpha)
        s.fill(self.color)
        screen.blit(s, (self.x - self.size, self.y - self.size))


class Game:
    def __init__(self) -> None:
        pygame.init()
        pygame.mixer.init()

        self.screen = pygame.display.set_mode((1200, 800))
        pygame.display.set_caption("Slot Machine")
        self.emoji_font = pygame.font.Font("./assets/fonts/NotoColorEmoji.ttf", 64)
        self.info_font = pygame.font.Font("./assets/fonts/Orbitron Black.ttf", 24)
        self.small_font = pygame.font.Font("./assets/fonts/Orbitron Black.ttf", 16)

        self.grid_rows = 5
        self.grid_cols = 5
        self.cell_size = 110
        self.padding = 12
        self.grid_draw_left = 50

        grid_actual_height = (
            self.grid_rows * (self.cell_size + self.padding) - self.padding
        )
        self.grid_draw_top = (self.screen.get_height() - grid_actual_height) // 2

        try:
            self.spin_sound = pygame.mixer.Sound("./assets/sounds/spin.wav")
            self.win_sound = pygame.mixer.Sound("./assets/sounds/win.wav")
        except pygame.error as e:
            print(f"Warning: Could not load sound files: {e}")
            self.spin_sound = None
            self.win_sound = None

        self.grid = random_grid(rows=self.grid_rows, cols=self.grid_cols)
        self.credits = 1000
        self.message = ""

        self.spinning = False
        self.spin_start_time = 0
        self.spin_duration = 2000
        self.spin_frames = 0
        self.max_spin_frames = 15
        self.winning_grid = None
        self.win_patterns = []
        self.animation_alpha = 0
        self.animation_direction = 1

        self.particles: List[Particle] = []

        self.btn_spin = pygame.Rect(800, 100, 150, 60)
        self.check_force = pygame.Rect(800, 200, 30, 30)
        self.force_win = False

        self.show_paytable = False
        self.btn_paytable = pygame.Rect(800, 420, 150, 40)

    def generate_particles(self, x, y, color):
        for _ in range(20):
            self.particles.append(Particle(x, y, color))

    def update_particles(self):
        self.particles = [p for p in self.particles if p.update()]

    def draw_particles(self):
        for p in self.particles:
            p.draw(self.screen)

    def render_paytable(self):
        table_bg_rect = pygame.Rect(780, 450, 400, 320)
        pygame.draw.rect(self.screen, (25, 28, 35), table_bg_rect, border_radius=15)
        pygame.draw.rect(self.screen, (40, 45, 55), table_bg_rect, 2, border_radius=15)

        title_text = self.info_font.render("PAYTABLE", True, (255, 215, 0))
        title_rect = title_text.get_rect(
            center=(table_bg_rect.centerx, table_bg_rect.top + 30)
        )
        self.screen.blit(title_text, title_rect)

        start_y = table_bg_rect.top + 70
        row_height = 35
        x_symbol_name = table_bg_rect.left + 30
        x_value_text = table_bg_rect.right - 30

        for i, symbol_data in enumerate(reversed(SYMBOLS)):
            current_y = start_y + i * row_height

            name_surf = self.small_font.render(symbol_data.name, True, (180, 185, 200))
            name_rect = name_surf.get_rect(
                midleft=(x_symbol_name, current_y + row_height // 2)
            )
            self.screen.blit(name_surf, name_rect)

            value_str = f"{symbol_data.base:<2d} x2(3) x5(4)"
            value_surf = self.small_font.render(value_str, True, (180, 185, 200))
            value_rect = value_surf.get_rect(
                midright=(x_value_text, current_y + row_height // 2)
            )
            self.screen.blit(value_surf, value_rect)

    def run(self):
        clock = pygame.time.Clock()
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                if event.type == pygame.KEYDOWN and not self.spinning:
                    if event.key == pygame.K_ESCAPE:
                        running = False
                    if event.key == pygame.K_f:
                        self.force_win = not self.force_win
                    if event.key == pygame.K_SPACE:
                        self.trigger_spin()
                    if event.key == pygame.K_p:
                        self.show_paytable = not self.show_paytable

                if event.type == pygame.MOUSEBUTTONDOWN and not self.spinning:
                    mx, my = event.pos
                    if self.btn_spin.collidepoint(mx, my):
                        self.trigger_spin()
                    if self.check_force.collidepoint(mx, my):
                        self.force_win = not self.force_win
                    if self.btn_paytable.collidepoint(mx, my):
                        self.show_paytable = not self.show_paytable

            if not self.spinning:
                self.update_win_animation()
            else:
                self.update_spin_animation()

            self.update_particles()

            self.screen.fill("black")
            self.draw_grid()
            self.draw_particles()
            self.draw_ui()
            pygame.display.flip()
            clock.tick(60)
        pygame.quit()

    def update_win_animation(self):
        if self.win_patterns:
            self.animation_alpha += self.animation_direction * 3
            if self.animation_alpha >= 180:
                self.animation_direction = -1
            elif self.animation_alpha <= 30:
                self.animation_direction = 1

    def draw_grid(self):
        grid_width = self.grid_cols * (self.cell_size + self.padding) - self.padding
        grid_height = self.grid_rows * (self.cell_size + self.padding) - self.padding

        left = self.grid_draw_left
        top = self.grid_draw_top

        grid_bg = pygame.Rect(left - 20, top - 20, grid_width + 40, grid_height + 40)
        pygame.draw.rect(self.screen, (30, 30, 30), grid_bg, border_radius=15)
        pygame.draw.rect(self.screen, (50, 50, 50), grid_bg, 2, border_radius=15)

        for r, row in enumerate(self.grid):
            for c, emoji in enumerate(row):
                x = left + c * (self.cell_size + self.padding)
                y = top + r * (self.cell_size + self.padding)
                rect = pygame.Rect(x, y, self.cell_size, self.cell_size)

                pygame.draw.rect(self.screen, (25, 25, 25), rect, border_radius=10)

                cell_in_win = False
                win_color = (30, 30, 30)

                for pattern_type, win_row, win_col, size in self.win_patterns:
                    if pattern_type in ("horizontal", "vertical"):
                        if pattern_type == "horizontal" and r == win_row:
                            if win_col <= c < win_col + size:
                                cell_in_win = True
                                win_color = (0, 255, 0, self.animation_alpha)
                        elif pattern_type == "vertical" and c == win_col:
                            if win_row <= r < win_row + size:
                                cell_in_win = True
                                win_color = (0, 255, 0, self.animation_alpha)
                    elif pattern_type == "block":
                        if win_row <= r < win_row + 2 and win_col <= c < win_col + 2:
                            cell_in_win = True
                            win_color = (255, 215, 0, self.animation_alpha)

                if cell_in_win:
                    s = pygame.Surface((self.cell_size, self.cell_size), pygame.SRCALPHA)
                    s.fill(win_color)
                    self.screen.blit(s, rect)

                pygame.draw.rect(self.screen, (45, 45, 45), rect, 2, border_radius=10)

                temp_surf = self.emoji_font.render(emoji, True, (255, 255, 255))

                desired_emoji_height = 48
                aspect_ratio = temp_surf.get_width() / temp_surf.get_height()
                scaled_width = int(desired_emoji_height * aspect_ratio)

                scaled_surf = pygame.transform.smoothscale(
                    temp_surf, (scaled_width, desired_emoji_height)
                )

                self.screen.blit(scaled_surf, scaled_surf.get_rect(center=rect.center))

    def draw_ui(self):
        button_color = (
            (60, 180, 60)
            if self.btn_spin.collidepoint(pygame.mouse.get_pos())
            else (50, 150, 50)
        )
        pygame.draw.rect(self.screen, button_color, self.btn_spin, border_radius=15)
        pygame.draw.rect(self.screen, (80, 200, 80), self.btn_spin, 2, border_radius=15)
        spin_text = self.info_font.render("SPIN", True, (255, 255, 255))
        self.screen.blit(spin_text, spin_text.get_rect(center=self.btn_spin.center))

        space_text = self.info_font.render("Press SPACE", True, (150, 150, 150))
        self.screen.blit(
            space_text,
            space_text.get_rect(
                center=(self.btn_spin.centerx, self.btn_spin.bottom + 25)
            ),
        )

        pygame.draw.rect(self.screen, (40, 40, 40), self.check_force, border_radius=5)
        pygame.draw.rect(
            self.screen, (80, 80, 80), self.check_force, 1, border_radius=5
        )
        if self.force_win:
            smaller_rect = self.check_force.inflate(-8, -8)
            pygame.draw.rect(self.screen, (80, 200, 80), smaller_rect, border_radius=3)

        force_text = self.info_font.render("Force Win (F)", True, (150, 150, 150))
        self.screen.blit(
            force_text, (self.check_force.right + 15, self.check_force.centery - 12)
        )

        credits_bg = pygame.Rect(780, 280, 200, 50)
        pygame.draw.rect(self.screen, (30, 30, 30), credits_bg, border_radius=10)
        pygame.draw.rect(self.screen, (50, 50, 50), credits_bg, 2, border_radius=10)

        credits_text = self.info_font.render(
            f"Credits: {self.credits}", True, (255, 255, 255)
        )
        self.screen.blit(credits_text, credits_text.get_rect(center=credits_bg.center))

        if self.message:
            msg_color = (255, 255, 0) if "won" in self.message else (150, 150, 150)
            msg_bg = pygame.Rect(780, 350, 200, 50)
            pygame.draw.rect(self.screen, (30, 30, 30), msg_bg, border_radius=10)
            pygame.draw.rect(self.screen, (50, 50, 50), msg_bg, 2, border_radius=10)

            msg_text = self.info_font.render(self.message, True, msg_color)
            self.screen.blit(msg_text, msg_text.get_rect(center=msg_bg.center))

        button_color = (60, 100, 180) if self.show_paytable else (40, 80, 150)
        pygame.draw.rect(self.screen, button_color, self.btn_paytable, border_radius=10)
        pygame.draw.rect(
            self.screen, (80, 120, 200), self.btn_paytable, 2, border_radius=10
        )
        paytable_text = self.small_font.render("PAYTABLE", True, (255, 255, 255))
        self.screen.blit(
            paytable_text, paytable_text.get_rect(center=self.btn_paytable.center)
        )

        if self.show_paytable:
            self.render_paytable()

    def trigger_spin(self):
        if self.spinning:
            return

        if self.credits < 10:
            self.message = "Not enough credits!"
            return

        if self.spin_sound:
            self.spin_sound.play()

        self.credits -= 10
        self.spinning = True
        self.spin_start_time = pygame.time.get_ticks()
        self.message = ""
        self.win_patterns = []

        self.winning_grid = self.generate_winning_grid() if self.force_win else None

    def update_spin_animation(self):
        current_time = pygame.time.get_ticks()
        time_elapsed = current_time - self.spin_start_time

        if time_elapsed < self.spin_duration:
            self.spin_frames += 1
            if self.spin_frames % 4 == 0:
                self.grid = random_grid(rows=self.grid_rows, cols=self.grid_cols)
        else:
            self.spinning = False
            if self.winning_grid:
                self.grid = self.winning_grid
            else:
                self.grid = random_grid(rows=self.grid_rows, cols=self.grid_cols)

            self.win_patterns = self.check_wins()
            payout = self.calculate_payout()
            if payout > 0:
                self.credits += payout
                self.message = f"You won {payout} credits!"
                if self.win_sound:
                    self.win_sound.play()
                for pattern_type, row, col, _ in self.win_patterns:
                    cell_plus_padding = self.cell_size + self.padding
                    particle_x = (
                        self.grid_draw_left
                        + col * cell_plus_padding
                        + self.cell_size // 2
                    )
                    particle_y = (
                        self.grid_draw_top
                        + row * cell_plus_padding
                        + self.cell_size // 2
                    )
                    color = (
                        (0, 255, 0)
                        if pattern_type in ("horizontal", "vertical")
                        else (255, 215, 0)
                    )
                    self.generate_particles(particle_x, particle_y, color)
            else:
                self.message = "Try again!"

    def generate_winning_grid(self):
        grid = random_grid(rows=self.grid_rows, cols=self.grid_cols)
        symbol = "\U0001f352"
        if self.grid_rows > 0:
            grid[0] = [symbol] * self.grid_cols
        return grid

    def check_wins(self):
        patterns = []

        for row in range(self.grid_rows):
            line = self.grid[row]
            for col in range(self.grid_cols):
                if col <= 0 and len(set(line[col : col + 5])) == 1:
                    patterns.append(("horizontal", row, col, 5))
                elif col <= 1 and len(set(line[col : col + 4])) == 1:
                    patterns.append(("horizontal", row, col, 4))
                elif col <= 2 and len(set(line[col : col + 3])) == 1:
                    patterns.append(("horizontal", row, col, 3))

        for col in range(self.grid_cols):
            column = [self.grid[r][col] for r in range(self.grid_rows)]
            for row in range(self.grid_rows):
                if row <= 0 and len(set(column[row : row + 5])) == 1:
                    patterns.append(("vertical", row, col, 5))
                elif row <= 1 and len(set(column[row : row + 4])) == 1:
                    patterns.append(("vertical", row, col, 4))
                elif row <= 2 and len(set(column[row : row + 3])) == 1:
                    patterns.append(("vertical", row, col, 3))

        for row in range(self.grid_rows - 1):
            for col in range(self.grid_cols - 1):
                block = [
                    self.grid[row][col],
                    self.grid[row][col + 1],
                    self.grid[row + 1][col],
                    self.grid[row + 1][col + 1],
                ]
                if len(set(block)) == 1:
                    patterns.append(("block", row, col, 2))

        return patterns

    def calculate_payout(self):
        if not self.win_patterns:
            return 0

        total_payout = 0
        for pattern_type, row, col, size in self.win_patterns:
            symbol = self.grid[row][col]
            base_value = SYMBOL_BY_EMOJI[symbol].base

            multiplier = 1
            if pattern_type in ("horizontal", "vertical"):
                if size == 3:
                    multiplier = 2
                elif size == 4:
                    multiplier = 5
                elif size == 5:
                    multiplier = 10
            elif pattern_type == "block":
                multiplier = 3

            total_payout += base_value * multiplier

        return total_payout


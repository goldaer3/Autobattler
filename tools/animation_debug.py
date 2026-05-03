import pygame
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from assets.units.bot_animation import SpritesheetAnimator, BotAnimationController, get_anims

WHITE = (255, 255, 255)
BLACK = (20, 20, 30)
GRAY = (100, 100, 100)
GREEN = (0, 255, 0)
RED = (255, 60, 60)
BLUE = (60, 150, 255)
YELLOW = (255, 255, 80)


def load_knight_anims():
    ASSETS_DIR = Path(__file__).resolve().parent.parent / "assets" / "units" / "Knight"
    return {
        "idle": SpritesheetAnimator(ASSETS_DIR / "__Idle.gif", fps=8, frame_width=120, frame_height=80, target_size=0, orientation="horizontal"),
        "move": SpritesheetAnimator(ASSETS_DIR / "__Run.gif", fps=12, frame_width=120, frame_height=80, target_size=0, orientation="horizontal"),
        "attack": SpritesheetAnimator(ASSETS_DIR / "__Attack.gif", fps=12, frame_width=120, frame_height=80, target_size=0, orientation="horizontal"),
        "attack2": SpritesheetAnimator(ASSETS_DIR / "__Attack2.gif", fps=12, frame_width=120, frame_height=80, target_size=0, orientation="horizontal"),
        "attack_no_move": SpritesheetAnimator(ASSETS_DIR / "__AttackNoMovement.gif", fps=12, frame_width=120, frame_height=80, target_size=0, orientation="horizontal"),
        "attack_combo": SpritesheetAnimator(ASSETS_DIR / "__AttackComboNoMovement.gif", fps=12, frame_width=120, frame_height=80, target_size=0, orientation="horizontal"),
        "hurt": SpritesheetAnimator(ASSETS_DIR / "__Hit.gif", fps=15, frame_width=120, frame_height=80, target_size=0, orientation="horizontal"),
        "death": SpritesheetAnimator(ASSETS_DIR / "__Death.gif", fps=6, frame_width=120, frame_height=80, target_size=0, orientation="horizontal"),
        "jump": SpritesheetAnimator(ASSETS_DIR / "__Jump.gif", fps=12, frame_width=120, frame_height=80, target_size=0, orientation="horizontal"),
        "fall": SpritesheetAnimator(ASSETS_DIR / "__Fall.gif", fps=8, frame_width=120, frame_height=80, target_size=0, orientation="horizontal"),
        "roll": SpritesheetAnimator(ASSETS_DIR / "__Roll.gif", fps=12, frame_width=120, frame_height=80, target_size=0, orientation="horizontal"),
        "dash": SpritesheetAnimator(ASSETS_DIR / "__Dash.gif", fps=15, frame_width=120, frame_height=80, target_size=0, orientation="horizontal"),
        "crouch": SpritesheetAnimator(ASSETS_DIR / "__Crouch.gif", fps=8, frame_width=120, frame_height=80, target_size=0, orientation="horizontal"),
        "crouch_walk": SpritesheetAnimator(ASSETS_DIR / "__CrouchWalk.gif", fps=8, frame_width=120, frame_height=80, target_size=0, orientation="horizontal"),
        "crouch_attack": SpritesheetAnimator(ASSETS_DIR / "__CrouchAttack.gif", fps=12, frame_width=120, frame_height=80, target_size=0, orientation="horizontal"),
    }


def load_bot_anims():
    ASSETS_DIR = Path(__file__).resolve().parent.parent / "assets" / "units" / "Bot Wheel"
    return {
        "idle": SpritesheetAnimator(ASSETS_DIR / "static idle.png", fps=5, target_size=60),
        "move": SpritesheetAnimator(ASSETS_DIR / "move with FX.png", fps=6, target_size=60),
        "shoot": SpritesheetAnimator(ASSETS_DIR / "shoot with FX.png", fps=12, target_size=60),
        "charge": SpritesheetAnimator(ASSETS_DIR / "charge.png", fps=8, target_size=60),
        "dash": SpritesheetAnimator(ASSETS_DIR / "GAS dash with FX.png", fps=15, target_size=60),
        "damage": SpritesheetAnimator(ASSETS_DIR / "damaged.png", fps=15, target_size=60),
        "death": SpritesheetAnimator(ASSETS_DIR / "death.png", fps=6, target_size=60),
        "wake": SpritesheetAnimator(ASSETS_DIR / "wake.png", fps=8, target_size=60),
    }


UNIT_TYPES = {
    "1": ("Knight", load_knight_anims),
    "2": ("Bot Wheel", load_bot_anims),
}


class AnimationDebugTool:
    def __init__(self, screen):
        self.screen = screen
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 28)
        self.title_font = pygame.font.Font(None, 36)
        
        self._load_anims("1")
        self._setup_controls()

    def _load_anims(self, unit_key):
        self.current_unit_key = unit_key
        unit_name, loader = UNIT_TYPES[unit_key]
        self.unit_name = unit_name
        self.anims = loader()
        self.anim_names = list(self.anims.keys())
        self.current_anim_idx = 0
        self.current_anim_name = self.anim_names[self.current_anim_idx]
        
        self.controller = BotAnimationController.__new__(BotAnimationController)
        self.controller._anims = self.anims
        self.controller._current_anim_name = self.current_anim_name
        self.controller._current_anim = self.anims.get(self.current_anim_name)
        self.controller._frame = 0
        self.controller._frame_timer = 0.0
        self.controller._status_frame_duration = None
        self.controller._loop = True
        self.controller._finished = False

    def _setup_controls(self):
        self.playing = True
        self.show_sheet = False
        self.scale = 4
        self.show_grid = True
        self.running = True

    def _handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
                return False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.running = False
                    return False
                elif event.key == pygame.K_F9:
                    self.running = False
                    return False
                elif event.key in (pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4, pygame.K_5, pygame.K_6, pygame.K_7, pygame.K_8, pygame.K_9):
                    key = chr(event.key)
                    if key in UNIT_TYPES:
                        self._load_anims(key)
                self._handle_keydown(event.key)
        
        if self.playing:
            dt = self.clock.tick(60) / 1000.0
            self.controller.update(dt)
        
        return self.running

    def _handle_keydown(self, key):
        if key == pygame.K_SPACE:
            self.playing = not self.playing
        elif key == pygame.K_TAB:
            self.show_sheet = not self.show_sheet
        elif key == pygame.K_g:
            self.show_grid = not self.show_grid
        elif key == pygame.K_r:
            self.controller.reset()
        elif key == pygame.K_q:
            self.scale = 1
        elif key == pygame.K_w:
            self.scale = 2
        elif key == pygame.K_e:
            self.scale = 3
        elif key == pygame.K_t:
            self.scale = 4
        elif key == pygame.K_y:
            self.scale = 5
        elif key == pygame.K_LEFT:
            self.current_anim_idx = (self.current_anim_idx - 1) % len(self.anim_names)
            self._switch_anim()
        elif key == pygame.K_RIGHT:
            self.current_anim_idx = (self.current_anim_idx + 1) % len(self.anim_names)
            self._switch_anim()
        elif key == pygame.K_UP:
            self.current_anim_idx = (self.current_anim_idx - 5) % len(self.anim_names)
            self._switch_anim()
        elif key == pygame.K_DOWN:
            self.current_anim_idx = (self.current_anim_idx + 5) % len(self.anim_names)
            self._switch_anim()

    def _switch_anim(self):
        self.current_anim_name = self.anim_names[self.current_anim_idx]
        loop = self.current_anim_name not in ("death",)
        self.controller.set_animation(self.current_anim_name, loop=loop)

    def _draw(self):
        overlay = pygame.Surface((900, 700), pygame.SRCALPHA)
        overlay.fill((20, 20, 30, 220))
        self.screen.blit(overlay, (0, 0))

        title = self.title_font.render(f"Animation Debug - {self.unit_name}", True, WHITE)
        self.screen.blit(title, (20, 20))

        anim = self.anims[self.current_anim_name]
        info_lines = [
            f"Unit: {self.unit_name} ({self.current_unit_key})",
            f"Animation: {self.current_anim_name}",
            f"Frame: {self.controller._frame + 1}/{anim.frame_count}",
            f"FPS: {anim.fps}",
            f"Frame size: {anim.frame_width}x{anim.frame_height}",
            f"Target size: {anim.target_size}",
            f"Playing: {self.playing}",
        ]

        y = 60
        for line in info_lines:
            text = self.font.render(line, True, GREEN if self.playing else RED)
            self.screen.blit(text, (20, y))
            y += 26

        unit_type_lines = ["", "UNIT TYPES:"]
        for key, (name, _) in UNIT_TYPES.items():
            unit_type_lines.append(f"  {key}: {name}")
        
        controls = [
            "",
            "CONTROLS:",
            "  1-2: Switch unit type",
            "  LEFT/RIGHT: Prev/Next animation",
            "  SPACE: Play/Pause",
            "  R: Reset animation",
            "  G: Toggle grid view",
            "  Q-T: Set scale 1-5",
            "  ESC/F9: Exit debug",
        ]
        
        for line in unit_type_lines + controls:
            text = self.font.render(line, True, YELLOW if line.startswith("  ") else GRAY)
            self.screen.blit(text, (20, y))
            y += 22

        frame = self.controller.current_frame
        if frame:
            scaled = pygame.transform.scale(frame, (frame.get_width() * self.scale, frame.get_height() * self.scale))
            self.screen.blit(scaled, (450, 100))

        if self.show_grid:
            self._draw_grid()

    def _draw_grid(self):
        grid_x, grid_y = 20, 420
        label = self.font.render(f"All Animations ({len(self.anim_names)} total) - green=current", True, WHITE)
        self.screen.blit(label, (grid_x, grid_y - 25))

        cols = 5
        for i, name in enumerate(self.anim_names):
            col = i % cols
            row = i // cols

            x = grid_x + col * 170
            y = grid_y + row * 100

            if x + 160 > 890 or y + 90 > 690:
                continue

            anim = self.anims[name]
            frame = anim.get_frame(0)

            if name == self.current_anim_name:
                pygame.draw.rect(self.screen, GREEN, (x - 2, y - 2, 164, 84), 2)

            if frame:
                scaled = pygame.transform.scale(frame, (80, 80))
                self.screen.blit(scaled, (x + 40, y))

            name_text = self.font.render(name, True, WHITE if name == self.current_anim_name else GRAY)
            self.screen.blit(name_text, (x, y + 82))


if __name__ == "__main__":
    pygame.init()
    screen = pygame.display.set_mode((900, 700))
    tool = AnimationDebugTool(screen)
    while tool._handle_events():
        tool._draw()
        pygame.display.flip()
    pygame.quit()
    sys.exit()
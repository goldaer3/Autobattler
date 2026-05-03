import pygame
from pathlib import Path

ASSETS_DIR = Path(__file__).resolve().parent.parent.parent / "assets" / "units" / "Bot Wheel"

_bot_anims = None

def _get_anims():
    global _bot_anims
    if _bot_anims is None:
        try:
            pygame.init()
        except:
            pass
        _bot_anims = {
            "idle": SpritesheetAnimator("static idle.png", fps=5, target_size=60),
            "move": SpritesheetAnimator("move with FX.png", fps=10, target_size=60),
            "shoot": SpritesheetAnimator("shoot with FX.png", fps=12, target_size=60),
            "charge": SpritesheetAnimator("charge.png", fps=8, target_size=60),
            "dash": SpritesheetAnimator("GAS dash with FX.png", fps=15, target_size=60),
            "damage": SpritesheetAnimator("damaged.png", fps=15, target_size=60),
            "death": SpritesheetAnimator("death.png", fps=6, target_size=60),
            "wake": SpritesheetAnimator("wake.png", fps=8, target_size=60),
        }
    return _bot_anims


class SpritesheetAnimator:
    def __init__(self, filename, frame_width=32, fps=10, target_size=60):
        image_path = ASSETS_DIR / filename
        self.sheet = pygame.image.load(image_path).convert_alpha()
        
        self.frame_width = frame_width
        self.frame_height = 26
        self.target_size = target_size
        
        self.frame_count = self.sheet.get_height() // self.frame_height
            
        self.fps = fps
        self.frame_duration = 1.0 / fps
        self.frame_timer = 0.0
        self.current_frame = 0
        
        self._cache = {}
    
    def _crop_to_bounds(self, surface):
        w, h = surface.get_size()
        if w == 0 or h == 0:
            return surface
        
        min_x, min_y = w, h
        max_x, max_y = 0, 0
        
        for y in range(h):
            for x in range(w):
                if surface.get_at((x, y))[3] > 0:
                    min_x, min_y = min(min_x, x), min(min_y, y)
                    max_x, max_y = max(max_x, x), max(max_y, y)
        
        if max_x < min_x or max_y < min_y:
            return surface
        
        return surface.subsurface((min_x, min_y, max_x - min_x + 1, max_y - min_y + 1))
    
    def _extract_frame(self, index):
        if index in self._cache:
            return self._cache[index]
        
        col = 0
        row = index
        
        frame = pygame.Surface((self.frame_width, self.frame_height), pygame.SRCALPHA)
        frame.blit(self.sheet, (0, 0), (
            col * self.frame_width,
            row * self.frame_height,
            self.frame_width,
            self.frame_height
        ))
        
        cropped = self._crop_to_bounds(frame)
        w, h = cropped.get_size()
        
        max_dim = max(w, h)
        scale = self.target_size / max_dim if max_dim > 0 else 1.0
        
        if scale != 1.0:
            new_w = int(w * scale)
            new_h = int(h * scale)
            cropped = pygame.transform.scale(cropped, (new_w, new_h))
        
        self._cache[index] = cropped
        return cropped
    
    def get_frame(self, index):
        return self._extract_frame(index % self.frame_count)
    
    def update(self, dt):
        self.frame_timer += dt
        if self.frame_timer >= self.frame_duration:
            self.frame_timer = 0
            self.current_frame = (self.current_frame + 1) % self.frame_count
        return self.current_frame
    
    def reset(self):
        self.current_frame = 0
        self.frame_timer = 0


def get_anims():
    return _get_anims()


class BotAnimationController:
    def __init__(self, anim_name="idle"):
        self._anims = _get_anims()
        self._current_anim_name = anim_name
        self._current_anim = self._anims.get(anim_name)
        self._frame = 0
        self._loop = True
        self._finished = False
    
    @property
    def current_frame(self):
        return self._current_anim.get_frame(self._frame)
    
    def set_animation(self, name, loop=True):
        if name != self._current_anim_name and name in self._anims:
            self._current_anim_name = name
            self._current_anim = self._anims[name]
            self._frame = 0
            self._loop = loop
            self._finished = False
            self._current_anim.reset()
    
    def update(self, dt):
        if self._current_anim is None:
            return self._frame
        
        if not self._loop and self._finished:
            return self._frame
        
        prev_frame = self._frame
        self._frame = self._current_anim.update(dt)
        
        if not self._loop and self._frame == 0 and prev_frame > 0:
            self._finished = True
            self._frame = prev_frame
        
        return self._frame
    
    def reset(self):
        self._frame = 0
        self._finished = False
        if self._current_anim:
            self._current_anim.reset()


if __name__ == "__main__":
    pygame.init()
    screen = pygame.display.set_mode((640, 480))
    clock = pygame.time.Clock()
    
    controller = BotAnimationController("move")
    
    running = True
    while running:
        dt = clock.tick(60) / 1000.0
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_1:
                    controller.set_animation("idle")
                elif event.key == pygame.K_2:
                    controller.set_animation("move")
                elif event.key == pygame.K_3:
                    controller.set_animation("shoot")
                elif event.key == pygame.K_4:
                    controller.set_animation("charge")
                elif event.key == pygame.K_5:
                    controller.set_animation("damage")
                elif event.key == pygame.K_6:
                    controller.set_animation("death", loop=False)
                elif event.key == pygame.K_7:
                    controller.set_animation("wake", loop=False)
        
        controller.update(dt)
        
        screen.fill((20, 20, 40))
        screen.blit(controller.current_frame, (320, 240))
        
        font = pygame.font.SysFont(None, 24)
        text = font.render(f"Anim: {controller._current_anim_name} (press 1-7)", True, (200, 200, 200))
        screen.blit(text, (10, 10))
        
        pygame.display.flip()
    
    pygame.quit()
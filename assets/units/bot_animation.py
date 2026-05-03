import pygame
from pathlib import Path

ASSETS_DIR = Path(__file__).resolve().parent.parent.parent / "assets" / "units"

_bot_anims = None
_knight_anims = None

def _get_bot_anims():
    global _bot_anims
    if _bot_anims is None:
        try:
            pygame.init()
        except:
            pass
        bot_dir = ASSETS_DIR / "Bot Wheel"
        _bot_anims = {
            "idle": SpritesheetAnimator(bot_dir / "static idle.png", fps=5, target_size=0),
            "move": SpritesheetAnimator(bot_dir / "move with FX.png", fps=6, target_size=0),
            "shoot": SpritesheetAnimator(bot_dir / "shoot with FX.png", fps=12, target_size=0),
            "charge": SpritesheetAnimator(bot_dir / "charge.png", fps=8, target_size=0),
            "dash": SpritesheetAnimator(bot_dir / "GAS dash with FX.png", fps=15, target_size=0),
            "damage": SpritesheetAnimator(bot_dir / "damaged.png", fps=15, target_size=0),
            "death": SpritesheetAnimator(bot_dir / "death.png", fps=6, target_size=0),
            "wake": SpritesheetAnimator(bot_dir / "wake.png", fps=8, target_size=0),
        }
        for anim in _bot_anims.values():
            anim._cache.clear()
    return _bot_anims

def _get_knight_anims():
    global _knight_anims
    if _knight_anims is None:
        try:
            pygame.init()
        except:
            pass
        knight_dir = ASSETS_DIR / "Knight"
        _knight_anims = {
            "idle": SpritesheetAnimator(knight_dir / "__Idle.gif", fps=8, frame_width=120, frame_height=80, target_size=0, orientation="horizontal"),
            "move": SpritesheetAnimator(knight_dir / "__Run.gif", fps=12, frame_width=120, frame_height=80, target_size=0, orientation="horizontal"),
            "attack": SpritesheetAnimator(knight_dir / "__Attack.gif", fps=12, frame_width=120, frame_height=80, target_size=0, orientation="horizontal"),
            "attack2": SpritesheetAnimator(knight_dir / "__Attack2.gif", fps=12, frame_width=120, frame_height=80, target_size=0, orientation="horizontal"),
            "hurt": SpritesheetAnimator(knight_dir / "__Hit.gif", fps=15, frame_width=120, frame_height=80, target_size=0, orientation="horizontal"),
            "death": SpritesheetAnimator(knight_dir / "__Death.gif", fps=6, frame_width=120, frame_height=80, target_size=0, orientation="horizontal"),
        }
        for anim in _knight_anims.values():
            anim._cache.clear()
    return _knight_anims

ANIM_MAPPING = {
    "bot_wheel": _get_bot_anims,
    "knight": _get_knight_anims,
}

def get_anims(unit_type):
    loader = ANIM_MAPPING.get(unit_type)
    if loader:
        return loader()
    return _get_bot_anims()


class SpritesheetAnimator:
    def __init__(self, image_path, frame_width=32, frame_height=26, fps=10, target_size=80, orientation="vertical"):
        if isinstance(image_path, str):
            image_path = Path(image_path)

        is_gif = str(image_path).lower().endswith('.gif')

        if is_gif:
            try:
                from PIL import Image
                pil_img = Image.open(image_path)
                n_frames = min(pil_img.n_frames, 20)
                sheet_width = pil_img.width
                sheet_height = pil_img.height
                frame_width = sheet_width
                frame_height = sheet_height

                self.sheet = pygame.Surface((sheet_width * n_frames, sheet_height), pygame.SRCALPHA)
                for i in range(n_frames):
                    try:
                        pil_img.seek(i)
                        frame = pil_img.convert('RGBA')
                        pygame_frame = pygame.image.fromstring(frame.tobytes(), frame.size, frame.mode)
                        self.sheet.blit(pygame_frame, (i * sheet_width, 0))
                    except Exception:
                        break
                pil_img.close()
                self._gif_frames = n_frames
                self._sheet_width = sheet_width
                
                temp_frame = pygame.Surface((frame_width, frame_height), pygame.SRCALPHA)
                temp_frame.blit(self.sheet, (0, 0), (0, 0, frame_width, frame_height))
                
                min_y = frame_height
                max_y = 0
                for y in range(frame_height):
                    for x in range(frame_width):
                        if temp_frame.get_at((x, y))[3] > 0:
                            min_y = min(min_y, y)
                            max_y = max(max_y, y)
                
                self._base_crop_y = min_y
                self._base_crop_h = max_y - min_y + 1 if max_y >= min_y else frame_height
            except Exception as e:
                print(f"Warning: Failed to load GIF {image_path}: {e}")
                self.sheet = pygame.Surface((frame_width, frame_height), pygame.SRCALPHA)
                self._gif_frames = 1
                self._base_crop_y = 0
                self._base_crop_h = frame_height
        else:
            self.sheet = pygame.image.load(image_path).convert_alpha()
            self._gif_frames = None
            self._sheet_width = None
            
            self._base_crop_y = 0
            self._base_crop_h = frame_height

        self.frame_width = frame_width
        self.frame_height = frame_height
        self.target_size = target_size
        self.orientation = orientation
        self.is_death = "death" in str(image_path).lower()

        if is_gif:
            self.frame_count = self._gif_frames if self._gif_frames else 1
        elif orientation == "vertical":
            self.frame_count = self.sheet.get_height() // self.frame_height
        else:
            sheet_width = self.sheet.get_width()
            self.frame_count = sheet_width // self.frame_width

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

        actual_index = index % self.frame_count

        if self.orientation == "vertical":
            col = 0
            row = actual_index
            frame_w = self.frame_width
            offset_x = 0
        else:
            col = actual_index
            row = 0
            frame_w = self.frame_width
            offset_x = col * (self._sheet_width or self.frame_width)

        frame = pygame.Surface((frame_w, self.frame_height), pygame.SRCALPHA)
        frame.blit(self.sheet, (0, 0), (
            offset_x,
            row * self.frame_height,
            frame_w,
            self.frame_height
        ))

        min_x, min_y = frame_w, self.frame_height
        max_x, max_y = 0, 0
        for y in range(self.frame_height):
            for x in range(frame_w):
                if frame.get_at((x, y))[3] > 0:
                    min_x = min(min_x, x)
                    min_y = min(min_y, y)
                    max_x = max(max_x, x)
                    max_y = max(max_y, y)

        

        if max_x >= min_x and max_y >= min_y:
            is_gif = self._gif_frames is not None and self._gif_frames > 1

            if is_gif:
                cropped_h = self._base_crop_h
                cropped = pygame.Surface((frame_w, cropped_h), pygame.SRCALPHA)
                cropped.blit(frame, (0, -self._base_crop_y))
                self._cache[index] = cropped
                return cropped

            cropped_w = max_x - min_x + 1
            cropped_h = max_y - min_y + 1
            cropped = pygame.Surface((cropped_w, cropped_h), pygame.SRCALPHA)
            cropped.blit(frame, (-min_x, -min_y))

            self._cache[index] = cropped
            return cropped

        self._cache[index] = frame
        return frame
    
    def get_frame(self, index):
        return self._extract_frame(index % self.frame_count)
    
    def update(self, dt):
        self.frame_timer += dt
        if self.frame_timer >= self.frame_duration:
            self.frame_timer -= self.frame_duration
            self.current_frame = (self.current_frame + 1) % self.frame_count
        return self.current_frame
    
    def reset(self):
        self.current_frame = 0
        self.frame_timer = 0


def get_anims(unit_type=None):
    if unit_type:
        return ANIM_MAPPING.get(unit_type, _get_bot_anims)()
    return _get_bot_anims()


class BotAnimationController:
    def __init__(self, anim_name="idle", unit_type="bot_wheel"):
        self._anims = get_anims(unit_type)
        self._current_anim_name = anim_name
        self._current_anim = self._anims.get(anim_name)
        self._frame = 0
        self._frame_timer = 0.0
        self._status_frame_duration = None
        self._loop = True
        self._finished = False
    
    @property
    def finished(self):
        return self._finished
    
    @property
    def current_frame(self):
        return self._current_anim.get_frame(self._frame) if self._current_anim else None
    
    def set_animation(self, name, loop=True, status_duration=None):
        if name != self._current_anim_name and name in self._anims:
            self._current_anim_name = name
            self._current_anim = self._anims[name]
            self._frame = 0
            self._frame_timer = 0.0
            self._loop = loop
            self._finished = False
            if status_duration and self._current_anim.frame_count > 0:
                self._status_frame_duration = status_duration / self._current_anim.frame_count
            else:
                self._status_frame_duration = None
    
    def update(self, dt):
        if self._current_anim is None:
            return self._frame
        
        if not self._loop and self._finished:
            return self._frame
        
        self._frame_timer += dt
        frame_duration = self._status_frame_duration or self._current_anim.frame_duration
        if self._frame_timer >= frame_duration:
            self._frame_timer -= frame_duration
            prev_frame = self._frame
            self._frame = (self._frame + 1) % self._current_anim.frame_count
            
            if not self._loop and self._frame < prev_frame:
                self._finished = True
                self._frame = prev_frame
        
        return self._frame
    
    def reset(self):
        self._frame = 0
        self._frame_timer = 0.0
        self._finished = False


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
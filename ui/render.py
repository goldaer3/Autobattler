# ui/render.py
import pygame
from config import (
    SCREEN_W, SCREEN_H, ARENA_W, ARENA_H,
    GRID_SZ, COLORS, DEBUG,
    BOTTOM_PANEL_H
)
from ui.panel import draw_info_section, draw_catalog_section
def init():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_W, SCREEN_H), pygame.FULLSCREEN | pygame.SCALED)
    pygame.display.set_caption("Autobattler Top-Down")
    clock = pygame.time.Clock()
    font = pygame.font.SysFont("consolas", 20, bold=True)
    big_font = pygame.font.SysFont("consolas", 28, bold=True)
    return screen, clock, font, big_font

def draw_arena(screen, arena_h=None):
    if arena_h is None:
        arena_h = ARENA_H
    screen.fill(COLORS["bg"])
    for y in range(arena_h):
        ratio = y / arena_h
        r = int(20 * (1 - ratio) + 10 * ratio)
        g = int(20 * (1 - ratio) + 15 * ratio)
        b = int(50 * (1 - ratio) + 25 * ratio)
        pygame.draw.line(screen, (r, g, b), (0, y), (ARENA_W, y))

    # Draw grid
    grid_color = (40, 40, 70)
    for col in range(1, ARENA_W // GRID_SZ):
        x = col * GRID_SZ
        pygame.draw.line(screen, grid_color, (x, 0), (x, arena_h), 1)

    for row in range(1, arena_h // GRID_SZ):
        y = row * GRID_SZ
        pygame.draw.line(screen, grid_color, (0, y), (ARENA_W, y), 1)

    # Draw team dividing line
    mid_x = ARENA_W // 2
    pygame.draw.line(screen, COLORS["accent"], (mid_x, 0), (mid_x, arena_h), 3)

    pygame.draw.rect(screen, (200, 200, 220), (0, 0, ARENA_W, arena_h), 3)

def draw_unit(screen, unit, font):
    sx, sy = int(unit.x), int(unit.y)
    w, h = 0, 0
    
    if unit.sprite:
        w, h = unit.sprite.get_size()
        screen.blit(unit.sprite, (sx - w // 2, sy - h // 2))
    
    if not unit.alive:
        return
    
    hp_w, hp_h = 40, 6
    hp_x, hp_y = sx - hp_w // 2, sy - GRID_SZ // 2 - 12
    
    hp_color = COLORS["hp_bar_fill"] if unit.team == "A" else (80, 150, 255)
    
    pygame.draw.rect(screen, COLORS["hp_bar_bg"], (hp_x, hp_y, hp_w, hp_h))
    hp_ratio = unit.current_hp / unit.hp if unit.hp > 0 else 0
    pygame.draw.rect(screen, hp_color, (hp_x, hp_y, int(hp_w * hp_ratio), hp_h))
    
    if unit.has_status("stun"):
        pygame.draw.circle(screen, (150, 150, 150), (sx, hp_y - 10), 6)
    
    if unit.has_status("fear"):
        pygame.draw.circle(screen, (180, 100, 220), (sx, hp_y - 10), 6)
    
    if DEBUG:
        name_text = font.render(unit.name[:6], True, COLORS["text"])
        screen.blit(name_text, (sx - name_text.get_width() // 2, sy - GRID_SZ // 2 - 30))

def draw_bottom_panel(screen, font, big_font, battle_info=None, wave=1, gold=0, state_hint="", units_db=None, catalog_scroll=0, selected_data=None):
    panel_y = ARENA_H
    panel_h = BOTTOM_PANEL_H
    
    pygame.draw.rect(screen, (20, 20, 40), (0, panel_y, SCREEN_W, panel_h))
    pygame.draw.line(screen, COLORS["accent"], (0, panel_y), (SCREEN_W, panel_y), 3)
    
    from ui.panel import INFO_W
    pygame.draw.line(screen, COLORS["accent"], (INFO_W, panel_y), (INFO_W, panel_y + panel_h), 2)
    
    draw_info_section(screen, font, big_font, battle_info, wave, gold, state_hint, selected_data)
    draw_catalog_section(screen, units_db, catalog_scroll, selected_data)

def draw_minimap(screen, units):
    m_w, m_h = 200, 120
    m_x, m_y = SCREEN_W - m_w - 20, 20
    
    pygame.draw.rect(screen, (10, 10, 20), (m_x, m_y, m_w, m_h), 2)
    pygame.draw.rect(screen, (20, 20, 35), (m_x, m_y, m_w, m_h))
    
    sx = m_w / ARENA_W
    sy = m_h / ARENA_H
    
    mid = m_x + m_w // 2
    pygame.draw.line(screen, (60, 60, 90), (mid, m_y), (mid, m_y + m_h))
    
    for u in units:
        if not u.alive:
            continue
        dx = m_x + u.x * sx
        dy = m_y + u.y * sy
        color = COLORS["team_a_indicator"] if u.team == "A" else COLORS["team_b_indicator"]
        pygame.draw.circle(screen, color, (int(dx), int(dy)), 4)

def draw_catalog(screen, units_db, scroll, selected_data):
    cat_y = ARENA_H
    cat_h = CATALOG_H
    
    pygame.draw.rect(screen, COLORS["catalog_bg"], (0, cat_y, SCREEN_W, cat_h))
    pygame.draw.line(screen, COLORS["accent"], (0, cat_y), (SCREEN_W, cat_y), 2)
    
    unit_w = 60
    unit_h = 60
    spacing = 10
    start_x = 20 - scroll
    start_y = cat_y + (cat_h - unit_h) // 2
    
    font = pygame.font.SysFont("consolas", 12, bold=True)
    
    for i, (uid, udata) in enumerate(units_db.items()):
        x = start_x + i * (unit_w + spacing)
        if x < -unit_w or x > SCREEN_W:
            continue
        
        rect = pygame.Rect(x, start_y, unit_w, unit_h)
        mouse_pos = pygame.mouse.get_pos()
        
        color = COLORS["text"]
        if selected_data and selected_data["id"] == uid:
            color = COLORS["accent"]
            pygame.draw.rect(screen, COLORS["selection_highlight"], rect, 3)
        
        pygame.draw.rect(screen, (30, 30, 50), rect)
        pygame.draw.rect(screen, color, rect, 2)
        
        text = font.render(uid[:5], True, COLORS["text"])
        screen.blit(text, (x + 2, start_y + unit_h - 18))

def draw_placement_preview(screen, unit_data, x, y, color, team="A"):
    try:
        from assets.units.bot_animation import BotAnimationController
        unit_type = unit_data.get("id", "bot_wheel")
        anim = BotAnimationController("idle", unit_type=unit_type)
        frame = anim.current_frame
        if frame:
            frame = frame.copy()
            frame.set_alpha(150)
            if team == "B":
                frame = pygame.transform.flip(frame, True, False)
            screen.blit(frame, (x - frame.get_width() // 2, y - frame.get_height() // 2))
            return
    except Exception as e:
        pass

    size = GRID_SZ - 20
    preview = pygame.Surface((size, size), pygame.SRCALPHA)

    team_color = COLORS["team_a_indicator"] if team == "A" else COLORS["team_b_indicator"]
    pygame.draw.circle(preview, (*team_color, 128), (size // 2, size // 2), size // 2)

    if len(color) == 4:
        pygame.draw.circle(preview, color, (size // 2, size // 2), size // 2, 2)
    else:
        pygame.draw.circle(preview, (*color, 200), (size // 2, size // 2), size // 2, 2)

    if team == "B":
        preview = pygame.transform.flip(preview, True, False)

    screen.blit(preview, (x - size // 2, y - size // 2))

def draw_projectiles(screen, projectiles):
    for p in projectiles:
        w, h = p.size if hasattr(p, 'size') else (10, 4)
        
        if getattr(p, 'is_ball', False):
            radius = max(w, h) // 2
            pygame.draw.circle(screen, p.color, (int(p.x), int(p.y)), radius)
            pygame.draw.circle(screen, (255, 255, 255), (int(p.x - radius//3), int(p.y - radius//3)), radius//3)
        else:
            angle = 0
            if p.dir_x != 0 or p.dir_y != 0:
                import math
                angle = math.degrees(math.atan2(-p.dir_y, p.dir_x))
            
            surf = pygame.Surface((w, h), pygame.SRCALPHA)
            pygame.draw.rect(surf, p.color, (0, 0, w, h))
            
            rotated = pygame.transform.rotate(surf, angle)
            rect = rotated.get_rect(center=(int(p.x), int(p.y)))
            screen.blit(rotated, rect.topleft)
# ui/render.py
import pygame
from config import (
    SCREEN_W, SCREEN_H, ARENA_W, ARENA_H,
    GRID_SZ, GRID_COLS, GRID_ROWS, COLORS, DEBUG,
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

def draw_arena(screen):
    screen.fill(COLORS["bg"])
    for y in range(ARENA_H):
        ratio = y / ARENA_H
        r = int(20 * (1 - ratio) + 10 * ratio)
        g = int(20 * (1 - ratio) + 15 * ratio)
        b = int(50 * (1 - ratio) + 25 * ratio)
        pygame.draw.line(screen, (r, g, b), (0, y), (ARENA_W, y))
    
    for col in range(GRID_COLS + 1):
        x = col * GRID_SZ
        color = (50, 50, 80, 80) if col != GRID_COLS // 2 else (100, 100, 150, 150)
        pygame.draw.line(screen, color, (x, 0), (x, ARENA_H))
    
    for row in range(GRID_ROWS + 1):
        y = row * GRID_SZ
        pygame.draw.line(screen, (50, 50, 80, 80), (0, y), (ARENA_W, y))
    
    mid_x = ARENA_W // 2
    
    for col in range(GRID_COLS // 2 - 1):
        for row in range(GRID_ROWS):
            rect = pygame.Rect(col * GRID_SZ, row * GRID_SZ, GRID_SZ, GRID_SZ)
            pygame.draw.rect(screen, (*COLORS["team_a_indicator"], 30), rect)
    
    for col in range(GRID_COLS // 2 + 1, GRID_COLS):
        for row in range(GRID_ROWS):
            rect = pygame.Rect(col * GRID_SZ, row * GRID_SZ, GRID_SZ, GRID_SZ)
            pygame.draw.rect(screen, (*COLORS["team_b_indicator"], 30), rect)
    
    pygame.draw.line(screen, COLORS["accent"], (mid_x, 0), (mid_x, ARENA_H), 3)

def draw_unit(screen, unit, font):
    sx, sy = int(unit.x), int(unit.y)
    w, h = 0, 0
    
    if unit.sprite:
        w, h = unit.sprite.get_size()
        screen.blit(unit.sprite, (sx - w // 2, sy - h // 2))
    else:
        size = GRID_SZ - 20
        unit_color = getattr(unit, 'color', (200, 200, 200))
        team_color = COLORS["team_a_indicator"] if unit.team == "A" else COLORS["team_b_indicator"]
        pygame.draw.circle(screen, unit_color, (sx, sy), size // 2)
        pygame.draw.circle(screen, COLORS["text"], (sx, sy), size // 2, 2)
    
    hp_w, hp_h = 40, 6
    hp_x, hp_y = sx - hp_w // 2, sy - GRID_SZ // 2 - 12
    
    hp_color = COLORS["hp_bar_fill"] if unit.team == "A" else (80, 150, 255)
    
    pygame.draw.rect(screen, COLORS["hp_bar_bg"], (hp_x, hp_y, hp_w, hp_h))
    hp_ratio = unit.current_hp / unit.hp if unit.hp > 0 else 0
    pygame.draw.rect(screen, hp_color, (hp_x, hp_y, int(hp_w * hp_ratio), hp_h))
    
    team_color = COLORS["team_a_indicator"] if unit.team == "A" else COLORS["team_b_indicator"]
    pygame.draw.ellipse(screen, (*team_color, 180), (sx - 4, sy + GRID_SZ // 2 + 5, 8, 8))
    
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
        if unit_data.get("id") == "bot_wheel":
            anim = BotAnimationController("idle")
            frame = anim.current_frame
            if frame:
                frame = frame.copy()
                frame.set_alpha(150)
                screen.blit(frame, (x - frame.get_width() // 2, y - frame.get_height() // 2))
                return
    except:
        pass
    
    size = GRID_SZ - 20
    preview = pygame.Surface((size, size), pygame.SRCALPHA)
    
    team_color = COLORS["team_a_indicator"] if team == "A" else COLORS["team_b_indicator"]
    pygame.draw.circle(preview, (*team_color, 128), (size // 2, size // 2), size // 2)
    
    if len(color) == 4:
        pygame.draw.circle(preview, color, (size // 2, size // 2), size // 2, 2)
    else:
        pygame.draw.circle(preview, (*color, 200), (size // 2, size // 2), size // 2, 2)
    
    screen.blit(preview, (x - size // 2, y - size // 2))

def draw_projectiles(screen, projectiles):
    for p in projectiles:
        color = p.color if len(p.color) == 3 else p.color[:3]
        pygame.draw.circle(screen, color, (int(p.x), int(p.y)), 8)
        pygame.draw.circle(screen, (255, 255, 255), (int(p.x), int(p.y)), 8, 2)
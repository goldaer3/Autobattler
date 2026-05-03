# ui/panel.py
import pygame
from config import SCREEN_W, ARENA_H, BOTTOM_PANEL_H, COLORS, DEBUG
from assets.units.bot_animation import get_anims

INFO_W = 350

def get_catalog_bounds():
    return INFO_W + 20, ARENA_H + 10, SCREEN_W - INFO_W - 40, BOTTOM_PANEL_H - 20

def draw_info_section(screen, font, big_font, battle_info=None, wave=1, gold=0, state_hint="", selected_data=None):
    panel_y = ARENA_H
    
    wave_text = big_font.render(f"Wave: {wave}", True, COLORS["text"])
    screen.blit(wave_text, (20, panel_y + 15))
    
    gold_text = font.render(f"Gold: {gold}", True, COLORS["accent"])
    screen.blit(gold_text, (140, panel_y + 20))
    
    if state_hint:
        state_text = big_font.render(state_hint, True, COLORS["accent"])
        screen.blit(state_text, (20, panel_y + 50))
    
    if battle_info:
        s_a = battle_info.get('survivors_a', 0)
        s_b = battle_info.get('survivors_b', 0)
        winner = battle_info.get('winner', 'draw')
        winner_txt = f"Team {winner}" if winner != 'draw' else "Draw"
        res_text = big_font.render(f"Winner: {winner_txt}  A: {s_a}  B: {s_b}", True, COLORS["text"])
        screen.blit(res_text, (20, panel_y + 85))
    else:
        hint = font.render("[ENTER] Next  |  [R] Reset  |  Scroll: Wheel", True, (180, 180, 200))
        screen.blit(hint, (20, panel_y + 120))
    
    if DEBUG:
        dbg = font.render("DEBUG", True, COLORS["accent"])
        screen.blit(dbg, (20, panel_y + 145))

def draw_catalog_section(screen, units_db, scroll, selected_data):
    if not units_db:
        return
    
    cat_x, cat_y, cat_w, cat_h = get_catalog_bounds()
    
    font_small = pygame.font.SysFont("consolas", 11, bold=True)
    
    unit_frames = {}
    
    for uid, udata in units_db.items():
        try:
            unit_type = uid if uid != "knight" else "knight"
            anims = get_anims(unit_type)
            move_anim = anims.get("move")
            if move_anim:
                unit_frames[uid] = move_anim.get_frame(0)
            else:
                idle_anim = anims.get("idle")
                if idle_anim:
                    unit_frames[uid] = idle_anim.get_frame(0)
        except:
            unit_frames[uid] = None
    
    for i, (uid, udata) in enumerate(units_db.items()):
        x = cat_x + 10 + i * 70 - scroll
        if x < cat_x or x > cat_x + cat_w:
            continue
        
        rect = pygame.Rect(x, cat_y, 60, 60)
        
        is_selected = selected_data and selected_data["id"] == uid
        
        if is_selected:
            pygame.draw.rect(screen, COLORS["accent"], rect, 3)
        else:
            pygame.draw.rect(screen, (40, 40, 60), rect, 2)
        
        frame = unit_frames.get(uid)
        if frame:
            frame = pygame.transform.scale(frame, (50, 50))
            screen.blit(frame, (x + 5, cat_y + 5))
        else:
            color = udata.get("color", [100, 100, 100])
            pygame.draw.rect(screen, color, rect)
        
        text = font_small.render(uid[:6], True, (255, 255, 255))
        screen.blit(text, (x + 2, cat_y + 62))

def hit_test_catalog(mx, my, units_db, scroll):
    cat_x, cat_y, cat_w, cat_h = get_catalog_bounds()
    
    if mx < cat_x or mx > cat_x + cat_w or my < cat_y or my > cat_y + cat_h:
        return None
    
    for i, uid in enumerate(units_db.keys()):
        x = cat_x + 10 + i * 70 - scroll
        if mx >= x and mx < x + 60:
            return uid
    return None
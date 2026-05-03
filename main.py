# main.py
import pygame
import sys
import random
from config import ARENA_W, ARENA_H, BATTLE_ARENA_H, GRID_SZ, GRID_COLS, GRID_ROWS, COLORS, FPS, DEBUG, BOTTOM_PANEL_H
from core.units import load_units_from_yaml, create_unit_from_data_v2 as create_unit_from_data
from core.battle import BattleEngine
from ui.render import init, draw_arena, draw_unit, draw_minimap, draw_placement_preview, draw_bottom_panel, draw_projectiles
from ui.panel import hit_test_catalog
from enum import Enum, auto
from tools.animation_debug import AnimationDebugTool

class GameState(Enum):
    DEPLOY = auto()
    BATTLE = auto()
    POST_BATTLE = auto()

def main():
    screen, clock, font, big_font = init()
    units_db = load_units_from_yaml()
    print(f"Loaded {len(units_db)} units: {list(units_db.keys())}")
    
    all_unit_ids = list(units_db.keys())
    random.shuffle(all_unit_ids)
    half = len(all_unit_ids) // 2
    
    team_a_ids = all_unit_ids[:half]
    team_b_ids = all_unit_ids[half:]
    
    team_a = []
    team_b = []
    
    state = GameState.DEPLOY
    current_arena_h = ARENA_H
    panel_visible = True
    battle_engine = None
    battle_result = None
    wave = 1
    gold = 0
    running = True
    
    selected_unit_data = None
    catalog_scroll = 0
    
    anim_debug = None
    anim_debug_active = False
    
    mx, my = 0, 0
    
    while running:
        dt = clock.tick(FPS) / 1000.0
        mx, my = pygame.mouse.get_pos()
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                
                if event.key == pygame.K_h:
                    panel_visible = not panel_visible
                
                if event.key == pygame.K_F9:
                    if not anim_debug_active:
                        anim_debug = AnimationDebugTool(screen)
                        anim_debug_active = True
                    else:
                        anim_debug = None
                        anim_debug_active = False
                
                if event.key == pygame.K_RETURN:
                    if state == GameState.DEPLOY:
                        if team_a and team_b:
                            state = GameState.BATTLE
                            current_arena_h = BATTLE_ARENA_H
                            battle_engine = BattleEngine(team_a, team_b, ARENA_W, BATTLE_ARENA_H)
                    elif state == GameState.POST_BATTLE:
                        wave += 1
                        gold += 50
                        team_a = []
                        team_b = []
                        random.shuffle(all_unit_ids)
                        team_a_ids = all_unit_ids[:len(all_unit_ids)//2]
                        team_b_ids = all_unit_ids[len(all_unit_ids)//2:]
                        state = GameState.DEPLOY
                        current_arena_h = ARENA_H
                        battle_engine = None
                        battle_result = None

                if event.key == pygame.K_r:
                    team_a, team_b = [], []
                    state = GameState.DEPLOY
                    current_arena_h = ARENA_H
                    battle_engine = None
                    battle_result = None
                    wave = 1
                    gold = 0
                
                if state == GameState.DEPLOY:
                    if event.key == pygame.K_1:
                        unit_ids_list = list(units_db.keys())
                        if len(unit_ids_list) > 0:
                            selected_unit_data = units_db[unit_ids_list[0]].copy()
                    elif event.key == pygame.K_2:
                        unit_ids_list = list(units_db.keys())
                        if len(unit_ids_list) > 1:
                            selected_unit_data = units_db[unit_ids_list[1]].copy()
                    elif event.key == pygame.K_3:
                        unit_ids_list = list(units_db.keys())
                        if len(unit_ids_list) > 2:
                            selected_unit_data = units_db[unit_ids_list[2]].copy()
                    elif event.key == pygame.K_4:
                        unit_ids_list = list(units_db.keys())
                        if len(unit_ids_list) > 3:
                            selected_unit_data = units_db[unit_ids_list[3]].copy()

            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 4:
                    catalog_scroll = max(0, catalog_scroll - 20)
                elif event.button == 5:
                    catalog_scroll += 20
                
                elif event.button == 1:
                    if panel_visible:
                        hit_uid = hit_test_catalog(mx, my, units_db, catalog_scroll)
                        if hit_uid:
                            selected_unit_data = units_db[hit_uid].copy()
                    if my < display_arena_h and selected_unit_data and state == GameState.DEPLOY:
                        team = "A" if mx < ARENA_W // 2 else "B"
                        unit = create_unit_from_data(selected_unit_data, team, mx, my)
                        if team == "A":
                            team_a.append(unit)
                        else:
                            team_b.append(unit)

        if state == GameState.BATTLE and battle_engine:
            if not battle_engine.step(dt):
                battle_result = battle_engine.run_simulation(dt)
                state = GameState.POST_BATTLE
                battle_engine = None
                for unit in team_a + team_b:
                    if hasattr(unit, '_anim') and unit._anim:
                        unit._anim.set_animation("death", loop=False)
        elif state == GameState.DEPLOY:
            for unit in team_a + team_b:
                if hasattr(unit, 'update_sprite'):
                    unit.update_sprite(dt, None)
        elif state == GameState.POST_BATTLE:
            anims_finished = True
            for unit in team_a + team_b:
                if hasattr(unit, '_anim') and unit._anim:
                    unit._anim.update(dt)
                    if unit._anim._finished:
                        continue
                    anims_finished = False

        display_arena_h = BATTLE_ARENA_H if not panel_visible else current_arena_h

        screen.fill(COLORS["bg"])
        draw_arena(screen, display_arena_h)

        for unit in team_a + team_b:
            draw_unit(screen, unit, font)

        if battle_engine and battle_engine.projectiles:
            draw_projectiles(screen, battle_engine.projectiles)

        if selected_unit_data and my < display_arena_h and state == GameState.DEPLOY:
            preview_team = "A" if mx < ARENA_W // 2 else "B"
            draw_placement_preview(screen, selected_unit_data, mx, my, COLORS["selection_highlight"], preview_team)

        state_hint = ""
        if state == GameState.DEPLOY:
            a_count = len(team_a)
            b_count = len(team_b)
            ready = "READY" if a_count > 0 and b_count > 0 else ""
            state_hint = f"Place Units (Blue: {a_count}, Red: {b_count}) {ready}"
        elif state == GameState.BATTLE:
            state_hint = "Battle!"
        elif state == GameState.POST_BATTLE:
            state_hint = "Finished!"

        if panel_visible and state != GameState.BATTLE:
            draw_bottom_panel(screen, font, big_font, battle_result, wave, gold, state_hint, units_db, catalog_scroll, selected_unit_data)
        
        display_arena_h = BATTLE_ARENA_H if not panel_visible else current_arena_h
        draw_minimap(screen, team_a + team_b)
        
        if anim_debug_active and anim_debug:
            anim_debug._draw()
            pygame.display.flip()
            anim_debug_active = anim_debug._handle_events()
            continue
        
        pygame.display.flip()
    
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
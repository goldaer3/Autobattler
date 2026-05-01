# main.py
import pygame
import sys
import random
from config import ARENA_W, ARENA_H, GRID_SZ, GRID_COLS, GRID_ROWS, COLORS, FPS, DEBUG, BOTTOM_PANEL_H
from core.units import load_units_from_yaml, create_unit_from_data_v2 as create_unit_from_data
from core.battle import BattleEngine
from ui.render import init, draw_arena, draw_unit, draw_minimap, draw_placement_preview, draw_bottom_panel, draw_projectiles
from ui.panel import hit_test_catalog
from enum import Enum, auto

class GameState(Enum):
    DEPLOY_A = auto()
    DEPLOY_B = auto()
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
    
    state = GameState.DEPLOY_A
    battle_engine = None
    battle_result = None
    wave = 1
    gold = 0
    running = True
    
    selected_unit_data = None
    catalog_scroll = 0
    
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
                
                if event.key == pygame.K_RETURN:
                    if state == GameState.DEPLOY_A:
                        state = GameState.DEPLOY_B
                    elif state == GameState.DEPLOY_B:
                        state = GameState.BATTLE
                        battle_engine = BattleEngine(team_a, team_b)
                    elif state == GameState.POST_BATTLE:
                        wave += 1
                        gold += 50
                        team_a = []
                        team_b = []
                        random.shuffle(all_unit_ids)
                        team_a_ids = all_unit_ids[:len(all_unit_ids)//2]
                        team_b_ids = all_unit_ids[len(all_unit_ids)//2:]
                        state = GameState.DEPLOY_A
                        battle_engine = None
                        battle_result = None

                if event.key == pygame.K_r:
                    team_a, team_b = [], []
                    state = GameState.DEPLOY_A
                    battle_engine = None
                    battle_result = None
                    wave = 1
                    gold = 0

            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 4:
                    catalog_scroll = max(0, catalog_scroll - 20)
                elif event.button == 5:
                    catalog_scroll += 20
                
                elif event.button == 1:
                    hit_uid = hit_test_catalog(mx, my, units_db, catalog_scroll)
                    if hit_uid:
                        selected_unit_data = units_db[hit_uid].copy()
                    elif my < ARENA_H:
                        if state == GameState.DEPLOY_A and selected_unit_data:
                            grid_x = (mx // GRID_SZ) * GRID_SZ + GRID_SZ // 2
                            grid_y = (my // GRID_SZ) * GRID_SZ + GRID_SZ // 2
                            if grid_x < GRID_SZ * (GRID_COLS // 2 - 1):
                                unit = create_unit_from_data(selected_unit_data, "A", grid_x, grid_y)
                                team_a.append(unit)
                                selected_unit_data = None
                        
                        elif state == GameState.DEPLOY_B and selected_unit_data:
                            grid_x = (mx // GRID_SZ) * GRID_SZ + GRID_SZ // 2
                            grid_y = (my // GRID_SZ) * GRID_SZ + GRID_SZ // 2
                            if grid_x > GRID_SZ * (GRID_COLS // 2 + 1):
                                unit = create_unit_from_data(selected_unit_data, "B", grid_x, grid_y)
                                team_b.append(unit)
                                selected_unit_data = None

        if state == GameState.BATTLE and battle_engine:
            if not battle_engine.step(dt):
                battle_result = battle_engine.run_simulation(dt)
                state = GameState.POST_BATTLE
                battle_engine = None

        screen.fill(COLORS["bg"])
        draw_arena(screen)
        
        for unit in team_a + team_b:
            draw_unit(screen, unit, font)

        if battle_engine and battle_engine.projectiles:
            draw_projectiles(screen, battle_engine.projectiles)

        if selected_unit_data and my < ARENA_H:
            grid_x = (mx // GRID_SZ) * GRID_SZ + GRID_SZ // 2
            grid_y = (my // GRID_SZ) * GRID_SZ + GRID_SZ // 2
            preview_team = "A" if state == GameState.DEPLOY_A else "B"
            draw_placement_preview(screen, selected_unit_data, grid_x, grid_y, COLORS["selection_highlight"], preview_team)

        state_hint = ""
        if state == GameState.DEPLOY_A:
            state_hint = "Place Team A"
        elif state == GameState.DEPLOY_B:
            state_hint = "Place Team B"
        elif state == GameState.BATTLE:
            state_hint = "Battle!"
        elif state == GameState.POST_BATTLE:
            state_hint = "Finished!"
        
        battle_info = battle_result
        draw_bottom_panel(screen, font, big_font, battle_result, wave, gold, state_hint, units_db, catalog_scroll, selected_unit_data)
        draw_minimap(screen, team_a + team_b)
        
        pygame.display.flip()
    
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
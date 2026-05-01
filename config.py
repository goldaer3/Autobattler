# config.py
import pygame
pygame.init()
info = pygame.display.Info()
FULLSCREEN = True
SCREEN_W = info.current_w or 1920
SCREEN_H = info.current_h or 1080
ARENA_W = SCREEN_W
ARENA_H = SCREEN_H - 160
GRID_SZ = 80
GRID_COLS = ARENA_W // GRID_SZ
GRID_ROWS = ARENA_H // GRID_SZ
BOTTOM_PANEL_H = 160
COLORS = {
    "bg": (15, 15, 35),
    "arena_bg": (20, 20, 40),
    "ui_panel": (25, 25, 45, 220),
    "text": (240, 240, 255),
    "accent": (100, 200, 255),
    "hp_bar_bg": (60, 20, 20),
    "hp_bar_fill": (220, 60, 60),
    "team_a_indicator": (80, 180, 255),
    "team_b_indicator": (255, 100, 100),
    "catalog_bg": (10, 10, 20),
    "selection_highlight": (255, 255, 255, 100)
}
FPS = 60
DEBUG = True
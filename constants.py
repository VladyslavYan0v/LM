from enum import Enum

SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GRAY = (100, 100, 100)
RED = (200, 50, 50)
STAR_FRAME_DURATION = 0.75
GLIDE_SPEED = 0.005

class ScreenState(Enum):
    MAIN_MENU = "MAIN_MENU"
    SETTINGS = "SETTINGS"
    LEVEL = "LEVEL"
    LOAD_MENU = "LOAD_MENU"
    PAUSE_MENU = "PAUSE_MENU"


def get_font(size, bold=True):
    import pygame
    path = pygame.font.match_font('segoeui', bold=bold) or pygame.font.match_font('impact')
    return pygame.font.Font(path, size)

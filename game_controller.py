import ctypes
import sys
import pygame
from ctypes import wintypes
from assets import AssetManager
from constants import ScreenState
from menus import MainMenuState, SettingsMenuState
from room import RoomState


class GameController:
    def __init__(self):
        pygame.init()
        pygame.mixer.init()

        self.assets = AssetManager()
        display_info = pygame.display.Info()
        self.auto_width = display_info.current_w
        self.auto_height = display_info.current_h

        self.windowed_size = (0, 0)
        self.windowed_pos = (0, 0)
        self.screen = None
        self.current_state = None

        self._apply_initial_display()

        self.main_menu_state = MainMenuState(self.assets)
        self.settings_state = SettingsMenuState(self.assets, self.auto_width, self.auto_height, self.main_menu_state)
        self.level_state = RoomState(self.assets)
        self.states = {
            ScreenState.MAIN_MENU: self.main_menu_state,
            ScreenState.SETTINGS: self.settings_state,
            ScreenState.LEVEL: self.level_state,
        }

        self.clock = pygame.time.Clock()
        self.running = True

        self.apply_layout_update()
        self.set_state(ScreenState.MAIN_MENU)

    def _apply_initial_display(self):
        self.windowed_size = self._calculate_windowed_size(self.assets.last_windowed_index)
        self.windowed_pos = self._calculate_center_position(self.windowed_size)

        if self.assets.is_fullscreen:
            self.assets.res_index = 3
            self.screen = pygame.display.set_mode((self.auto_width, self.auto_height), pygame.NOFRAME)
            self._set_window_position(0, 0, self.auto_width, self.auto_height)
        else:
            self.screen = pygame.display.set_mode(self.windowed_size)
            self.assets.res_index = self.assets.last_windowed_index
            self._set_window_position(*self.windowed_pos, *self.windowed_size)

        pygame.display.set_caption("Project C")
        self.assets.save_settings()

    def _calculate_windowed_size(self, index):
        resolutions = [
            (self.auto_width // 2, self.auto_height // 2),
            (int(self.auto_width * 0.75), int(self.auto_height * 0.75)),
            (int(self.auto_width * 0.90), int(self.auto_height * 0.85)),
        ]
        return resolutions[index] if index < len(resolutions) else resolutions[0]

    def _calculate_center_position(self, size):
        width, height = size
        return ((self.auto_width - width) // 2, (self.auto_height - height) // 2)

    def _get_window_position(self):
        if not sys.platform.startswith("win"):
            return (100, 100)

        hwnd = pygame.display.get_wm_info().get("window")
        rect = wintypes.RECT()
        ctypes.windll.user32.GetWindowRect(hwnd, ctypes.byref(rect))
        return (rect.left, rect.top)

    def _set_window_position(self, x, y, width, height):
        if not sys.platform.startswith("win"):
            return

        hwnd = pygame.display.get_wm_info().get("window")
        ctypes.windll.user32.MoveWindow(hwnd, x, y, width, height, True)

    def _create_screen(self, size, flags=0):
        return pygame.display.set_mode(size, flags)

    def set_state(self, state_id):
        self.current_state = self.states[state_id]
        current_size = self.screen.get_size()
        self.current_state.resize(*current_size)

        if state_id == ScreenState.MAIN_MENU:
            self.main_menu_state.reset_hovers()

    def apply_layout_update(self):
        width, height = self.screen.get_size()
        self.main_menu_state.resize(width, height)
        self.settings_state.resize(width, height)
        self.level_state.resize(width, height)

    def toggle_fullscreen(self):
        if not self.assets.is_fullscreen:
            self.windowed_size = self.screen.get_size()
            self.windowed_pos = self._get_window_position()
            if self.assets.res_index < 3:
                self.assets.last_windowed_index = self.assets.res_index
            self.screen = self._create_screen((self.auto_width, self.auto_height), pygame.NOFRAME)
            self._set_window_position(0, 0, self.auto_width, self.auto_height)
            self.assets.is_fullscreen = True
            self.assets.res_index = 3
        else:
            self.assets.is_fullscreen = False
            self.assets.res_index = self.assets.last_windowed_index
            window_size = self._calculate_windowed_size(self.assets.res_index)
            self.screen = self._create_screen(window_size)
            self._set_window_position(*self.windowed_pos, *window_size)

        self.assets.save_settings()
        self.apply_layout_update()
        self.current_state.resize(*self.screen.get_size())

    def _apply_display_mode(self):
        if self.assets.is_fullscreen:
            self.windowed_size = self.screen.get_size()
            self.windowed_pos = self._get_window_position()
            self.screen = self._create_screen((self.auto_width, self.auto_height), pygame.NOFRAME)
            self._set_window_position(0, 0, self.auto_width, self.auto_height)
        else:
            self.assets.res_index = self.assets.last_windowed_index
            window_size = self._calculate_windowed_size(self.assets.res_index)
            self.screen = self._create_screen(window_size)
            self._set_window_position(*self._calculate_center_position(window_size), *window_size)

        self.assets.save_settings()
        self.apply_layout_update()
        self.current_state.resize(*self.screen.get_size())

    def run(self):
        self.assets.play_music("music", "ingame_menu.flac")

        while self.running:
            dt = self.clock.tick(60)
            mouse_pos = pygame.mouse.get_pos()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.assets.save_settings()
                    self.running = False
                    break

                if event.type == pygame.KEYDOWN:
                    if event.key in (pygame.K_f, pygame.K_F5):
                        self.toggle_fullscreen()
                    elif event.key == pygame.K_ESCAPE and self.current_state == self.settings_state:
                        self.set_state(ScreenState.MAIN_MENU)

                state_change = self.current_state.handle_event(event)
                if isinstance(state_change, ScreenState):
                    self.set_state(state_change)

                if getattr(self.current_state, "pending_command", None) == "APPLY_DISPLAY_MODE":
                    self._apply_display_mode()
                    if hasattr(self.current_state, "clear_pending_command"):
                        self.current_state.clear_pending_command()

            self.current_state.update(dt, mouse_pos)
            self.current_state.draw(self.screen)
            pygame.display.flip()

        pygame.quit()

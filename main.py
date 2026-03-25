import os
import pygame
import sys
import ctypes
from ctypes import wintypes

# Constants
SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720

BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
STAR_FRAME_DURATION = 0.75
GLIDE_SPEED = 0.005

# Asset Manager

class AssetManager:
    """Handles loading and caching of game assets."""
    def __init__(self):
        self.root = os.path.join(os.path.dirname(__file__), "embed")
        self.cache = {}

    def get_image(self, *path_parts):
        full_path = os.path.join(self.root, *path_parts)
        if full_path not in self.cache:
            try:
                img = pygame.image.load(full_path).convert_alpha()
                self.cache[full_path] = img
            except Exception as e:
                print(f"Warning: failed to load '{full_path}': {e}")
                return None
        return self.cache[full_path]

    def play_music(self, *path_parts, volume=0.6):
        full_path = os.path.join(self.root, *path_parts)
        try:
            pygame.mixer.music.load(full_path)
            pygame.mixer.music.set_volume(volume)
            pygame.mixer.music.play(-1)
        except Exception as e:
            print(f"Music error: {e}")

# UI Components

class FullscreenLayerItem:
    def __init__(self, name, idle_image=None, hover_image=None):
        self.name = name
        self.idle_image = idle_image
        self.hover_image = hover_image
        self.hovered = False
        self._scaled_idle = None
        self._scaled_hover = None
        self._last_size = None
        self.mask = None 

    def update_size(self, size):
        if self._last_size != size:
            if self.idle_image:
                self._scaled_idle = pygame.transform.smoothscale(self.idle_image, size)
                self.mask = pygame.mask.from_surface(self._scaled_idle)
            if self.hover_image:
                self._scaled_hover = pygame.transform.smoothscale(self.hover_image, size)
            self._last_size = size

    def is_hovering(self, mouse_pos):
        if not self.mask: return False
        try: return self.mask.get_at(mouse_pos) != 0
        except IndexError: return False

    def draw(self, screen):
        sprite = self._scaled_hover if self.hovered and self._scaled_hover else self._scaled_idle
        if sprite: screen.blit(sprite, (0, 0))

class AnimatedFullscreenStar(FullscreenLayerItem):
    def __init__(self, name, idle_frames, hover_frames):
        super().__init__(name)
        self.idle_frames = [f for f in idle_frames if f]
        self.hover_frames = [f for f in hover_frames if f]
        self.frame_index = 0
        self.last_update = 0
        self._scaled_idle_frames = []
        self._scaled_hover_frames = []
        self.hover_visual_scale = 0.80  
        self.hitbox_growth_ratio = 1.40 
        self.idle_hitbox = pygame.Rect(0, 0, 0, 0)
        self.active_hitbox = pygame.Rect(0, 0, 0, 0)
        self.hover_draw_offset = (0, 0)

    def update_size(self, size, base_hitbox):
        if self._last_size != size:
            w, h = size
            self._scaled_idle_frames = [pygame.transform.smoothscale(f, size) for f in self.idle_frames]
            hw, hh = int(w * self.hover_visual_scale), int(h * self.hover_visual_scale)
            self._scaled_hover_frames = [pygame.transform.smoothscale(f, (hw, hh)) for f in self.hover_frames]
            ax, ay = base_hitbox.center
            self.hover_draw_offset = (ax - (ax * self.hover_visual_scale), ay - (ay * self.hover_visual_scale))
            self._last_size = size
        
        self.idle_hitbox = base_hitbox
        self.active_hitbox = pygame.Rect(0, 0, base_hitbox.width * self.hitbox_growth_ratio, base_hitbox.height * self.hitbox_growth_ratio)
        self.active_hitbox.center = self.idle_hitbox.center 

    def is_hovering(self, mouse_pos):
        current_hitbox = self.active_hitbox if self.hovered else self.idle_hitbox
        return current_hitbox.collidepoint(mouse_pos)

    def update_animation(self, dt):
        self.last_update += dt
        if self.last_update >= STAR_FRAME_DURATION * 1000:
            self.last_update -= STAR_FRAME_DURATION * 1000
            self.frame_index += 1

    def draw(self, screen):
        if self.hovered and self._scaled_hover_frames:
            idx = self.frame_index % len(self._scaled_hover_frames)
            screen.blit(self._scaled_hover_frames[idx], self.hover_draw_offset)
        elif not self.hovered and self._scaled_idle_frames:
            idx = self.frame_index % len(self._scaled_idle_frames)
            screen.blit(self._scaled_idle_frames[idx], (0, 0))

# Main Logic

class MainMenu:
    """Encapsulates the Main Menu logic and state."""
    def __init__(self, assets):
        self.assets = assets
        
        # UI Entities
        self.char_layer = FullscreenLayerItem("character", self.assets.get_image("mmenu", "gmenu_char.png"))
        self.purple_door = FullscreenLayerItem("start", 
                                              self.assets.get_image("mmenu", "gmenu_exit_idle.png"),
                                              self.assets.get_image("mmenu", "gmenu_exit_hover.png"))
        self.gray_door = FullscreenLayerItem("settings", 
                                            self.assets.get_image("mmenu", "gmenu_settings_idle.png"),
                                            self.assets.get_image("mmenu", "gmenu_settings_hover.png"))
        
        star_idle = [self.assets.get_image("effects", "gmenu_load1.png"), self.assets.get_image("effects", "gmenu_load2.png")]
        star_hover = [self.assets.get_image("effects", "gmenu_load_h1.png"), self.assets.get_image("effects", "gmenu_load_h2.png")]
        self.star_anim = AnimatedFullscreenStar("star", star_idle, star_hover)

        # Backgrounds
        self.bg_img = self.assets.get_image("mmenu", "gmenu_bg.png")
        self.overlay_img = self.assets.get_image("mmenu", "gmenu_overlay.png")
        self.logo_img = self.assets.get_image("mmenu", "logo.png")

        # State vars
        self.glide_progress = 0.0
        self.last_screen_size = (0, 0)
        self.hint_font = None
        self.scaled_bg = None
        self.scaled_overlay = None
        self.scaled_logo = None

    def resize(self, width, height):
        self.last_screen_size = (width, height)
        
        # Backgrounds
        if self.bg_img: self.scaled_bg = pygame.transform.smoothscale(self.bg_img, (width, height))
        if self.overlay_img: self.scaled_overlay = pygame.transform.smoothscale(self.overlay_img, (width, height))
        
        # Logo
        if self.logo_img:
            aspect = self.logo_img.get_width() / self.logo_img.get_height()
            lw = int(width * 0.40)
            self.scaled_logo = pygame.transform.smoothscale(self.logo_img, (lw, int(lw / aspect)))

        # Sub-elements
        self.char_layer.update_size((width, height))
        self.purple_door.update_size((width, height))
        self.gray_door.update_size((width, height))
        
        # Star layout logic
        star_size = min(width, height) * 0.06 
        base_star_box = pygame.Rect(0, 0, star_size, star_size)
        base_star_box.center = (width * 0.51, height * 0.43)
        self.star_anim.update_size((width, height), base_star_box)

        # Font
        path = pygame.font.match_font('segoeui', bold=True) or pygame.font.match_font('impact')
        self.hint_font = pygame.font.Font(path, max(18, int(height * 0.045)))

    def update(self, dt, mouse_pos):
        # Update animations
        self.star_anim.update_animation(dt)
        
        # Update Glide
        if self.glide_progress < 1.0:
            self.glide_progress = min(1.0, self.glide_progress + GLIDE_SPEED)
            if self.scaled_logo:
                self.scaled_logo.set_alpha(int(255 * self.glide_progress))

        # Update Hovers
        self.purple_door.hovered = self.purple_door.is_hovering(mouse_pos)
        self.gray_door.hovered = self.gray_door.is_hovering(mouse_pos)
        self.star_anim.hovered = self.star_anim.is_hovering(mouse_pos)

    def handle_click(self):
        if self.purple_door.hovered: print("[action] start_game()")
        elif self.star_anim.hovered: print("[action] save_menu()")
        elif self.gray_door.hovered: print("[action] open_settings()")

    def draw(self, screen):
        w, h = screen.get_size()
        
        # Draw layers
        if self.scaled_bg: screen.blit(self.scaled_bg, (0, 0))
        self.purple_door.draw(screen)
        self.gray_door.draw(screen)
        self.star_anim.draw(screen)
        self.char_layer.draw(screen)

        # Logo Glide Draw
        if self.scaled_logo:
            target_y = h * 0.04
            start_y = -self.scaled_logo.get_height()
            current_y = start_y + (target_y - start_y) * self.glide_progress
            lx = w // 2 - self.scaled_logo.get_width() // 2
            screen.blit(self.scaled_logo, (lx, int(current_y)))

        if self.scaled_overlay: screen.blit(self.scaled_overlay, (0, 0))

        # Hint text
        if (self.purple_door.hovered or self.star_anim.hovered or self.gray_door.hovered) and self.hint_font:
            msg = "Start New Game" if self.purple_door.hovered else "Load Save Menu" if self.star_anim.hovered else "Settings"
            surf = self.hint_font.render(msg, True, WHITE)
            screen.blit(surf, surf.get_rect(center=(w // 2, int(h * 0.965))))

class GameController:
    """Engine class."""

    def __init__(self):
        pygame.init()

        info = pygame.display.Info()
        self.auto_width, self.auto_height = info.current_w, info.current_h

        self.windowed_size = (self.auto_width // 2, self.auto_height // 2)
        self.windowed_pos = (100, 100)

        self.screen = pygame.display.set_mode(self.windowed_size)
        pygame.display.set_caption("Project C")

        self.clock = pygame.time.Clock()
        self.assets = AssetManager()
        self.menu = MainMenu(self.assets)
        self.running = True
        self.fullscreen = False

    def _get_window_position(self):
        if not sys.platform.startswith("win"):
            return (100, 100)
        hwnd = pygame.display.get_wm_info()["window"]
        rect = wintypes.RECT()
        ctypes.windll.user32.GetWindowRect(hwnd, ctypes.byref(rect))
        return (rect.left, rect.top)

    def _set_window_position(self, x, y, width, height):
        if not sys.platform.startswith("win"):
            return
        hwnd = pygame.display.get_wm_info()["window"]
        ctypes.windll.user32.MoveWindow(hwnd, x, y, width, height, True)

    def toggle_fullscreen(self):
        if not self.fullscreen:
            self.windowed_size = self.screen.get_size()
            self.windowed_pos = self._get_window_position()

            self.screen = pygame.display.set_mode(
                (self.auto_width, self.auto_height), pygame.NOFRAME
            )
            if sys.platform.startswith("win"):
                self._set_window_position(0, 0, self.auto_width, self.auto_height)

            self.fullscreen = True
        else:
            self.screen = pygame.display.set_mode(self.windowed_size)
            if sys.platform.startswith("win"):
                x, y = self.windowed_pos
                self._set_window_position(x, y, self.windowed_size[0], self.windowed_size[1])

            self.fullscreen = False

        self.menu.resize(*self.screen.get_size())

    def run(self):
        self.assets.play_music("music", "ingame_menu.flac")

        while self.running:
            dt = self.clock.tick(60)
            mouse_pos = pygame.mouse.get_pos()

            if self.screen.get_size() != self.menu.last_screen_size:
                self.menu.resize(*self.screen.get_size())

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_f or event.key == pygame.K_F5:
                        self.toggle_fullscreen()
                elif event.type == pygame.VIDEORESIZE:
                    pass
                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    self.menu.handle_click()

            self.menu.update(dt, mouse_pos)
            self.menu.draw(self.screen)
            pygame.display.flip()

        pygame.quit()
        sys.exit()

if __name__ == "__main__":
    game = GameController()
    game.run()
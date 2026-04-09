import os
import pygame
import sys
import ctypes
from ctypes import wintypes
import pickle

# Constants

SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GRAY = (100, 100, 100)
RED = (200, 50, 50)
STAR_FRAME_DURATION = 0.75
GLIDE_SPEED = 0.005

# UI Components

class HorizontalSlider:
    def __init__(self, label, x, y, width, initial_val=0.6):
        self.label = label
        self.rect = pygame.Rect(x, y, width, 10)
        self.value = initial_val
        self.dragging = False

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.inflate(30, 50).collidepoint(event.pos):
                self.dragging = True
        elif event.type == pygame.MOUSEBUTTONUP:
            self.dragging = False
        
        if self.dragging and event.type == pygame.MOUSEMOTION:
            mx = event.pos[0]
            relative_x = mx - self.rect.x
            self.value = max(0.0, min(1.0, relative_x / self.rect.width))
            return True 
        return False

    def draw(self, screen, font, screen_h):
        knob_radius = int(screen_h * 0.018) 
        self.rect.height = int(screen_h * 0.012)
        
        lbl_text = f"{self.label}: {int(self.value * 100)}%"
        lbl_surf = font.render(lbl_text, True, (255, 255, 255))
        screen.blit(lbl_surf, (self.rect.x, self.rect.y - int(screen_h * 0.05)))
        
        pygame.draw.rect(screen, (100, 100, 100), self.rect, border_radius=5)
        knob_x = self.rect.x + (self.value * self.rect.width)
        pygame.draw.circle(screen, (255, 255, 255), (int(knob_x), self.rect.centery), knob_radius)

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

# Core Systems

class PathHelper:
    @staticmethod
    def get_resource_path(relative_path):
        try:
            base_path = sys._MEIPASS
        except AttributeError:
            base_path = os.path.abspath(".")

        return os.path.join(base_path, relative_path)

    @staticmethod
    def get_user_data_path(filename):
        if getattr(sys, 'frozen', False):
            base_path = os.path.dirname(sys.executable)
        else:
            base_path = os.path.dirname(os.path.abspath(__file__))
            
        return os.path.join(base_path, filename)

class AssetManager:
    def __init__(self):
        self.root = PathHelper.get_resource_path("embed")
        self.settings_file = PathHelper.get_user_data_path("settings.dat")
        self.cache = {}
        
        self.music_vol = 0.6
        self.sfx_vol = 0.7
        self.res_index = 0
        self.last_windowed_index = 1
        self.is_fullscreen = False

        self.load_settings()

    def load_settings(self):
        if os.path.exists(self.settings_file):
            try:
                with open(self.settings_file, "rb") as f:
                    data = pickle.load(f)
                    self.music_vol = data.get("music_vol", 0.6)
                    self.sfx_vol = data.get("sfx_vol", 0.7)
                    self.res_index = data.get("res_index", 0)
                    self.is_fullscreen = data.get("is_fullscreen", False)
                    self.last_windowed_index = data.get("last_windowed_index", 
                                                       self.res_index if self.res_index < 3 else 1)
                    pygame.mixer.music.set_volume(self.music_vol)
            except:
                self.save_settings()

    def save_settings(self):
        data = {
            "music_vol": self.music_vol, "sfx_vol": self.sfx_vol,
            "res_index": self.res_index, "is_fullscreen": self.is_fullscreen,
            "last_windowed_index": self.last_windowed_index
        }
        try:
            with open(self.settings_file, "wb") as f:
                pickle.dump(data, f)
        except: pass

    def set_music_volume(self, vol):
        self.music_vol = vol
        pygame.mixer.music.set_volume(vol)
        self.save_settings()

    def set_sfx_volume(self, vol):
        self.sfx_vol = vol
        self.save_settings()

    def get_image(self, *path_parts):
        full_path = os.path.join(self.root, *path_parts)
        if full_path not in self.cache:
            try:
                img = pygame.image.load(full_path).convert_alpha()
                self.cache[full_path] = img
            except: return None
        return self.cache[full_path]

    def play_music(self, *path_parts):
        full_path = os.path.join(self.root, *path_parts)
        try:
            pygame.mixer.music.load(full_path)
            pygame.mixer.music.set_volume(self.music_vol)
            pygame.mixer.music.play(-1)
        except: pass

    def play_sfx(self, *path_parts):
        full_path = os.path.join(self.root, *path_parts)
        try:
            if full_path not in self.cache:
                self.cache[full_path] = pygame.mixer.Sound(full_path)
            sound = self.cache[full_path]
            sound.set_volume(self.sfx_vol)
            sound.play()
        except: pass

    # Setting Update Methods

    def set_music_volume(self, vol):
        self.music_vol = vol
        pygame.mixer.music.set_volume(vol)
        self.save_settings()

    def set_sfx_volume(self, vol):
        self.sfx_vol = vol
        self.save_settings()

    def set_video_settings(self, res_index, is_fs):
        self.last_res_index = res_index
        self.is_fullscreen = is_fs
        self.save_settings()

    # Resource Management

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

    def play_music(self, *path_parts):
        full_path = os.path.join(self.root, *path_parts)
        try:
            pygame.mixer.music.load(full_path)
            pygame.mixer.music.set_volume(self.music_vol)
            pygame.mixer.music.play(-1)
        except Exception as e:
            print(f"Music error: {e}")

    def play_sfx(self, *path_parts):
        full_path = os.path.join(self.root, *path_parts)
        try:
            if full_path not in self.cache:
                self.cache[full_path] = pygame.mixer.Sound(full_path)
            sound = self.cache[full_path]
            # Apply the up-to-date sfx volume before playing
            sound.set_volume(self.sfx_vol)
            sound.play()
        except Exception as e:
            print(f"SFX error: {e}")

# Game States

class MainMenu:
    def __init__(self, assets):
        self.assets = assets
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

        self.bg_img = self.assets.get_image("mmenu", "gmenu_bg.png")
        self.overlay_img = self.assets.get_image("mmenu", "gmenu_overlay.png")
        self.logo_img = self.assets.get_image("mmenu", "logo.png")

        self.glide_progress = 0.0
        self.last_screen_size = (0, 0)
        self.hint_font = None
        self.scaled_bg = None
        self.scaled_overlay = None
        self.scaled_logo = None

    def reset_hovers(self):
        self.purple_door.hovered = False
        self.gray_door.hovered = False
        self.star_anim.hovered = False

    def handle_click(self):
        if self.purple_door.hovered:
            print("[action] start_game()")
        elif self.star_anim.hovered:
            print("[action] save_menu()")

    def resize(self, width, height):
        self.last_screen_size = (width, height)
        if self.bg_img: self.scaled_bg = pygame.transform.smoothscale(self.bg_img, (width, height))
        if self.overlay_img: self.scaled_overlay = pygame.transform.smoothscale(self.overlay_img, (width, height))
        if self.logo_img:
            aspect = self.logo_img.get_width() / self.logo_img.get_height()
            lw = int(width * 0.40)
            self.scaled_logo = pygame.transform.smoothscale(self.logo_img, (lw, int(lw / aspect)))

        self.char_layer.update_size((width, height))
        self.purple_door.update_size((width, height))
        self.gray_door.update_size((width, height))
        
        star_size = min(width, height) * 0.06 
        base_star_box = pygame.Rect(0, 0, star_size, star_size)
        base_star_box.center = (width * 0.51, height * 0.43)
        self.star_anim.update_size((width, height), base_star_box)

        path = pygame.font.match_font('segoeui', bold=True) or pygame.font.match_font('impact')
        self.hint_font = pygame.font.Font(path, max(18, int(height * 0.045)))

    def update(self, dt, mouse_pos):
        self.star_anim.update_animation(dt)
        if self.glide_progress < 1.0:
            self.glide_progress = min(1.0, self.glide_progress + GLIDE_SPEED)
            if self.scaled_logo: self.scaled_logo.set_alpha(int(255 * self.glide_progress))

        self.purple_door.hovered = self.purple_door.is_hovering(mouse_pos)
        self.gray_door.hovered = self.gray_door.is_hovering(mouse_pos)
        self.star_anim.hovered = self.star_anim.is_hovering(mouse_pos)

    def draw(self, screen):
        w, h = screen.get_size()
        if self.scaled_bg: screen.blit(self.scaled_bg, (0, 0))
        self.purple_door.draw(screen)
        self.gray_door.draw(screen)
        self.star_anim.draw(screen)
        self.char_layer.draw(screen)

        if self.scaled_logo:
            target_y = h * 0.04
            start_y = -self.scaled_logo.get_height()
            current_y = start_y + (target_y - start_y) * self.glide_progress
            lx = w // 2 - self.scaled_logo.get_width() // 2
            screen.blit(self.scaled_logo, (lx, int(current_y)))

        if self.scaled_overlay: screen.blit(self.scaled_overlay, (0, 0))

        if (self.purple_door.hovered or self.star_anim.hovered or self.gray_door.hovered) and self.hint_font:
            msg = "Start New Game" if self.purple_door.hovered else "Load Save Menu" if self.star_anim.hovered else "Settings"
            surf = self.hint_font.render(msg, True, WHITE)
            screen.blit(surf, surf.get_rect(center=(w // 2, int(h * 0.965))))
            

class SettingsMenu:
    def __init__(self, assets, auto_w, auto_h):
        self.assets = assets
        self.res_options = [
            (auto_w // 2, auto_h // 2, "Small"),
            (int(auto_w * 0.75), int(auto_h * 0.75), "Medium"),
            (int(auto_w * 0.90), int(auto_h * 0.85), "Large"),
            (auto_w, auto_h, "Fullscreen")
        ]
        self.music_slider = HorizontalSlider("Music Volume", 0, 0, 100, assets.music_vol)
        self.sfx_slider = HorizontalSlider("Sound Effects", 0, 0, 100, assets.sfx_vol)
        self.res_btn_rect = pygame.Rect(0, 0, 1, 1)
        self.reset_btn_rect = pygame.Rect(0, 0, 1, 1)
        self.back_btn_rect = pygame.Rect(0, 0, 1, 1)
        self.font = None

    def resize(self, width, height):
        cx, cy = width // 2, height // 2
        sw, bw, bh = int(width * 0.35), int(width * 0.25), int(height * 0.07)
        self.music_slider.rect.width = sw
        self.music_slider.rect.center = (cx, cy - int(height * 0.15))
        self.sfx_slider.rect.width = sw
        self.sfx_slider.rect.center = (cx, cy + int(height * 0.02))
        self.res_btn_rect = pygame.Rect(0, 0, bw, bh); self.res_btn_rect.center = (cx, cy + int(height * 0.18))
        self.reset_btn_rect = pygame.Rect(0, 0, bw, bh); self.reset_btn_rect.center = (cx, cy + int(height * 0.28))
        self.back_btn_rect = pygame.Rect(0, 0, int(bw * 0.7), bh); self.back_btn_rect.center = (cx, cy + int(height * 0.39))
        path = pygame.font.match_font('segoeui', bold=True) or pygame.font.match_font('impact')
        self.font = pygame.font.Font(path, max(16, int(height * 0.035)))

    def draw(self, screen):
        w, h = screen.get_size(); mouse_pos = pygame.mouse.get_pos()
        overlay = pygame.Surface((w, h), pygame.SRCALPHA); overlay.fill((0, 0, 0, 200)); screen.blit(overlay, (0, 0))
        if not self.font: return
        self.music_slider.draw(screen, self.font, h)
        self.sfx_slider.draw(screen, self.font, h)
        
        hvr = self.res_btn_rect.collidepoint(mouse_pos)
        color = (255, 255, 255) if hvr else (200, 200, 200)
        pygame.draw.rect(screen, color, self.res_btn_rect, 3 if hvr else 1, border_radius=10)
        res_label = self.res_options[self.assets.res_index][2]
        txt = self.font.render(f"Resolution: {res_label}", True, color)
        screen.blit(txt, txt.get_rect(center=self.res_btn_rect.center))
        
        for b, label, base_c in [(self.reset_btn_rect, "Reset Defaults", (120,120,120)), (self.back_btn_rect, "Back", (180,40,40))]:
            is_h = b.collidepoint(mouse_pos)
            c = (min(base_c[0]+40, 255), min(base_c[1]+40, 255), min(base_c[2]+40, 255)) if is_h else base_c
            pygame.draw.rect(screen, c, b, border_radius=10)
            s = self.font.render(label, True, (255, 255, 255))
            screen.blit(s, s.get_rect(center=b.center))


class GameController:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption("Project C")
        self.assets = AssetManager()
        info = pygame.display.Info()
        self.auto_width, self.auto_height = info.current_w, info.current_h
        self.settings = SettingsMenu(self.assets, self.auto_width, self.auto_height)
        
        idx = self.assets.last_windowed_index
        w, h, _ = self.settings.res_options[idx]
        self.windowed_size = (w, h)
        self.windowed_pos = ((self.auto_width - w) // 2, (self.auto_height - h) // 2)

        if self.assets.is_fullscreen:
            self.screen = pygame.display.set_mode((self.auto_width, self.auto_height), pygame.NOFRAME)
            self.assets.res_index = 3
            if sys.platform.startswith("win"): self._set_window_position(0, 0, self.auto_width, self.auto_height)
        else:
            self.screen = pygame.display.set_mode(self.windowed_size)
            self.assets.res_index = idx
            if sys.platform.startswith("win"): self._set_window_position(self.windowed_pos[0], self.windowed_pos[1], w, h)

        self.clock = pygame.time.Clock(); self.menu = MainMenu(self.assets)
        self.state = "MAIN_MENU"; self.running = True
        self.apply_layout_update()

    def _get_window_position(self):
        if not sys.platform.startswith("win"): return (100, 100)
        hwnd = pygame.display.get_wm_info()["window"]; rect = wintypes.RECT()
        ctypes.windll.user32.GetWindowRect(hwnd, ctypes.byref(rect))
        return (rect.left, rect.top)

    def _set_window_position(self, x, y, width, height):
        if not sys.platform.startswith("win"): return
        hwnd = pygame.display.get_wm_info()["window"]
        ctypes.windll.user32.MoveWindow(hwnd, x, y, width, height, True)

    def apply_layout_update(self):
        if not self.screen: return
        w, h = self.screen.get_size()
        self.menu.resize(w, h); self.settings.resize(w, h)

    def toggle_fullscreen(self):
        if not self.assets.is_fullscreen:
            self.windowed_size = self.screen.get_size(); self.windowed_pos = self._get_window_position()
            if self.assets.res_index < 3: self.assets.last_windowed_index = self.assets.res_index
            self.screen = pygame.display.set_mode((self.auto_width, self.auto_height), pygame.NOFRAME)
            if sys.platform.startswith("win"): self._set_window_position(0, 0, self.auto_width, self.auto_height)
            self.assets.is_fullscreen, self.assets.res_index = True, 3
        else:
            idx = self.assets.last_windowed_index; w, h, _ = self.settings.res_options[idx]
            self.screen = pygame.display.set_mode((w, h))
            if sys.platform.startswith("win"): self._set_window_position(self.windowed_pos[0], self.windowed_pos[1], w, h)
            self.assets.is_fullscreen, self.assets.res_index = False, idx
        self.assets.save_settings(); self.apply_layout_update()

    def run(self):
        self.assets.play_music("music", "ingame_menu.flac")
        while self.running:
            dt = self.clock.tick(60); mouse_pos = pygame.mouse.get_pos()
            for event in pygame.event.get():
                if event.type == pygame.QUIT: self.assets.save_settings(); self.running = False
                if event.type == pygame.KEYDOWN:
                    if event.key in (pygame.K_f, pygame.K_F5): self.toggle_fullscreen()
                    if event.key == pygame.K_ESCAPE and self.state == "SETTINGS": self.state = "MAIN_MENU"

                if self.state == "MAIN_MENU":
                    if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                        if self.menu.gray_door.hovered:
                            self.menu.reset_hovers(); self.state = "SETTINGS"; self.assets.play_sfx("sfx", "click.wav")
                        else: self.menu.handle_click()
                
                elif self.state == "SETTINGS":
                    if self.settings.music_slider.handle_event(event): self.assets.set_music_volume(self.settings.music_slider.value)
                    if self.settings.sfx_slider.handle_event(event): self.assets.set_sfx_volume(self.settings.sfx_slider.value)
                    if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                        if self.settings.res_btn_rect.collidepoint(event.pos):
                            self.assets.res_index = (self.assets.res_index + 1) % 4
                            if self.assets.res_index == 3:
                                if not self.assets.is_fullscreen: self.toggle_fullscreen()
                            else:
                                self.assets.is_fullscreen = False; self.assets.last_windowed_index = self.assets.res_index
                                w, h, _ = self.settings.res_options[self.assets.res_index]
                                self.screen = pygame.display.set_mode((w, h))
                                nx, ny = (self.auto_width-w)//2, (self.auto_height-h)//2; self.windowed_pos = (nx, ny)
                                if sys.platform.startswith("win"): self._set_window_position(nx, ny, w, h)
                                self.apply_layout_update()
                            self.assets.save_settings(); self.assets.play_sfx("sfx", "click.wav")
                        
                        elif self.settings.reset_btn_rect.collidepoint(event.pos):
                            self.assets.music_vol, self.assets.sfx_vol = 0.6, 0.7
                            self.assets.res_index, self.assets.last_windowed_index, self.assets.is_fullscreen = 0, 0, False
                            self.settings.music_slider.value, self.settings.sfx_slider.value = 0.6, 0.7
                            w, h, _ = self.settings.res_options[0]; self.screen = pygame.display.set_mode((w, h))
                            nx, ny = (self.auto_width-w)//2, (self.auto_height-h)//2
                            if sys.platform.startswith("win"): self._set_window_position(nx, ny, w, h)
                            self.apply_layout_update(); self.assets.save_settings(); self.assets.play_sfx("sfx", "click.wav")

                        elif self.settings.back_btn_rect.collidepoint(event.pos):
                            self.assets.play_sfx("sfx", "click.wav"); self.state = "MAIN_MENU"

            if self.state == "MAIN_MENU": self.menu.update(dt, mouse_pos)
            elif self.state == "SETTINGS": self.menu.star_anim.update_animation(dt); self.menu.reset_hovers() 
            self.menu.draw(self.screen)
            if self.state == "SETTINGS": self.settings.draw(self.screen)
            pygame.display.flip()
        pygame.quit()

if __name__ == "__main__":
    game = GameController()
    game.run()
import pygame
from constants import WHITE, GRAY, GLIDE_SPEED, ScreenState, get_font
from ui_components import HorizontalSlider, FullscreenLayerItem, AnimatedFullscreenStar


class GameState:
    def __init__(self, assets):
        self.assets = assets
        self.pending_command = None

    def clear_pending_command(self):
        self.pending_command = None

    def resize(self, width, height):
        pass

    def handle_event(self, event):
        pass

    def update(self, dt, mouse_pos):
        pass

    def draw(self, screen):
        pass


class MainMenuState(GameState):
    def __init__(self, assets):
        super().__init__(assets)
        self.char_layer = FullscreenLayerItem("character", self.assets.get_image("mmenu", "gmenu_char.png"))
        self.purple_door = FullscreenLayerItem(
            "start",
            self.assets.get_image("mmenu", "gmenu_exit_idle.png"),
            self.assets.get_image("mmenu", "gmenu_exit_hover.png"),
        )
        self.gray_door = FullscreenLayerItem(
            "settings",
            self.assets.get_image("mmenu", "gmenu_settings_idle.png"),
            self.assets.get_image("mmenu", "gmenu_settings_hover.png"),
        )

        idle_frames = [
            self.assets.get_image("effects", "gmenu_load1.png"),
            self.assets.get_image("effects", "gmenu_load2.png"),
        ]
        hover_frames = [
            self.assets.get_image("effects", "gmenu_load_h1.png"),
            self.assets.get_image("effects", "gmenu_load_h2.png"),
        ]
        self.star_anim = AnimatedFullscreenStar("star", idle_frames, hover_frames)

        self.bg_img = self.assets.get_image("mmenu", "gmenu_bg.png")
        self.overlay_img = self.assets.get_image("mmenu", "gmenu_overlay.png")
        self.logo_img = self.assets.get_image("mmenu", "logo.png")

        self.glide_progress = 0.0
        self.scaled_bg = None
        self.scaled_overlay = None
        self.scaled_logo = None
        self.hint_font = None

    def reset_hovers(self):
        self.purple_door.hovered = False
        self.gray_door.hovered = False
        self.star_anim.hovered = False

    def resize(self, width, height):
        if self.bg_img:
            self.scaled_bg = pygame.transform.smoothscale(self.bg_img, (width, height))
        if self.overlay_img:
            self.scaled_overlay = pygame.transform.smoothscale(self.overlay_img, (width, height))

        if self.logo_img:
            aspect_ratio = self.logo_img.get_width() / self.logo_img.get_height()
            logo_width = int(width * 0.40)
            self.scaled_logo = pygame.transform.smoothscale(self.logo_img, (logo_width, int(logo_width / aspect_ratio)))

        self.char_layer.update_size((width, height))
        self.purple_door.update_size((width, height))
        self.gray_door.update_size((width, height))

        star_size = int(min(width, height) * 0.06)
        base_star_box = pygame.Rect(0, 0, star_size, star_size)
        base_star_box.center = (width * 0.51, height * 0.43)
        self.star_anim.update_size((width, height), base_star_box)

        self.hint_font = get_font(max(18, int(height * 0.045)))

    def update(self, dt, mouse_pos):
        self.star_anim.update_animation(dt)

        if self.glide_progress < 1.0:
            self.glide_progress = min(1.0, self.glide_progress + GLIDE_SPEED)
            if self.scaled_logo:
                self.scaled_logo.set_alpha(int(255 * self.glide_progress))

        self.purple_door.hovered = self.purple_door.is_hovering(mouse_pos)
        self.gray_door.hovered = self.gray_door.is_hovering(mouse_pos)
        self.star_anim.hovered = self.star_anim.is_hovering(mouse_pos)

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.gray_door.hovered:
                self.assets.play_sfx("sfx", "click.wav")
                self.reset_hovers()
                return ScreenState.SETTINGS

            if self.purple_door.hovered:
                self.assets.play_sfx("sfx", "click.wav")
                print("[action] start_game()")

            if self.star_anim.hovered:
                self.assets.play_sfx("sfx", "click.wav")
                print("[action] save_menu()")

        return None

    def draw(self, screen):
        if self.scaled_bg:
            screen.blit(self.scaled_bg, (0, 0))

        self.purple_door.draw(screen)
        self.gray_door.draw(screen)
        self.star_anim.draw(screen)
        self.char_layer.draw(screen)

        if self.scaled_logo:
            width, height = screen.get_size()
            target_y = height * 0.04
            start_y = -self.scaled_logo.get_height()
            current_y = start_y + (target_y - start_y) * self.glide_progress
            logo_x = width // 2 - self.scaled_logo.get_width() // 2
            screen.blit(self.scaled_logo, (logo_x, int(current_y)))

        if self.scaled_overlay:
            screen.blit(self.scaled_overlay, (0, 0))

        if self.hint_font and (self.purple_door.hovered or self.star_anim.hovered or self.gray_door.hovered):
            message = "Start New Game" if self.purple_door.hovered else "Load Save Menu" if self.star_anim.hovered else "Settings"
            hint_surface = self.hint_font.render(message, True, WHITE)
            screen.blit(hint_surface, hint_surface.get_rect(center=(screen.get_width() // 2, int(screen.get_height() * 0.965))))


class SettingsMenuState(GameState):
    def __init__(self, assets, auto_width, auto_height, background_state):
        super().__init__(assets)
        self.background_state = background_state
        self.res_options = [
            (auto_width // 2, auto_height // 2, "Small"),
            (int(auto_width * 0.75), int(auto_height * 0.75), "Medium"),
            (int(auto_width * 0.90), int(auto_height * 0.85), "Large"),
            (auto_width, auto_height, "Fullscreen"),
        ]
        self.music_slider = HorizontalSlider("Music Volume", 0, 0, 100, self.assets.music_vol)
        self.sfx_slider = HorizontalSlider("Sound Effects", 0, 0, 100, self.assets.sfx_vol)
        self.res_btn_rect = pygame.Rect(0, 0, 1, 1)
        self.reset_btn_rect = pygame.Rect(0, 0, 1, 1)
        self.back_btn_rect = pygame.Rect(0, 0, 1, 1)
        self.font = None

    def resize(self, width, height):
        center_x, center_y = width // 2, height // 2
        slider_width = int(width * 0.35)
        button_width = int(width * 0.25)
        button_height = int(height * 0.07)

        self.music_slider.rect.width = slider_width
        self.music_slider.rect.center = (center_x, center_y - int(height * 0.15))

        self.sfx_slider.rect.width = slider_width
        self.sfx_slider.rect.center = (center_x, center_y + int(height * 0.02))

        self.res_btn_rect = pygame.Rect(0, 0, button_width, button_height)
        self.res_btn_rect.center = (center_x, center_y + int(height * 0.18))

        self.reset_btn_rect = pygame.Rect(0, 0, button_width, button_height)
        self.reset_btn_rect.center = (center_x, center_y + int(height * 0.28))

        self.back_btn_rect = pygame.Rect(0, 0, int(button_width * 0.7), button_height)
        self.back_btn_rect.center = (center_x, center_y + int(height * 0.39))

        self.font = get_font(max(16, int(height * 0.035)))

    def update(self, dt, mouse_pos):
        if self.background_state:
            self.background_state.star_anim.update_animation(dt)
            self.background_state.reset_hovers()

    def handle_event(self, event):
        if self.music_slider.handle_event(event):
            self.assets.set_music_volume(self.music_slider.value)

        if self.sfx_slider.handle_event(event):
            self.assets.set_sfx_volume(self.sfx_slider.value)

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.res_btn_rect.collidepoint(event.pos):
                self.assets.res_index = (self.assets.res_index + 1) % len(self.res_options)
                self.assets.is_fullscreen = self.assets.res_index == len(self.res_options) - 1
                self.assets.set_video_settings(self.assets.res_index, self.assets.is_fullscreen)
                self.pending_command = "APPLY_DISPLAY_MODE"
                self.assets.play_sfx("sfx", "click.wav")

            elif self.reset_btn_rect.collidepoint(event.pos):
                self.assets.reset_settings()
                self.music_slider.value = self.assets.music_vol
                self.sfx_slider.value = self.assets.sfx_vol
                self.pending_command = "APPLY_DISPLAY_MODE"
                self.assets.play_sfx("sfx", "click.wav")

            elif self.back_btn_rect.collidepoint(event.pos):
                self.assets.play_sfx("sfx", "click.wav")
                return ScreenState.MAIN_MENU

        return None

    def draw(self, screen):
        if self.background_state:
            self.background_state.draw(screen)

        overlay = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 200))
        screen.blit(overlay, (0, 0))

        if not self.font:
            return

        self.music_slider.draw(screen, self.font, screen.get_height())
        self.sfx_slider.draw(screen, self.font, screen.get_height())

        mouse_pos = pygame.mouse.get_pos()
        resolution_label = self.res_options[self.assets.res_index][2]
        button_color = (255, 255, 255) if self.res_btn_rect.collidepoint(mouse_pos) else (200, 200, 200)
        pygame.draw.rect(screen, button_color, self.res_btn_rect, 3 if self.res_btn_rect.collidepoint(mouse_pos) else 1, border_radius=10)
        res_surface = self.font.render(f"Resolution: {resolution_label}", True, button_color)
        screen.blit(res_surface, res_surface.get_rect(center=self.res_btn_rect.center))

        self._draw_button(screen, self.reset_btn_rect, "Reset Defaults", mouse_pos, (120, 120, 120))
        self._draw_button(screen, self.back_btn_rect, "Back", mouse_pos, (180, 40, 40))

    def _draw_button(self, screen, rect, label, mouse_pos, base_color):
        hovered = rect.collidepoint(mouse_pos)
        color = tuple(min(value + 40, 255) for value in base_color) if hovered else base_color
        pygame.draw.rect(screen, color, rect, border_radius=10)
        label_surface = self.font.render(label, True, WHITE)
        screen.blit(label_surface, label_surface.get_rect(center=rect.center))

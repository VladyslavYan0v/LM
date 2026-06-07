import os
import pygame
from commands import ApplyDisplayModeCommand, GoToMainMenuCommand, StartLevelCommand, StartStoryCommand
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

    def on_enter(self):
        pass

    def on_exit(self):
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
        
        self.transition_target_level = None
        self.fade_alpha = 255
        self.fade_direction = -1

    def reset_hovers(self):
        self.purple_door.hovered = False
        self.gray_door.hovered = False
        self.star_anim.hovered = False

    def reset_transition(self):
        self.transition_target_level = None
        self.pending_command = None
        self.fade_alpha = 255
        self.fade_direction = -1

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
        if self.fade_direction == -1:
            self.fade_alpha = max(0, self.fade_alpha - dt * 0.25)
            if self.fade_alpha == 0:
                self.fade_direction = 0
        elif self.fade_direction == 1:
            self.fade_alpha = min(255, self.fade_alpha + dt * 0.25)
            if self.fade_alpha == 255:
                self.fade_direction = 0
                if self.transition_target_level is not None:
                    self.pending_command = StartStoryCommand(self.transition_target_level)
                    self.transition_target_level = None
            return

        self.star_anim.update_animation(dt)

        if self.glide_progress < 1.0:
            self.glide_progress = min(1.0, self.glide_progress + GLIDE_SPEED)
            if self.scaled_logo:
                self.scaled_logo.set_alpha(int(255 * self.glide_progress))

        self.purple_door.hovered = self.purple_door.is_hovering(mouse_pos)
        self.gray_door.hovered = self.gray_door.is_hovering(mouse_pos)
        self.star_anim.hovered = self.star_anim.is_hovering(mouse_pos)

    def handle_event(self, event):
        if self.fade_direction == 1:
            return None

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.gray_door.hovered:
                self.assets.play_sfx("sfx", "click.wav")
                self.reset_hovers()
                return ScreenState.SETTINGS

            if self.purple_door.hovered:
                self.assets.play_sfx("sfx", "click.wav")
                self.assets.fadeout_music(1000)
                self.transition_target_level = 0
                self.fade_direction = 1
                return None

            if self.star_anim.hovered:
                self.assets.play_sfx("sfx", "click.wav")
                self.reset_hovers()
                return ScreenState.LOAD_MENU

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

        if self.fade_alpha > 0:
            fade_surface = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
            fade_surface.fill((0, 0, 0, min(255, int(self.fade_alpha))))
            screen.blit(fade_surface, (0, 0))

class StoryState(GameState):
    def __init__(self, assets):
        super().__init__(assets)
        self.scripts = {
            0: [
                {"name": "???", "color": [100, 150, 255], "text": "...[w:600]\nUgh...", "sfx": "voice_blue.wav"},
                {"name": "???", "color": [100, 150, 255], "text": "My head...[w:400] Everything is freezing cold.[w:250]\nIt feels like someone ripped half my thoughts out.", "sfx": "voice_blue.wav"},
                {"name": "???", "color": [100, 150, 255], "text": "Where am I?[w:200] Why can't I see anything?[w:400]\nThink...[w:300] Come on.[w:200] A place.[w:150] A face.[w:150] Anything.", "sfx": "voice_blue.wav"},
                {"name": "???", "color": [100, 150, 255], "text": "...[w:500]Nothing.[w:300]\nNo, wait...[w:400] There's a word.[w:200] I remember a name.", "sfx": "voice_blue.wav"},
                {"name": "???", "color": [100, 150, 255], "text": "Kael.[w:400]\nYeah.[w:200] That's me.[w:200] Kael.", "sfx": "voice_blue.wav"},
                {"name": "Kael", "color": [100, 150, 255], "text": "Wonderful.[w:200] A name and absolutely nothing else.[w:400]\nHello?![w:300] Can anybody hear me?!", "sfx": "voice_blue.wav"},
                {"name": "Kael", "color": [100, 150, 255], "text": "...[w:750]\nDidn't think so.", "sfx": "voice_blue.wav"},
                {"name": "???", "color": [220, 60, 60], "text": "You are not alone,[w:150] Kael.", "sfx": "voice_red.wav"},
                {"name": "Kael", "color": [100, 150, 255], "text": "WHAT?![w:300]\nWho's there?!", "sfx": "voice_blue.wav"},
                {"name": "???", "color": [220, 60, 60], "text": "Easy.[w:300] Panic rarely improves a situation.", "sfx": "voice_red.wav"},
                {"name": "Kael", "color": [100, 150, 255], "text": "A voice appears out of nowhere and tells me to easy?[w:300]\nHow do you know my name?", "sfx": "voice_blue.wav"},
                {"name": "???", "color": [220, 60, 60], "text": "Names leave distinct traces here,[w:250] even when memories fail.", "sfx": "voice_red.wav"},
                {"name": "Kael", "color": [100, 150, 255], "text": "That is a terrible answer.", "sfx": "voice_blue.wav"},
                {"name": "???", "color": [220, 60, 60], "text": "Good answers are difficult to find in this place.[w:400]\nWelcome to the Hollow Arch.[w:300] A space suspended between worlds.", "sfx": "voice_red.wav"},
                {"name": "Kael", "color": [100, 150, 255], "text": "The Hollow Arch...?[w:400] Means nothing to me.", "sfx": "voice_blue.wav"},
                {"name": "???", "color": [220, 60, 60], "text": "Very few know of it before they arrive.[w:300]\nI am Vesper,[w:150] the Guardian.[w:300] I have no shape for you to find.", "sfx": "voice_red.wav"},
                {"name": "Kael", "color": [100, 150, 255], "text": "A Guardian?[w:300] Then guard me to the exit.", "sfx": "voice_blue.wav"},
                {"name": "Vesper", "color": [220, 60, 60], "text": "...[w:600]If an exit were so simple,[w:200] I would have found it long ago.", "sfx": "voice_red.wav"},
                {"name": "Kael", "color": [100, 150, 255], "text": "Not exactly reassuring.", "sfx": "voice_blue.wav"},
                {"name": "Vesper", "color": [220, 60, 60], "text": "Reassurance is not my purpose.[w:250] Guidance,[w:150] however,[w:150] I can provide.[w:400]\nIf you wish to piece things together,[w:200] you must walk.", "sfx": "voice_red.wav"},
                {"name": "Vesper", "color": [220, 60, 60], "text": "Reality is brittle here.[w:250] Up may become down.[w:400]\nObserve closely,[w:200] trust your senses,[w:200] and move forward.", "sfx": "voice_red.wav"}
            ],

            1: [
                {"name": "Kael", "color": [100, 150, 255], "text": "Well...[w:400] I'm somehow still alive.[w:300]\nI wasn't sure that rift wouldn't just drop me into a void.", "sfx": "voice_blue.wav"},
                {"name": "Vesper", "color": [220, 60, 60], "text": "The Arch has a flair for dramatic first impressions.[w:300]\nBut you adapt quickly,[w:150] wanderer.", "sfx": "voice_red.wav"},
                {"name": "Kael", "color": [100, 150, 255], "text": "You talk like this place is alive.", "sfx": "voice_blue.wav"},
                {"name": "Vesper", "color": [220, 60, 60], "text": "Perhaps it is.[w:400] I've never been entirely certain.", "sfx": "voice_red.wav"},
                {"name": "Kael", "color": [100, 150, 255], "text": "That's almost a normal thing to say.", "sfx": "voice_blue.wav"},
                {"name": "Vesper", "color": [220, 60, 60], "text": "I will treasure the compliment.", "sfx": "voice_red.wav"},
                {"name": "Kael", "color": [100, 150, 255], "text": "...[w:500]Was that a joke?", "sfx": "voice_blue.wav"},
                {"name": "Vesper", "color": [220, 60, 60], "text": "I've had a very long time to practice them.[w:300]\nThe results remain...[w:300] inconsistent.", "sfx": "voice_red.wav"},
                {"name": "Kael", "color": [100, 150, 255], "text": "How long have you actually been here?", "sfx": "voice_blue.wav"},
                {"name": "Vesper", "color": [220, 60, 60], "text": "...[w:600]Long enough that the concept of time has lost meaning.", "sfx": "voice_red.wav"},
                {"name": "Kael", "color": [100, 150, 255], "text": "That's an evasion,[w:150] not an answer.", "sfx": "voice_blue.wav"},
                {"name": "Vesper", "color": [220, 60, 60], "text": "No.[w:250] But it is the truth.", "sfx": "voice_red.wav"},
                {"name": "Kael", "color": [100, 150, 255], "text": "The layout keeps altering itself every time I look away.", "sfx": "voice_blue.wav"},
                {"name": "Vesper", "color": [220, 60, 60], "text": "It responds to motion,[w:150] possibility,[w:150] and choice.[w:300]\nAnd yet,[w:150] you're still moving.[w:250] That is what matters.", "sfx": "voice_red.wav"},
                {"name": "Kael", "color": [100, 150, 255], "text": "I don't exactly have options.[w:400]\nWait...[w:300] look closely at the walls.[w:250] What are those shapes?", "sfx": "voice_blue.wav"},
                {"name": "Kael", "color": [100, 150, 255], "text": "Are those...[w:300] people?", "sfx": "voice_blue.wav"},
                {"name": "Vesper", "color": [220, 60, 60], "text": "They are those who stopped moving.", "sfx": "voice_red.wav"}
            ],

            2: [
                {"name": "Kael", "color": [100, 150, 255], "text": "Vesper...[w:300] Something is wrong with these portals.[w:300]\nEvery time I step through,[w:150] there's a flash.", "sfx": "voice_blue.wav"},
                {"name": "Kael", "color": [100, 150, 255], "text": "A sudden feeling of falling.[w:300] Like a brief phantom memory.", "sfx": "voice_blue.wav"},
                {"name": "Vesper", "color": [220, 60, 60], "text": "The rifts are tears in space.[w:250] They resonate with what you carry.", "sfx": "voice_red.wav"},
                {"name": "Kael", "color": [100, 150, 255], "text": "But I don't carry anything.", "sfx": "voice_blue.wav"},
                {"name": "Vesper", "color": [220, 60, 60], "text": "The mind preserves impressions long after facts vanish.[w:200]", "sfx": "voice_red.wav"},
                {"name": "Kael", "color": [100, 150, 255], "text": "It feels like a warning.[w:300] Like an instinct to stay away.", "sfx": "voice_blue.wav"},
                {"name": "Vesper", "color": [220, 60, 60], "text": "Fear is an excellent survival tool.[w:250] Do not disregard it.", "sfx": "voice_red.wav"},
                {"name": "Kael", "color": [100, 150, 255], "text": "Sometimes I know where a corridor turns before I see it.[w:300]\nIt doesn't make sense.", "sfx": "voice_blue.wav"},
                {"name": "Vesper", "color": [220, 60, 60], "text": "And are you usually correct?", "sfx": "voice_red.wav"},
                {"name": "Kael", "color": [100, 150, 255], "text": "...[w:400]Yes.", "sfx": "voice_blue.wav"},
                {"name": "Vesper", "color": [220, 60, 60], "text": "Then trust the navigation.[w:250] It wants to keep you breathing.", "sfx": "voice_red.wav"},
                {"name": "Kael", "color": [100, 150, 255], "text": "You're very selective about what you choose to explain.", "sfx": "voice_blue.wav"},
                {"name": "Vesper", "color": [220, 60, 60], "text": "...[w:600]Too much weight can break a traveler early on.[w:400]\nFocus on the path ahead.[w:300] The architecture is sharpening.", "sfx": "voice_red.wav"}
            ],

            3: [
                {"name": "Kael", "color": [100, 150, 255], "text": "The structure here...[w:300] It's narrowing.[w:300]\nNo,[w:150] it feels like it's reacting directly to me.", "sfx": "voice_blue.wav"},
                {"name": "Kael", "color": [100, 150, 255], "text": "When my mind wanders,[w:150] the halls twist.", "sfx": "voice_blue.wav"},
                {"name": "Vesper", "color": [220, 60, 60], "text": "An interesting observation.[w:300]\nThis place is built on intent,[w:200] not just mortar.", "sfx": "voice_red.wav"},
                {"name": "Kael", "color": [100, 150, 255], "text": "So I'm making it harder?", "sfx": "voice_blue.wav"},
                {"name": "Vesper", "color": [220, 60, 60], "text": "Unfocused thoughts create unfocused paths.[w:300]\nThe more you stress the stone,[w:200] the more it resists.", "sfx": "voice_red.wav"},
                {"name": "Kael", "color": [100, 150, 255], "text": "Then give me something solid.[w:250] Why am I here?", "sfx": "voice_blue.wav"},
                {"name": "Vesper", "color": [220, 60, 60], "text": "...[w:500]You arrived because an entry point opened.[w:400]\nThe 'why' comes much later.", "sfx": "voice_red.wav"},
                {"name": "Kael", "color": [100, 150, 255], "text": "That's incredibly frustrating.", "sfx": "voice_blue.wav"},
                {"name": "Vesper", "color": [220, 60, 60], "text": "I prefer you frustrated over stagnant.[w:300]\nAnger has momentum.[w:250] Use it to keep walking.", "sfx": "voice_red.wav"},
                {"name": "Kael", "color": [100, 150, 255], "text": "...[w:400]Fine.[w:250] Let's see what's in the next chamber.", "sfx": "voice_blue.wav"}
            ]
        }
        
        self.target_level = 0
        self.dialogue = []
        self.current_line = 0
        self.current_char = 0
        self.timer = 0.0
        self.extra_delay = 0.0
        self.clean_text = ""
        self.delays = {}
        self.char_delay = 30
        self.font = None
        self.name_font = None
        self.hint_font = None
        self.fade_alpha = 255
        self.fade_direction = -1

    def _parse_line(self, raw_text):
        clean_text = ""
        delays = {}
        i = 0
        while i < len(raw_text):
            if raw_text[i:i+3] == "[w:":
                end = raw_text.find("]", i)
                if end != -1:
                    try:
                        val = int(raw_text[i+3:end])
                        delays[len(clean_text)] = val
                        i = end + 1
                        continue
                    except ValueError:
                        pass
            clean_text += raw_text[i]
            i += 1
        return clean_text, delays

    def _load_current_line(self):
        if self.current_line < len(self.dialogue):
            line = self.dialogue[self.current_line]
            self.clean_text, self.delays = self._parse_line(line["text"])
            self.current_char = 0
            self.timer = 0.0
            self.extra_delay = 0.0
        
    def setup_story(self, level_index):
        self.target_level = level_index
        self.dialogue = self.scripts.get(level_index, self.scripts[0])
        self.current_line = 0
        self.fade_alpha = 255
        self.fade_direction = -1
        self.pending_command = None
        if self.dialogue:
            self._load_current_line()
        self.assets.play_music("music", "depth.flac")
        
    def resize(self, width, height):
        self.font = get_font(max(20, int(height * 0.04)), bold=False)
        self.name_font = get_font(max(24, int(height * 0.05)), bold=True)
        self.hint_font = get_font(max(16, int(height * 0.03)), bold=False)

    def update(self, dt, mouse_pos):
        if self.fade_direction == -1:
            self.fade_alpha = max(0, self.fade_alpha - dt * 0.25)
            if self.fade_alpha == 0:
                self.fade_direction = 0
        elif self.fade_direction == 1:
            self.fade_alpha = min(255, self.fade_alpha + dt * 0.25)
            if self.fade_alpha == 255:
                self.fade_direction = 0
                self.pending_command = StartLevelCommand(self.target_level)
            return

        if self.fade_direction != 0: return

        if self.current_line < len(self.dialogue):
            if self.extra_delay > 0:
                self.extra_delay -= dt
                if self.extra_delay < 0:
                    self.extra_delay = 0.0
            else:
                if self.current_char < len(self.clean_text):
                    self.timer += dt
                    if self.timer >= self.char_delay:
                        self.timer = 0.0
                        self.current_char += 1
                        
                        if self.current_char in self.delays:
                            self.extra_delay = self.delays[self.current_char]
                        
                        char = self.clean_text[self.current_char - 1]
                        if char.isalpha() and self.current_char % 2 == 0:
                            line = self.dialogue[self.current_line]
                            self.assets.play_sfx("sfx", line["sfx"])

    def handle_event(self, event):
        if self.fade_direction != 0: return None

        if event.type == pygame.MOUSEBUTTONDOWN or (event.type == pygame.KEYDOWN and event.key in (pygame.K_SPACE, pygame.K_RETURN)):
            if self.current_line < len(self.dialogue):
                if self.current_char < len(self.clean_text) or self.extra_delay > 0:
                    self.current_char = len(self.clean_text)
                    self.extra_delay = 0.0
                else:
                    self.current_line += 1
                    if self.current_line >= len(self.dialogue):
                        self.fade_direction = 1
                        self.assets.fadeout_music(1000)
                    else:
                        self._load_current_line()
            return None

    def draw(self, screen):
        screen.fill((10, 10, 15))
        
        if self.current_line < len(self.dialogue) and self.font and self.name_font:
            line = self.dialogue[self.current_line]
            name_surf = self.name_font.render(line["name"], True, line["color"])
            screen.blit(name_surf, (screen.get_width() * 0.15, screen.get_height() * 0.65))
            
            text_to_draw = self.clean_text[:self.current_char]
            lines = text_to_draw.split('\n')
            
            start_y = screen.get_height() * 0.75
            line_spacing = self.font.get_linesize() + 5
            
            for i, text_line in enumerate(lines):
                text_surf = self.font.render(text_line, True, WHITE)
                screen.blit(text_surf, (screen.get_width() * 0.15, start_y + i * line_spacing))

            if self.current_char == len(self.clean_text) and self.extra_delay <= 0:
                hint_surf = self.hint_font.render("Click or press Space to continue...", True, GRAY)
                screen.blit(hint_surf, (screen.get_width() * 0.15, screen.get_height() * 0.88))

        if self.fade_alpha > 0:
            fade_surface = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
            fade_surface.fill((0, 0, 0, min(255, int(self.fade_alpha))))
            screen.blit(fade_surface, (0, 0))


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
                self.pending_command = ApplyDisplayModeCommand()
                self.assets.play_sfx("sfx", "click.wav")

            elif self.reset_btn_rect.collidepoint(event.pos):
                self.assets.reset_settings()
                self.music_slider.value = self.assets.music_vol
                self.sfx_slider.value = self.assets.sfx_vol
                self.pending_command = ApplyDisplayModeCommand()
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


class LoadMenuState(GameState):
    def __init__(self, assets, main_menu_state):
        super().__init__(assets)
        self.main_menu_state = main_menu_state
        self.level_buttons = []
        self.back_btn_rect = pygame.Rect(0, 0, 1, 1)
        self.font = None
        self.transition_target_level = None
        self.fade_alpha = 0

    def resize(self, width, height):
        center_x, center_y = width // 2, height // 2
        button_width = int(width * 0.25)
        button_height = int(height * 0.08)
        
        self.level_buttons = []
        for i in range(1, 4):
            rect = pygame.Rect(0, 0, button_width, button_height)
            rect.center = (center_x, center_y - int(height * 0.1) + (i - 1) * int(height * 0.12))
            self.level_buttons.append((i, rect))
            
        self.back_btn_rect = pygame.Rect(0, 0, int(button_width * 0.7), button_height)
        self.back_btn_rect.center = (center_x, center_y + int(height * 0.35))
        self.font = get_font(max(18, int(height * 0.04)))

    def update(self, dt, mouse_pos):
        if self.main_menu_state:
            self.main_menu_state.star_anim.update_animation(dt)

        if self.transition_target_level is not None:
            self.fade_alpha = min(255, self.fade_alpha + dt * 0.25)
            if self.fade_alpha == 255:
                self.pending_command = StartStoryCommand(self.transition_target_level)
                self.transition_target_level = None
            return

    def handle_event(self, event):
        if self.transition_target_level is not None: return None

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mouse_pos = event.pos
            
            for level_num, rect in self.level_buttons:
                if rect.collidepoint(mouse_pos):
                    if self.assets.max_unlocked_level >= level_num:
                        self.assets.play_sfx("sfx", "click.wav")
                        self.assets.fadeout_music(1000)
                        self.transition_target_level = level_num
                        return None
                    else:
                        self.assets.play_sfx("sfx", "error.wav")

            if self.back_btn_rect.collidepoint(mouse_pos):
                self.assets.play_sfx("sfx", "click.wav")
                return ScreenState.MAIN_MENU
        return None

    def draw(self, screen):
        if self.main_menu_state:
            self.main_menu_state.draw(screen)

        overlay = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 210))
        screen.blit(overlay, (0, 0))

        if not self.font:
            return

        mouse_pos = pygame.mouse.get_pos()
        title = self.font.render("SELECT LEVEL", True, WHITE)
        screen.blit(title, title.get_rect(center=(screen.get_width() // 2, screen.get_height() * 0.15)))

        for level_num, rect in self.level_buttons:
            is_unlocked = self.assets.max_unlocked_level >= level_num
            base_color = (60, 160, 80) if is_unlocked else (100, 100, 100)
            hovered = rect.collidepoint(mouse_pos) and is_unlocked
            color = tuple(min(value + 40, 255) for value in base_color) if hovered else base_color
            
            pygame.draw.rect(screen, color, rect, border_radius=10)
            label = f"Level {level_num}" + ("" if is_unlocked else " (Locked)")
            label_surface = self.font.render(label, True, WHITE if is_unlocked else (180, 180, 180))
            screen.blit(label_surface, label_surface.get_rect(center=rect.center))

        self._draw_button(screen, self.back_btn_rect, "Back", mouse_pos, (180, 40, 40))

        if self.fade_alpha > 0:
            fade_surface = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
            fade_surface.fill((0, 0, 0, min(255, int(self.fade_alpha))))
            screen.blit(fade_surface, (0, 0))

    def _draw_button(self, screen, rect, label, mouse_pos, base_color):
        hovered = rect.collidepoint(mouse_pos)
        color = tuple(min(value + 40, 255) for value in base_color) if hovered else base_color
        pygame.draw.rect(screen, color, rect, border_radius=10)
        label_surface = self.font.render(label, True, WHITE)
        screen.blit(label_surface, label_surface.get_rect(center=rect.center))


class PauseMenuState(GameState):
    def __init__(self, assets, auto_width, auto_height, level_state):
        super().__init__(assets)
        self.level_state = level_state
        self.res_options = SettingsMenuState(assets, auto_width, auto_height, None).res_options
        self.music_slider = HorizontalSlider("Music Volume", 0, 0, 100, self.assets.music_vol)
        self.sfx_slider = HorizontalSlider("Sound Effects", 0, 0, 100, self.assets.sfx_vol)
        
        self.resume_btn = pygame.Rect(0, 0, 1, 1)
        self.restart_btn = pygame.Rect(0, 0, 1, 1)
        self.res_btn = pygame.Rect(0, 0, 1, 1)
        self.menu_btn = pygame.Rect(0, 0, 1, 1)
        self.font = None
        self.transition_target = None
        self.fade_alpha = 0

    def resize(self, width, height):
        center_x, center_y = width // 2, height // 2
        slider_width = int(width * 0.35)
        button_width = int(width * 0.25)
        button_height = int(height * 0.07)
        
        self.resume_btn = pygame.Rect(0, 0, button_width, button_height)
        self.resume_btn.center = (center_x, center_y - int(height * 0.25))
        
        self.restart_btn = pygame.Rect(0, 0, button_width, button_height)
        self.restart_btn.center = (center_x, center_y - int(height * 0.15))

        self.music_slider.rect.width = slider_width
        self.sfx_slider.rect.width = slider_width
        self.music_slider.rect.center = (center_x, center_y - int(height * 0.01))
        self.sfx_slider.rect.center = (center_x, center_y + int(height * 0.12))

        self.res_btn = pygame.Rect(0, 0, button_width, button_height)
        self.res_btn.center = (center_x, center_y + int(height * 0.25))

        self.menu_btn = pygame.Rect(0, 0, button_width, button_height)
        self.menu_btn.center = (center_x, center_y + int(height * 0.37))

        self.font = get_font(max(16, int(height * 0.035)))
        
    def update(self, dt, mouse_pos):
        if self.transition_target:
            self.fade_alpha = min(255, self.fade_alpha + dt * 0.25)
            if self.fade_alpha == 255:
                self.pending_command = self.transition_target
                self.transition_target = None

    def handle_event(self, event):
        if self.transition_target: return None

        if self.music_slider.handle_event(event):
            self.assets.set_music_volume(self.music_slider.value)
        if self.sfx_slider.handle_event(event):
            self.assets.set_sfx_volume(self.sfx_slider.value)

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mouse_pos = event.pos
            if self.resume_btn.collidepoint(mouse_pos):
                self.assets.play_sfx("sfx", "click.wav")
                return ScreenState.LEVEL
            elif self.restart_btn.collidepoint(mouse_pos):
                self.assets.play_sfx("sfx", "click.wav")
                self.level_state.setup_level(self.level_state.current_level_idx)
                return ScreenState.LEVEL
            elif self.res_btn.collidepoint(mouse_pos):
                self.assets.res_index = (self.assets.res_index + 1) % len(self.res_options)
                self.assets.is_fullscreen = self.assets.res_index == len(self.res_options) - 1
                self.assets.set_video_settings(self.assets.res_index, self.assets.is_fullscreen)
                self.pending_command = ApplyDisplayModeCommand()
                self.assets.play_sfx("sfx", "click.wav")
            elif self.menu_btn.collidepoint(mouse_pos):
                self.assets.play_sfx("sfx", "click.wav")
                self.assets.fadeout_music(1000)
                self.transition_target = GoToMainMenuCommand()
                return None
        return None

    def draw(self, screen):
        if self.level_state:
            self.level_state.draw(screen)
            
        overlay = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        screen.blit(overlay, (0, 0))
        
        if not self.font: return
        
        mouse_pos = pygame.mouse.get_pos()
        SettingsMenuState._draw_button(self, screen, self.resume_btn, "Resume", mouse_pos, (60, 140, 60))
        SettingsMenuState._draw_button(self, screen, self.restart_btn, "Restart Level", mouse_pos, (140, 100, 40))
        self.music_slider.draw(screen, self.font, screen.get_height())
        self.sfx_slider.draw(screen, self.font, screen.get_height())
        
        resolution_label = self.res_options[self.assets.res_index][2]
        SettingsMenuState._draw_button(self, screen, self.res_btn, f"Resolution: {resolution_label}", mouse_pos, (120, 120, 120))
        SettingsMenuState._draw_button(self, screen, self.menu_btn, "Quit to Main Menu", mouse_pos, (180, 40, 40))
        
        if self.fade_alpha > 0:
            fade_surface = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
            fade_surface.fill((0, 0, 0, min(255, int(self.fade_alpha))))
            screen.blit(fade_surface, (0, 0))

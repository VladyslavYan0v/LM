import os
import random
import math
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
                {"name": "???", "color": [100, 150, 255], "text": "...[w:500]Nothing.[w:300]\nNo, wait...[w:400] I almost remember.[w:200] My name is...", "sfx": "voice_blue.wav", "action": "NAME_INPUT"},
                {"name": "{player_name}", "color": [100, 150, 255], "text": "{player_name}.[w:400]\nYeah.[w:200] That's me.[w:200] {player_name}.", "sfx": "voice_blue.wav"},
                {"name": "{player_name}", "color": [100, 150, 255], "text": "Wonderful.[w:200] A name and absolutely nothing else.[w:400]\nHello?![w:300] Can anybody hear me?!", "sfx": "voice_blue.wav"},
                {"name": "{player_name}", "color": [100, 150, 255], "text": "...[w:750]\nThought so.", "sfx": "voice_blue.wav"},
                {"name": "???", "color": [220, 60, 60], "text": "You are not alone,[w:150] {player_name}.", "sfx": "voice_red.wav"},
                {"name": "{player_name}", "color": [100, 150, 255], "text": "WHAT?![w:300]\nWho's there?!", "sfx": "voice_blue.wav"},
                {"name": "???", "color": [220, 60, 60], "text": "Calm yourself.[w:300] Panic rarely improves a situation.", "sfx": "voice_red.wav"},
                {"name": "{player_name}", "color": [100, 150, 255], "text": "A voice appears out of nowhere and tells me to calm down?[w:300]\nHow do you know my name?", "sfx": "voice_blue.wav"},
                {"name": "???", "color": [220, 60, 60], "text": "Names leave distinct traces here,[w:250] even when memories fail.", "sfx": "voice_red.wav"},
                {"name": "{player_name}", "color": [100, 150, 255], "text": "That is a terrible answer.", "sfx": "voice_blue.wav"},
                {"name": "???", "color": [220, 60, 60], "text": "Good answers are difficult to find in this place.[w:400]\nWelcome to the Hollow Arch.[w:300] A space suspended between worlds.", "sfx": "voice_red.wav"},
                {"name": "{player_name}", "color": [100, 150, 255], "text": "The Hollow Arch...?[w:400] Means nothing to me.", "sfx": "voice_blue.wav"},
                {"name": "???", "color": [220, 60, 60], "text": "Very few know of it before they arrive.[w:300]\nMy name is Vesper,[w:150] I am the Guardian of this realm.", "sfx": "voice_red.wav"},
                {"name": "{player_name}", "color": [100, 150, 255], "text": "A Guardian?[w:300] Then do your job and get me out of here.", "sfx": "voice_blue.wav"},
                {"name": "Vesper", "color": [220, 60, 60], "text": "...[w:600]If it was so simple,[w:200] I would have left this place long ago.", "sfx": "voice_red.wav"},
                {"name": "{player_name}", "color": [100, 150, 255], "text": "Not exactly reassuring.", "sfx": "voice_blue.wav"},
                {"name": "Vesper", "color": [220, 60, 60], "text": "Reassurance is not my purpose.[w:250] Guidance,[w:150] however,[w:150] I can provide.[w:400]\nIf you wish to piece things together,[w:200] you must walk.", "sfx": "voice_red.wav"},
                {"name": "Vesper", "color": [220, 60, 60], "text": "Reality is brittle here.[w:250] Laws of your world no longer apply here.[w:400]\nObserve closely,[w:200] trust your senses,[w:200] and move forward.", "sfx": "voice_red.wav"}
            ],

            1: [
                {"name": "{player_name}", "color": [100, 150, 255], "text": "Well...[w:400] I'm somehow still alive.[w:300]\nI wasn't sure that rift wouldn't just drop me into a void.", "sfx": "voice_blue.wav"},
                {"name": "Vesper", "color": [220, 60, 60], "text": "The Arch has a flair for dramatic first impressions.[w:300]\nBut you adapt quickly,[w:150] wanderer.", "sfx": "voice_red.wav"},
                {"name": "{player_name}", "color": [100, 150, 255], "text": "You talk like this place is alive.", "sfx": "voice_blue.wav"},
                {"name": "Vesper", "color": [220, 60, 60], "text": "Perhaps it is.[w:400] I've never been entirely certain.", "sfx": "voice_red.wav"},
                {"name": "{player_name}", "color": [100, 150, 255], "text": "That's almost a normal thing to say.", "sfx": "voice_blue.wav"},
                {"name": "Vesper", "color": [220, 60, 60], "text": "I will treasure the compliment.", "sfx": "voice_red.wav"},
                {"name": "{player_name}", "color": [100, 150, 255], "text": "...[w:500]Was that a joke?", "sfx": "voice_blue.wav"},
                {"name": "Vesper", "color": [220, 60, 60], "text": "I've had a very long time to practice them.[w:300]\nThe results remain...[w:300] inconsistent.", "sfx": "voice_red.wav"},
                {"name": "{player_name}", "color": [100, 150, 255], "text": "How long have you actually been here?", "sfx": "voice_blue.wav"},
                {"name": "Vesper", "color": [220, 60, 60], "text": "...[w:600]Long enough that the concept of time has lost meaning.", "sfx": "voice_red.wav"},
                {"name": "{player_name}", "color": [100, 150, 255], "text": "That's an evasion,[w:150] not an answer.", "sfx": "voice_blue.wav"},
                {"name": "Vesper", "color": [220, 60, 60], "text": "No.[w:250] But it is the truth.", "sfx": "voice_red.wav"},
                {"name": "{player_name}", "color": [100, 150, 255], "text": "The layout keeps altering itself every time I look away.", "sfx": "voice_blue.wav"},
                {"name": "Vesper", "color": [220, 60, 60], "text": "It responds to motion,[w:150] possibility,[w:150] and choice.[w:300]\nAnd yet,[w:150] you're still moving.[w:250] That is what matters.", "sfx": "voice_red.wav"},
                {"name": "{player_name}", "color": [100, 150, 255], "text": "I don't exactly have options.[w:400]\nWait...[w:300] look closely at the walls.[w:250] What are those shapes?", "sfx": "voice_blue.wav"},
                {"name": "{player_name}", "color": [100, 150, 255], "text": "Are those...[w:300] people?", "sfx": "voice_blue.wav"},
                {"name": "Vesper", "color": [220, 60, 60], "text": "They are those who stopped moving.", "sfx": "voice_red.wav"}
            ],

            2: [
                {"name": "{player_name}", "color": [100, 150, 255], "text": "Vesper...[w:300] Something is wrong with these portals.[w:300]\nEvery time I step through,[w:150] there's a flash.", "sfx": "voice_blue.wav"},
                {"name": "{player_name}", "color": [100, 150, 255], "text": "A sudden feeling of falling.[w:300] Like a brief phantom memory.", "sfx": "voice_blue.wav"},
                {"name": "Vesper", "color": [220, 60, 60], "text": "The rifts are tears in space.[w:250] They resonate with what you carry.", "sfx": "voice_red.wav"},
                {"name": "{player_name}", "color": [100, 150, 255], "text": "But I don't carry anything.", "sfx": "voice_blue.wav"},
                {"name": "Vesper", "color": [220, 60, 60], "text": "The mind preserves impressions long after facts vanish.[w:200]", "sfx": "voice_red.wav"},
                {"name": "{player_name}", "color": [100, 150, 255], "text": "It feels like a warning.[w:300] Like an instinct to stay away.", "sfx": "voice_blue.wav"},
                {"name": "Vesper", "color": [220, 60, 60], "text": "Fear is an excellent survival tool.[w:250] Do not disregard it.", "sfx": "voice_red.wav"},
                {"name": "{player_name}", "color": [100, 150, 255], "text": "Sometimes I know where a corridor turns before I see it.[w:300]\nIt doesn't make sense.", "sfx": "voice_blue.wav"},
                {"name": "Vesper", "color": [220, 60, 60], "text": "And are you usually correct?", "sfx": "voice_red.wav"},
                {"name": "{player_name}", "color": [100, 150, 255], "text": "...[w:400]Yes.", "sfx": "voice_blue.wav"},
                {"name": "Vesper", "color": [220, 60, 60], "text": "Then trust the navigation.[w:250] It wants to keep you breathing.", "sfx": "voice_red.wav"},
                {"name": "{player_name}", "color": [100, 150, 255], "text": "You're very selective about what you choose to explain.", "sfx": "voice_blue.wav"},
                {"name": "Vesper", "color": [220, 60, 60], "text": "...[w:600]Too much weight can break a traveler early on.[w:400]\nFocus on the path ahead.[w:300] The architecture is sharpening.", "sfx": "voice_red.wav"}
            ],

            3: [
                {"name": "{player_name}", "color": [100, 150, 255], "text": "The structure here...[w:300] It's narrowing.[w:300]\nNo,[w:150] it feels like it's reacting directly to me.", "sfx": "voice_blue.wav"},
                {"name": "{player_name}", "color": [100, 150, 255], "text": "When my mind wanders,[w:150] the halls twist.", "sfx": "voice_blue.wav"},
                {"name": "Vesper", "color": [220, 60, 60], "text": "An interesting observation.[w:300]\nThis place is built on intent,[w:200] not just mortar.", "sfx": "voice_red.wav"},
                {"name": "{player_name}", "color": [100, 150, 255], "text": "So I'm making it harder?", "sfx": "voice_blue.wav"},
                {"name": "Vesper", "color": [220, 60, 60], "text": "Unfocused thoughts create unfocused paths.[w:300]\nThe more you stress the stone,[w:200] the more it resists.", "sfx": "voice_red.wav"},
                {"name": "{player_name}", "color": [100, 150, 255], "text": "Then give me something solid.[w:250] Why am I here?", "sfx": "voice_blue.wav"},
                {"name": "Vesper", "color": [220, 60, 60], "text": "...[w:500]You arrived because an entry point opened.[w:400]\nThe 'why' comes much later.", "sfx": "voice_red.wav"},
                {"name": "{player_name}", "color": [100, 150, 255], "text": "That's incredibly frustrating.", "sfx": "voice_blue.wav"},
                {"name": "Vesper", "color": [220, 60, 60], "text": "I prefer you frustrated over stagnant.[w:300]\nAnger has momentum.[w:250] Use it to keep walking.", "sfx": "voice_red.wav"},
                {"name": "{player_name}", "color": [100, 150, 255], "text": "...[w:400]Fine.[w:250] Let's see what's in the next chamber.", "sfx": "voice_blue.wav"}
            ]
        }
        
        self.player_name = ""
        self.typed_name = ""
        self.ui_mode = "DIALOGUE"
        self.dialogue_alpha = 255.0
        self.name_menu_alpha = 0.0
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
        self.particles = [[random.uniform(-1.0, 1.0), random.uniform(-1.0, 1.0), random.uniform(0.1, 2.0)] for _ in range(150)]
        self.aggression_level = 0.0
        self.vesper_appeared = False
        self.pulse_time = 0.0
        
        self.name_items = []
        self.name_sel_idx = 0

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
            p_name = self.player_name if self.player_name else "???"
            raw_text = line["text"].replace("{player_name}", p_name)
            self.clean_text, self.delays = self._parse_line(raw_text)
            self.current_char = 0
            self.timer = 0.0
            self.extra_delay = 0.0
            
    def _init_name_menu(self):
        self.name_items = []
        
        lines_caps = ["QWERTYUIOP", "ASDFGHJKL", "ZXCVBNM"]
        for row_idx, line in enumerate(lines_caps):
            offset = -(len(line) * 1.05) / 2.0 + 0.525
            for col_idx, char in enumerate(line):
                col = offset + col_idx * 1.05
                row = -2.5 + row_idx * 1.05
                self.name_items.append({"text": char, "lx": col, "ly": row, "type": "char"})
                
        lines_small = ["qwertyuiop", "asdfghjkl", "zxcvbnm"]
        for row_idx, line in enumerate(lines_small):
            offset = -(len(line) * 1.05) / 2.0 + 0.525
            for col_idx, char in enumerate(line):
                col = offset + col_idx * 1.05
                row = 1.0 + row_idx * 1.05
                self.name_items.append({"text": char, "lx": col, "ly": row, "type": "char"})
                
        self.name_items.append({"text": "ERASE", "lx": -2.5, "ly": 4.5, "type": "action"})
        self.name_items.append({"text": "CONFIRM", "lx": 2.5, "ly": 4.5, "type": "action"})
        self.name_sel_idx = 0
        
    def _navigate_name_menu(self, dx, dy):
        curr = self.name_items[self.name_sel_idx]
        cx, cy = curr["lx"], curr["ly"]
        best_idx = self.name_sel_idx
        best_score = float('inf')
        
        for i, item in enumerate(self.name_items):
            if i == self.name_sel_idx: continue
            nx, ny = item["lx"], item["ly"]
            vx, vy = nx - cx, ny - cy
            
            valid = False
            if dx > 0 and vx > 0: valid = True
            if dx < 0 and vx < 0: valid = True
            if dy > 0 and vy > 0: valid = True
            if dy < 0 and vy < 0: valid = True
            
            if valid:
                if dx != 0:
                    score = abs(vx) + abs(vy) * 10.0
                else:
                    score = abs(vy) + abs(vx) * 2.0
                    
                if score < best_score:
                    best_score = score
                    best_idx = i
                    
        if best_idx != self.name_sel_idx:
            self.assets.play_sfx("sfx", "click.wav")
            self.name_sel_idx = best_idx
            
    def _activate_name_item(self, item):
        if item["type"] == "char":
            self.assets.play_sfx("sfx", "click.wav")
            if len(self.typed_name) < 12:
                self.typed_name += item["text"]
        elif item["text"] == "ERASE":
            self.assets.play_sfx("sfx", "click.wav")
            self.typed_name = self.typed_name[:-1]
        elif item["text"] == "CONFIRM":
            if len(self.typed_name.strip()) > 0:
                self.assets.play_sfx("sfx", "click.wav")
                if self.typed_name.strip().lower() == "vesper":
                    self.ui_mode = "VESPER_CONFIRM"
                    self.vesper_confirm_sel = 1
                    self.vesper_warning_timer = 0.0
                    self.vesper_warning_chars = 0
                    self.assets.play_sfx("sfx", "error.wav")
                else:
                    self.player_name = self.typed_name.strip()
                    self.ui_mode = "FADE_TO_DIALOGUE"
            else:
                self.assets.play_sfx("sfx", "error.wav")
        
    def setup_story(self, level_index):
        self.target_level = level_index
        if level_index == 0:
            self.player_name = ""
        self.typed_name = ""
        self.ui_mode = "DIALOGUE"
        self.dialogue_alpha = 255.0
        self.name_menu_alpha = 0.0
        self.dialogue = self.scripts.get(level_index, self.scripts[0])
        self.current_line = 0
        self.fade_alpha = 255
        self.fade_direction = -1
        self.pending_command = None
        self.aggression_level = 0.0
        self.vesper_appeared = False
        self.pulse_time = 0.0
        if self.dialogue:
            self._load_current_line()
        self.assets.play_music("music", "depth.flac")
        
    def resize(self, width, height):
        self.font = get_font(max(20, int(height * 0.04)), bold=False)
        self.name_font = get_font(max(24, int(height * 0.05)), bold=True)
        self.hint_font = get_font(max(16, int(height * 0.03)), bold=False)

    def update(self, dt, mouse_pos):
        if hasattr(self, "ui_mode") and self.ui_mode == "CRASH_SEQUENCE":
            if not hasattr(self, "crash_timer"): self.crash_timer = 0.0
            self.crash_timer += dt
            if self.crash_timer > 3000:
                import sys
                pygame.quit()
                sys.exit(0)
            return

        if hasattr(self, "ui_mode") and self.ui_mode == "VESPER_CONFIRM":
            self.vesper_warning_timer += dt
            t = self.vesper_warning_timer
            
            title_text_1 = "To claim this name is to surrender the self."
            title_text_2 = "Two minds cannot occupy a single vessel."
            sub_text = "DO YOU RELINQUISH CONTROL?"
            
            chars = 0
            if t < 2000:
                chars = int((t / 2000.0) * len(title_text_1))
            elif t < 2500:
                chars = len(title_text_1)
            elif t < 4500:
                chars = len(title_text_1) + int(((t - 2500) / 2000.0) * len(title_text_2))
            elif t < 5000:
                chars = len(title_text_1) + len(title_text_2)
            elif t < 7000:
                chars = len(title_text_1) + len(title_text_2) + int(((t - 5000) / 2000.0) * len(sub_text))
            else:
                chars = len(title_text_1) + len(title_text_2) + len(sub_text)
                
            expected_chars = min(chars, len(title_text_1) + len(title_text_2) + len(sub_text))
            
            current_chars = getattr(self, "vesper_warning_chars", 0)
            if expected_chars > current_chars:
                self.vesper_warning_chars = expected_chars
                if expected_chars % 2 == 0:
                    self.assets.play_sfx("sfx", "voice_red.wav")
                    
            if t > 7000:
                if not hasattr(self, "btn_offsets"): self.btn_offsets = [(0,0), (0,0)]
                if not hasattr(self, "flicker_t"): self.flicker_t = 0
                self.flicker_t += dt
                if self.flicker_t > 80:
                    self.flicker_t = 0
                    if random.random() < 0.4:
                        self.btn_offsets = [
                            (random.randint(-150, 150), random.randint(-100, 100)),
                            (random.randint(-150, 150), random.randint(-100, 100))
                        ]
                    else:
                        self.btn_offsets = [(0,0), (0,0)]

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
            
        self.pulse_time += dt
            
        if self.current_line < len(self.dialogue):
            if self.dialogue[self.current_line].get("color") == [220, 60, 60]:
                self.vesper_appeared = True
                
        target_aggression = 1.0 if self.vesper_appeared else 0.0
        if self.aggression_level < target_aggression:
            self.aggression_level = min(1.0, self.aggression_level + dt * 0.0015)
        elif self.aggression_level > target_aggression:
            self.aggression_level = max(0.0, self.aggression_level - dt * 0.0015)
                
        speed = 0.2
        for p in self.particles:
            p[2] -= (dt / 1000.0) * speed
            if p[2] <= 0.01:
                p[0] = random.uniform(-1.0, 1.0)
                p[1] = random.uniform(-1.0, 1.0)
                p[2] = 2.0

        if self.fade_direction != 0: return

        fade_speed = 400.0 * (dt / 1000.0)
        
        if self.ui_mode == "FADE_TO_NAME":
            self.dialogue_alpha = max(0.0, self.dialogue_alpha - fade_speed)
            if self.dialogue_alpha == 0:
                self.ui_mode = "FADE_NAME_IN"
                self._init_name_menu()
        elif self.ui_mode == "FADE_NAME_IN":
            self.name_menu_alpha = min(255.0, self.name_menu_alpha + fade_speed)
            if self.name_menu_alpha == 255:
                self.ui_mode = "NAME_ACTIVE"
        elif self.ui_mode == "FADE_TO_DIALOGUE":
            self.name_menu_alpha = max(0.0, self.name_menu_alpha - fade_speed)
            if self.name_menu_alpha == 0:
                self.ui_mode = "FADE_DIALOGUE_IN"
                self.current_line += 1
                self._load_current_line()
        elif self.ui_mode == "FADE_DIALOGUE_IN":
            self.dialogue_alpha = min(255.0, self.dialogue_alpha + fade_speed)
            if self.dialogue_alpha == 255:
                self.ui_mode = "DIALOGUE"

        if self.current_line < len(self.dialogue):
            if self.extra_delay > 0:
                self.extra_delay -= dt
                if self.extra_delay < 0:
                    self.extra_delay = 0.0
            elif self.ui_mode in ("DIALOGUE", "FADE_TO_NAME"):
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
                elif self.ui_mode == "DIALOGUE":
                    line_data = self.dialogue[self.current_line]
                    if line_data.get("action") == "NAME_INPUT" and not self.player_name:
                        self.ui_mode = "FADE_TO_NAME"

    def handle_event(self, event):
        if self.fade_direction != 0: return None
        
        if self.ui_mode == "VESPER_CONFIRM":
            if getattr(self, "vesper_warning_timer", 0) < 8000:
                return None
                
            if event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_LEFT, pygame.K_RIGHT, pygame.K_UP, pygame.K_DOWN, pygame.K_a, pygame.K_d):
                    self.vesper_confirm_sel = 1 - getattr(self, "vesper_confirm_sel", 1)
                    self.assets.play_sfx("sfx", "click.wav")
                elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                    self.assets.play_sfx("sfx", "click.wav")
                    if getattr(self, "vesper_confirm_sel", 1) == 0:
                        self.ui_mode = "CRASH_SEQUENCE"
                        self.crash_timer = 0.0
                    else:
                        self.ui_mode = "NAME_ACTIVE"
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                screen_w, screen_h = pygame.display.get_surface().get_size()
                dialog_w, dialog_h = int(screen_w * 0.6), int(screen_h * 0.45)
                dx, dy = (screen_w - dialog_w) // 2, (screen_h - dialog_h) // 2
                
                yes_off, no_off = getattr(self, "btn_offsets", [(0,0), (0,0)])
                anim_t = min(1.0, (getattr(self, "vesper_warning_timer", 0) - 7000) / 1000.0)
                slide_y = int((1.0 - anim_t) * 30)
                
                yes_rect = pygame.Rect(dx + int(dialog_w * 0.2) + yes_off[0], dy + int(dialog_h * 0.75) + yes_off[1] + slide_y, 120, 45)
                no_rect = pygame.Rect(dx + int(dialog_w * 0.8) - 120 + no_off[0], dy + int(dialog_h * 0.75) + no_off[1] + slide_y, 120, 45)
                if yes_rect.collidepoint(event.pos):
                    self.assets.play_sfx("sfx", "click.wav")
                    self.ui_mode = "CRASH_SEQUENCE"
                    self.crash_timer = 0.0
                elif no_rect.collidepoint(event.pos):
                    self.assets.play_sfx("sfx", "click.wav")
                    self.ui_mode = "NAME_ACTIVE"
            return None

        if self.ui_mode == "NAME_ACTIVE":
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_BACKSPACE:
                    self.assets.play_sfx("sfx", "click.wav")
                    self.typed_name = self.typed_name[:-1]
                elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                    sel_item = self.name_items[self.name_sel_idx]
                    self._activate_name_item(sel_item)
                elif event.key == pygame.K_UP:
                    self._navigate_name_menu(0, -1)
                elif event.key == pygame.K_DOWN:
                    self._navigate_name_menu(0, 1)
                elif event.key == pygame.K_LEFT:
                    self._navigate_name_menu(-1, 0)
                elif event.key == pygame.K_RIGHT:
                    self._navigate_name_menu(1, 0)
                elif event.unicode.isalpha() and len(self.typed_name) < 12:
                    self.assets.play_sfx("sfx", "click.wav")
                    self.typed_name += event.unicode
            return None

        if event.type == pygame.MOUSEBUTTONDOWN or (event.type == pygame.KEYDOWN and event.key in (pygame.K_SPACE, pygame.K_RETURN)):
            if self.ui_mode == "DIALOGUE" and self.current_line < len(self.dialogue):
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
        
        bg_r = int(2 + (8 * self.aggression_level))
        bg_g = 2
        bg_b = int(5 - (3 * self.aggression_level))
        screen.fill((bg_r, bg_g, bg_b))
        
        screen_w, screen_h = screen.get_size()
        center_x = screen_w // 2
        center_y = screen_h // 2
        
        particle_color = (
            int(80 + (80 * self.aggression_level)),
            int(90 - (50 * self.aggression_level)),
            int(120 - (80 * self.aggression_level))
        )
        
        for p in self.particles:
            x, y, z = p
            size = max(1, int(3.0 / z))
            prev_z = z + 0.1
            
            proj_x = center_x + (x / z) * (screen_h * 0.8)
            proj_y = center_y + (y / z) * (screen_h * 0.8)
            
            prev_proj_x = center_x + (x / prev_z) * (screen_h * 0.8)
            prev_proj_y = center_y + (y / prev_z) * (screen_h * 0.8)
            
            pygame.draw.line(screen, particle_color, (int(prev_proj_x), int(prev_proj_y)), (int(proj_x), int(proj_y)), size)

        if self.aggression_level > 0:
            pulse = math.sin(self.pulse_time * 0.0008)
            pulse_norm = (pulse + 1.0) / 2.0  # від 0.0 до 1.0
            
            base_scale = 0.09 + 0.06 * pulse_norm
            max_radius = min(screen_w, screen_h) * base_scale
            
            # Allocate surface based on max possible size to prevent lag spikes
            max_possible_radius = min(screen_w, screen_h) * 0.15
            surf_size = int(max_possible_radius * 9.0)
            if not hasattr(self, '_glow_surf') or self._glow_surf.get_size() != (surf_size, surf_size):
                self._glow_surf = pygame.Surface((surf_size, surf_size), pygame.SRCALPHA)
            else:
                self._glow_surf.fill((0, 0, 0, 0))
                
            surf_center = surf_size // 2
            
            red_boost = int(40 * pulse_norm)
            gb_drop = int(10 * pulse_norm)
            
            num_points = 120
            if not hasattr(self, "_star_trig") or len(self._star_trig) != num_points:
                self._star_trig = []
                for p in range(num_points):
                    theta = p * (math.pi * 2 / num_points)
                    self._star_trig.append((
                        math.cos(theta),
                        math.sin(theta),
                        ((math.cos(theta * 4) + 1) / 2) ** 4,
                        ((math.cos(theta * 8) + 1) / 2) ** 6 * 0.15
                    ))
            
            steps = 25
            for i in range(steps):
                u = 1.0 - (i / steps)
                
                if u < 0.4:
                    norm = u / 0.4
                    color = (min(255, int(160 * (norm ** 2)) + red_boost), 0, 0, 255)
                elif u < 0.7:
                    norm = (u - 0.4) / 0.3
                    gb = max(0, int(15 * norm) - gb_drop)
                    color = (min(255, int(160 + 95 * norm) + red_boost), gb, gb, 255)
                else:
                    norm = (u - 0.7) / 0.3
                    gb = max(0, int(15 * (1.0 - norm)) - gb_drop)
                    color = (255, gb, gb, int(255 * (1.0 - norm)))
                
                points = []
                u_18 = u ** 1.8
                z_mult = 2.1
                
                for cos_t, sin_t, spike, small_spike in self._star_trig:
                    perspective = 3.5 / (3.5 - (u_18 * (spike + small_spike) * z_mult))
                    px = surf_center + (u * cos_t * perspective) * max_radius
                    py = surf_center + (u * sin_t * perspective) * max_radius
                    points.append((px, py))
                
                pygame.draw.polygon(self._glow_surf, color, points)
                    
            self._glow_surf.set_alpha(int(255 * self.aggression_level))
            screen.blit(self._glow_surf, (center_x - surf_center, center_y - surf_center))
            
        if self.dialogue_alpha > 0 and self.current_line < len(self.dialogue) and self.font and self.name_font:
            dialog_layer = pygame.Surface((screen_w, screen_h), pygame.SRCALPHA)
            line = self.dialogue[self.current_line]
            
            box_w = int(screen_w * 0.8)
            box_h = int(screen_h * 0.28)
            box_x = int(screen_w * 0.1)
            box_y = int(screen_h * 0.68)
            
            dialog_surf = pygame.Surface((box_w, box_h), pygame.SRCALPHA)
            pygame.draw.rect(dialog_surf, (20, 20, 25, 235), dialog_surf.get_rect(), border_radius=12)
            pygame.draw.rect(dialog_surf, line["color"], dialog_surf.get_rect(), width=2, border_radius=12)
            dialog_layer.blit(dialog_surf, (box_x, box_y))
            
            display_name = line["name"].replace("{player_name}", self.player_name if self.player_name else "???")
            name_surf = self.name_font.render(display_name, True, (15, 15, 20))
            name_box_w, name_box_h = name_surf.get_width() + 40, name_surf.get_height() + 10
            name_box_x, name_box_y = box_x + 40, box_y - name_box_h + 5
            
            name_bg_surf = pygame.Surface((name_box_w, name_box_h), pygame.SRCALPHA)
            pygame.draw.rect(name_bg_surf, line["color"], name_bg_surf.get_rect(), border_radius=8)
            dialog_layer.blit(name_bg_surf, (name_box_x, name_box_y))
            dialog_layer.blit(name_surf, (name_box_x + 20, name_box_y + 2))

            text_to_draw = self.clean_text[:self.current_char]
            for i, text_line in enumerate(text_to_draw.split('\n')):
                text_surf = self.font.render(text_line, True, WHITE)
                dialog_layer.blit(text_surf, (box_x + 40, box_y + 35 + i * (self.font.get_linesize() + 5)))

            if self.current_char == len(self.clean_text) and self.extra_delay <= 0 and self.ui_mode == "DIALOGUE":
                hint_surf = self.hint_font.render("Click or press Space to continue...", True, GRAY)
                dialog_layer.blit(hint_surf, (box_x + box_w - hint_surf.get_width() - 25, box_y + box_h - hint_surf.get_height() - 15))
                
            dialog_layer.set_alpha(int(self.dialogue_alpha))
            screen.blit(dialog_layer, (0, 0))
                
        if self.name_menu_alpha > 0:
            name_layer = pygame.Surface((screen_w, screen_h), pygame.SRCALPHA)
            
            intensity = 0.0
            target = "vesper"
            typed = self.typed_name.strip().lower()
            if target.startswith(typed) and len(typed) >= 3:
                linear_intensity = min(1.0, (len(typed) - 2) / 4.0)
                intensity = linear_intensity ** 2.0

            def lerp_c(c1, c2, t):
                if len(c1) == 3: c1 = (*c1, 255)
                if len(c2) == 3: c2 = (*c2, 255)
                return tuple(int(a + (b - a) * t) for a, b in zip(c1, c2))

            overlay = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
            overlay.fill(lerp_c((0, 0, 0, 180), (5, 0, 0, 210), intensity))
            name_layer.blit(overlay, (0, 0))
            
            time_sec = pygame.time.get_ticks() / 1000.0
            spacing_x = screen_w * 0.055
            spacing_y = screen_h * 0.06
            
            def project(lx, ly):
                jitter_mag = intensity * 0.03
                jitter = (random.random() - 0.5) * jitter_mag
                float_mag = 0.15 + intensity * 0.05
                float_y = math.sin(time_sec * (2.0 - 0.5*intensity) + lx * (0.5 + 0.2*intensity) + ly * (0.3 + 0.1*intensity)) * float_mag + jitter
                y3d = ly + float_y
                x3d = lx + jitter * 15.0
                
                x_norm = lx / 6.0
                z = (abs(x_norm)**1.5) * 0.8
                
                cam_z = 3.5
                perspective = cam_z / (cam_z - z)
                
                px = screen_w // 2 + x3d * spacing_x * perspective
                py = screen_h // 2 + y3d * spacing_y * perspective
                return px, py, perspective
                
            def apply_3d_skew(surface, lx, base_scale, is_action=False):
                w, h = surface.get_size()
                if w <= 0 or h <= 0: return surface
                
                def get_p(x_val):
                    x_n = x_val / 6.0
                    z_val = (abs(x_n)**1.5) * 0.8
                    return 3.5 / (max(0.1, 3.5 - z_val))
                    
                p_center = get_p(lx)
                span = 1.0 if is_action else 0.5
                p_left = get_p(lx - span)
                p_right = get_p(lx + span)
                
                norm_l = p_left / p_center
                norm_r = p_right / p_center
                
                tilt_w = max(0.4, 1.0 - (abs(lx) / 6.0) * 0.25)
                if is_action:
                    tilt_w *= 0.85
                scaled_w = max(1, int(w * base_scale * tilt_w))
                
                max_norm = max(norm_l, norm_r)
                new_h = int(h * base_scale * max_norm)
                if new_h <= 0: return surface
                
                new_surf = pygame.Surface((scaled_w, new_h), pygame.SRCALPHA)
                strips = min(scaled_w, 24 if is_action else 8)
                if strips <= 0: return new_surf
                
                strip_orig_w = w / strips
                strip_new_w = scaled_w / strips
                
                for j in range(strips):
                    orig_x = int(j * strip_orig_w)
                    orig_sw = int((j + 1) * strip_orig_w) - orig_x
                    if orig_sw <= 0: continue
                    
                    new_x = int(j * strip_new_w)
                    new_sw = int((j + 1) * strip_new_w) - new_x
                    if new_sw <= 0: continue
                    
                    progress = (j + 0.5) / strips
                    strip_scale = norm_l * (1.0 - progress) + norm_r * progress
                    
                    slice_h = max(1, int(h * base_scale * strip_scale))
                    slice_surf = surface.subsurface((orig_x, 0, orig_sw, h))
                    
                    scaled_slice = pygame.transform.scale(slice_surf, (new_sw, slice_h))
                    y_off = (new_h - slice_h) // 2
                    new_surf.blit(scaled_slice, (new_x, y_off))
                    
                return new_surf

            render_list = []
            for i, item in enumerate(self.name_items):
                px, py, scale = project(item["lx"], item["ly"])
                render_list.append((i, item, px, py, scale))
                
            render_list.sort(key=lambda x: abs(x[1]["lx"]))
            
            for i, item, px, py, scale in render_list:
                selected = (i == self.name_sel_idx)
                
                is_disabled = False
                if item["type"] == "action":
                    if item["text"] == "CONFIRM":
                        if len(self.typed_name.strip()) == 0:
                            base_c = (30, 30, 30, 150)
                            base_t = (100, 100, 100)
                            targ_c = (20, 10, 10, 150)
                            targ_t = (70, 40, 40)
                            is_disabled = True
                        else:
                            base_c = (80, 220, 80, 255) if selected else (40, 100, 40, 200)
                            base_t = (10, 40, 10) if selected else WHITE
                            targ_c = (120, 20, 20, 255) if selected else (40, 20, 20, 200)
                            targ_t = (255, 180, 180) if selected else (180, 120, 120)
                    elif item["text"] == "ERASE":
                        base_c = (255, 100, 100, 255) if selected else (100, 40, 40, 200)
                        base_t = (40, 10, 10) if selected else WHITE
                        targ_c = (120, 20, 20, 255) if selected else (40, 20, 20, 200)
                        targ_t = (255, 180, 180) if selected else (180, 120, 120)
                else:
                    base_c = (200, 230, 255, 255) if selected else (40, 40, 50, 180)
                    base_t = (10, 10, 20) if selected else (220, 220, 220)
                    targ_c = (100, 20, 20, 255) if selected else (20, 15, 15, 180)
                    targ_t = (255, 180, 180) if selected else (150, 130, 130)
                        
                color = lerp_c(base_c, targ_c, intensity)
                text_color = lerp_c(base_t, targ_t, intensity)
                
                font_to_use = self.name_font if item["type"] == "action" else self.font
                text_surf = font_to_use.render(item["text"], True, text_color)
                
                if item["type"] == "action":
                    padding_x = 24
                    padding_y = 12
                else:
                    padding_x = 16
                    padding_y = 8
                    
                max_shadow = 6
                is_pressed = selected and not is_disabled
                shadow_drop = 2 if is_pressed else max_shadow
                y_offset = max_shadow - shadow_drop

                bw = text_surf.get_width() + padding_x * 2
                bh = text_surf.get_height() + padding_y * 2
                base_surf = pygame.Surface((bw, bh + max_shadow), pygame.SRCALPHA)
                
                shadow_c_base = (max(0, base_c[0]-30), max(0, base_c[1]-30), max(0, base_c[2]-30), base_c[3])
                if is_disabled: shadow_c_base = (20, 20, 20, 150)
                shadow_c_targ = (max(0, targ_c[0]-20), max(0, targ_c[1]-20), max(0, targ_c[2]-20), targ_c[3])
                if is_disabled: shadow_c_targ = (10, 5, 5, 150)
                
                shadow_color = lerp_c(shadow_c_base, shadow_c_targ, intensity)
                
                pygame.draw.rect(base_surf, shadow_color, pygame.Rect(0, y_offset, bw, bh + shadow_drop), border_radius=8)
                
                top_rect = pygame.Rect(0, y_offset, bw, bh)
                pygame.draw.rect(base_surf, color, top_rect, border_radius=8)
                
                b_c_base = WHITE if is_pressed else ((80, 80, 90) if not is_disabled else (50, 50, 50))
                b_c_targ = (200, 80, 80) if is_pressed else ((60, 40, 40) if not is_disabled else (30, 15, 15))
                border_color = lerp_c(b_c_base, b_c_targ, intensity)
                
                pygame.draw.rect(base_surf, border_color, top_rect, width=2 if is_pressed else 1, border_radius=8)

                text_rect = text_surf.get_rect(center=(bw // 2, bh // 2 + y_offset))
                base_surf.blit(text_surf, text_rect)
                
                skewed_surf = apply_3d_skew(base_surf, item["lx"], scale, is_action=(item["type"] == "action"))
                
                if skewed_surf.get_width() > 0 and skewed_surf.get_height() > 0:
                    name_layer.blit(skewed_surf, skewed_surf.get_rect(center=(int(px), int(py))))
                    
            epx, epy, escale = project(0, -4.5)
            blink_freq = int(400 - 200 * intensity)
            show_cursor = "|" if (pygame.time.get_ticks() // max(1, blink_freq)) % 2 == 0 else ""
            typed_surf = self.name_font.render(self.typed_name + show_cursor, True, lerp_c(WHITE, (255, 200, 200), intensity))
            tw, th = int(typed_surf.get_width() * escale), int(typed_surf.get_height() * escale)
            if tw > 0 and th > 0:
                typed_surf = pygame.transform.smoothscale(typed_surf, (tw, th))
                typed_rect = typed_surf.get_rect(center=(int(epx), int(epy)))
                box_rect = typed_rect.inflate(int(80 * escale), int(20 * escale))
                box_rect.width = max(box_rect.width, int(250 * escale))
                box_rect.center = (int(epx), int(epy))
                
                tbox_bg = lerp_c((30, 30, 40, 200), (20, 10, 10, 220), intensity)
                tbox_bd = lerp_c((100, 150, 255), (120, 40, 40), intensity)
                
                pygame.draw.rect(name_layer, tbox_bg, box_rect, border_radius=int(8*escale))
                pygame.draw.rect(name_layer, tbox_bd, box_rect, max(1, int(2*escale)), border_radius=int(8*escale))
                name_layer.blit(typed_surf, typed_rect)
                
            tpx, tpy, tscale = project(0, -6.0)
            title_surf = self.name_font.render("Who are you?", True, lerp_c((200, 200, 200), (160, 120, 120), intensity))
            tiw, tih = int(title_surf.get_width() * tscale), int(title_surf.get_height() * tscale)
            if tiw > 0 and tih > 0:
                title_surf = pygame.transform.smoothscale(title_surf, (tiw, tih))
                
                if intensity > 0:
                    title_shadow = self.name_font.render("Who are you?", True, (100, 20, 20))
                    title_shadow = pygame.transform.smoothscale(title_shadow, (tiw, tih))
                    title_shadow.set_alpha(int(255 * intensity))
                    jitter_tx = (random.random() - 0.5) * 6.0 * tscale * intensity
                    jitter_ty = (random.random() - 0.5) * 6.0 * tscale * intensity
                    name_layer.blit(title_shadow, title_shadow.get_rect(center=(int(tpx + jitter_tx), int(tpy + jitter_ty))))
                    
                name_layer.blit(title_surf, title_surf.get_rect(center=(int(tpx), int(tpy))))

            name_layer.set_alpha(int(self.name_menu_alpha))
            screen.blit(name_layer, (0, 0))

        if getattr(self, "ui_mode", "") in ("VESPER_CONFIRM", "CRASH_SEQUENCE"):
            if self.ui_mode == "VESPER_CONFIRM":
                glitch_intensity = 0.2 + random.random() * 0.3
                if random.random() < glitch_intensity:
                    for _ in range(random.randint(5, 20)):
                        gx = random.randint(0, screen_w)
                        gy = random.randint(0, screen_h)
                        gw = random.randint(50, 400)
                        gh = random.randint(10, 60)
                        pygame.draw.rect(screen, (random.randint(150, 255), 0, 0, 100), (gx, gy, gw, gh))
                    for _ in range(random.randint(2, 10)):
                        sy = random.randint(0, screen_h - 1)
                        sh = random.randint(10, 80)
                        shift = random.randint(-40, 40)
                        if sh > 0 and sy + sh <= screen_h:
                            chunk = screen.subsurface((0, sy, screen_w, sh)).copy()
                            screen.blit(chunk, (shift, sy))

            dialog_w, dialog_h = int(screen_w * 0.6), int(screen_h * 0.45)
            dx, dy = (screen_w - dialog_w) // 2, (screen_h - dialog_h) // 2
            
            glitch_x, glitch_y = 0, 0
            if self.ui_mode in ("CRASH_SEQUENCE", "VESPER_CONFIRM"):
                glitch_x = random.randint(-8, 8)
                glitch_y = random.randint(-8, 8)
                
            dialog_rect = pygame.Rect(dx + glitch_x, dy + glitch_y, dialog_w, dialog_h)
            
            overlay = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
            overlay.fill((30, 0, 0, 150))
            screen.blit(overlay, (0, 0))

            pygame.draw.rect(screen, (15, 5, 5, 240), dialog_rect, border_radius=15)
            pygame.draw.rect(screen, (200, 30, 30), dialog_rect, width=3, border_radius=15)
            
            if self.ui_mode in ("CRASH_SEQUENCE", "VESPER_CONFIRM"):
                for _ in range(8):
                    line_y = random.randint(dy + glitch_y, dy + glitch_y + dialog_h)
                    pygame.draw.line(screen, (255, 50, 50), (dx + glitch_x, line_y), (dx + glitch_x + dialog_w, line_y), 1)
            
            title_text_1 = "To claim this name is to surrender the self."
            title_text_2 = "Two minds cannot occupy a single vessel."
            sub_text = "DO YOU WISH TO PROCEED?"
            
            chars_to_show = getattr(self, "vesper_warning_chars", 0)
            if self.ui_mode == "CRASH_SEQUENCE":
                chars_to_show = len(title_text_1) + len(title_text_2) + len(sub_text)
                
            def get_substring(text, start_idx, allowed_chars):
                if allowed_chars <= start_idx:
                    return ""
                return text[:allowed_chars - start_idx]

            disp_title_1 = get_substring(title_text_1, 0, chars_to_show)
            disp_title_2 = get_substring(title_text_2, len(title_text_1), chars_to_show)
            disp_sub = get_substring(sub_text, len(title_text_1) + len(title_text_2), chars_to_show)
            
            if disp_title_1:
                title1 = self.font.render(disp_title_1, True, (255, 80, 80))
                title1_shadow = self.font.render(disp_title_1, True, (120, 0, 0))
                screen.blit(title1_shadow, title1_shadow.get_rect(center=(dx + glitch_x + dialog_w // 2 + random.randint(-3, 3), dy + glitch_y + int(dialog_h * 0.25) + random.randint(-3, 3))))
                screen.blit(title1, title1.get_rect(center=(dx + glitch_x + dialog_w // 2, dy + glitch_y + int(dialog_h * 0.25))))

            if disp_title_2:
                title2 = self.font.render(disp_title_2, True, (255, 80, 80))
                title2_shadow = self.font.render(disp_title_2, True, (120, 0, 0))
                screen.blit(title2_shadow, title2_shadow.get_rect(center=(dx + glitch_x + dialog_w // 2 + random.randint(-3, 3), dy + glitch_y + int(dialog_h * 0.40) + random.randint(-3, 3))))
                screen.blit(title2, title2.get_rect(center=(dx + glitch_x + dialog_w // 2, dy + glitch_y + int(dialog_h * 0.40))))
            
            if disp_sub:
                sub = self.font.render(disp_sub, True, (200, 50, 50))
                sub_shadow = self.font.render(disp_sub, True, (100, 0, 0))
                screen.blit(sub_shadow, sub_shadow.get_rect(center=(dx + glitch_x + dialog_w // 2 + random.randint(-2, 2), dy + glitch_y + int(dialog_h * 0.60) + random.randint(-2, 2))))
                screen.blit(sub, sub.get_rect(center=(dx + glitch_x + dialog_w // 2, dy + glitch_y + int(dialog_h * 0.60))))

            show_buttons = getattr(self, "vesper_warning_timer", 0) > 7000 or self.ui_mode == "CRASH_SEQUENCE"
            if show_buttons:
                anim_t = 1.0
                if self.ui_mode == "VESPER_CONFIRM":
                    anim_t = min(1.0, (getattr(self, "vesper_warning_timer", 0) - 7000) / 1000.0)
                
                btn_layer = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
                
                yes_color = (180, 30, 30) if getattr(self, "vesper_confirm_sel", 1) == 0 else (50, 10, 10)
                no_color = (180, 30, 30) if getattr(self, "vesper_confirm_sel", 1) == 1 else (50, 10, 10)
                
                yes_off, no_off = getattr(self, "btn_offsets", [(0,0), (0,0)])
                slide_y = int((1.0 - anim_t) * 30)
                
                yes_rect = pygame.Rect(dx + glitch_x + int(dialog_w * 0.2) + yes_off[0], dy + glitch_y + int(dialog_h * 0.75) + yes_off[1] + slide_y, 120, 45)
                no_rect = pygame.Rect(dx + glitch_x + int(dialog_w * 0.8) - 120 + no_off[0], dy + glitch_y + int(dialog_h * 0.75) + no_off[1] + slide_y, 120, 45)
                
                pygame.draw.rect(btn_layer, yes_color, yes_rect, border_radius=6)
                if getattr(self, "vesper_confirm_sel", 1) == 0:
                    pygame.draw.rect(btn_layer, (255, 100, 100), yes_rect, width=2, border_radius=6)
                else:
                    pygame.draw.rect(btn_layer, (100, 30, 30), yes_rect, width=1, border_radius=6)
                yes_text = self.font.render("YES", True, WHITE if getattr(self, "vesper_confirm_sel", 1) == 0 else (150, 150, 150))
                btn_layer.blit(yes_text, yes_text.get_rect(center=yes_rect.center))
                
                pygame.draw.rect(btn_layer, no_color, no_rect, border_radius=6)
                if getattr(self, "vesper_confirm_sel", 1) == 1:
                    pygame.draw.rect(btn_layer, (255, 100, 100), no_rect, width=2, border_radius=6)
                else:
                    pygame.draw.rect(btn_layer, (100, 30, 30), no_rect, width=1, border_radius=6)
                no_text = self.font.render("NO", True, WHITE if getattr(self, "vesper_confirm_sel", 1) == 1 else (150, 150, 150))
                btn_layer.blit(no_text, no_text.get_rect(center=no_rect.center))
                
                btn_layer.set_alpha(int(anim_t * 255))
                screen.blit(btn_layer, (0, 0))

        if getattr(self, "ui_mode", "") == "CRASH_SEQUENCE":
            intensity = getattr(self, "crash_timer", 0) / 3000.0
            
            num_glitches = int(intensity * 80)
            for _ in range(num_glitches):
                gx = random.randint(0, screen_w)
                gy = random.randint(0, screen_h)
                gw = random.randint(10, 300)
                gh = random.randint(5, 50)
                pygame.draw.rect(screen, (random.randint(150, 255), 0, 0), (gx, gy, gw, gh))
            
            for _ in range(int(intensity * 30)):
                sy = random.randint(0, screen_h - 1)
                sh = random.randint(10, min(100, screen_h - sy))
                shift = random.randint(-50, 50)
                if sh > 0 and sy + sh <= screen_h:
                    chunk = screen.subsurface((0, sy, screen_w, sh)).copy()
                    screen.blit(chunk, (shift, sy))
            
            crash_overlay = pygame.Surface((screen_w, screen_h), pygame.SRCALPHA)
            crash_overlay.fill((255, 0, 0, int(intensity * 120)))
            screen.blit(crash_overlay, (0, 0))

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
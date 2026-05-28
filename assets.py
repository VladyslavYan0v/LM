import os
import pickle
import sys
import pygame


class AssetManager:
    def __init__(self):
        if getattr(sys, 'frozen', False):
            base_dir = getattr(sys, '_MEIPASS', os.path.dirname(__file__))
            settings_dir = os.path.dirname(sys.executable)
        else:
            base_dir = os.path.dirname(__file__)
            settings_dir = base_dir

        self.root = os.path.join(base_dir, "embed")
        self.settings_file = os.path.join(settings_dir, "settings.dat")
        self.cache = {}

        self.music_vol = 0.6
        self.sfx_vol = 0.7
        self.res_index = 0
        self.last_windowed_index = 1
        self.is_fullscreen = False

        self.load_settings()

    def load_settings(self):
        if not os.path.exists(self.settings_file):
            return

        try:
            with open(self.settings_file, "rb") as file_handle:
                data = pickle.load(file_handle)
        except Exception:
            self.reset_settings()
            return

        self.music_vol = data.get("music_vol", self.music_vol)
        self.sfx_vol = data.get("sfx_vol", self.sfx_vol)
        self.res_index = data.get("res_index", self.res_index)
        self.is_fullscreen = data.get("is_fullscreen", self.is_fullscreen)
        self.last_windowed_index = data.get("last_windowed_index", self.last_windowed_index)
        self.last_windowed_index = self.last_windowed_index if self.last_windowed_index < 4 else 1

        try:
            pygame.mixer.music.set_volume(self.music_vol)
        except Exception:
            pass

    def save_settings(self):
        try:
            with open(self.settings_file, "wb") as file_handle:
                pickle.dump({
                    "music_vol": self.music_vol,
                    "sfx_vol": self.sfx_vol,
                    "res_index": self.res_index,
                    "is_fullscreen": self.is_fullscreen,
                    "last_windowed_index": self.last_windowed_index,
                }, file_handle)
        except Exception:
            pass

    def reset_settings(self):
        self.music_vol = 0.6
        self.sfx_vol = 0.7
        self.res_index = 0
        self.last_windowed_index = 0
        self.is_fullscreen = False
        try:
            pygame.mixer.music.set_volume(self.music_vol)
        except Exception:
            pass
        self.save_settings()

    def set_music_volume(self, volume):
        self.music_vol = max(0.0, min(1.0, volume))
        try:
            pygame.mixer.music.set_volume(self.music_vol)
        except Exception:
            pass
        self.save_settings()

    def set_sfx_volume(self, volume):
        self.sfx_vol = max(0.0, min(1.0, volume))
        self.save_settings()

    def set_video_settings(self, res_index, is_fullscreen):
        self.res_index = res_index
        self.is_fullscreen = is_fullscreen
        if res_index < 3:
            self.last_windowed_index = res_index
        self.save_settings()

    def _get_path(self, *path_parts):
        return os.path.join(self.root, *path_parts)

    def get_image(self, *path_parts):
        full_path = self._get_path(*path_parts)
        if full_path in self.cache:
            return self.cache[full_path]

        try:
            image = pygame.image.load(full_path)
            try:
                image = image.convert_alpha()
            except Exception:
                image = image.convert()
            self.cache[full_path] = image
            return image
        except Exception:
            return None

    def play_music(self, *path_parts):
        try:
            pygame.mixer.music.load(self._get_path(*path_parts))
            pygame.mixer.music.set_volume(self.music_vol)
            pygame.mixer.music.play(-1)
        except Exception:
            pass

    def play_sfx(self, *path_parts):
        try:
            full_path = self._get_path(*path_parts)
            if full_path not in self.cache:
                self.cache[full_path] = pygame.mixer.Sound(full_path)
            sound = self.cache[full_path]
            sound.set_volume(self.sfx_vol)
            sound.play()
        except Exception:
            pass

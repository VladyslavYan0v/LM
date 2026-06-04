import os
import struct
import pygame
import math
from assets import AssetManager
from constants import WHITE, ScreenState, get_font


class RoomMap:
    TILE_FLOOR = 1
    TILE_WALL = 2
    TILE_DOOR_CLOSED = 3
    TILE_DOOR_OPEN = 4
    TILE_PORTAL = 5
    TILE_PORTAL_INVERTED = 6

    TILE_COLORS = {
        0: (15, 15, 35),
        TILE_FLOOR: (60, 120, 180),
        TILE_WALL: (80, 80, 80),
        TILE_DOOR_CLOSED: (140, 50, 50),
        TILE_DOOR_OPEN: (200, 180, 80),
        TILE_PORTAL: (140, 120, 220),
        TILE_PORTAL_INVERTED: (120, 220, 200),
    }

    TILE_COLORS_INVERTED = {
        TILE_FLOOR: TILE_COLORS[TILE_WALL],
        TILE_WALL: TILE_COLORS[TILE_FLOOR],
        TILE_DOOR_CLOSED: TILE_COLORS[TILE_FLOOR],
        TILE_DOOR_OPEN: TILE_COLORS[TILE_WALL],
        TILE_PORTAL: TILE_COLORS[TILE_PORTAL_INVERTED],
        TILE_PORTAL_INVERTED: TILE_COLORS[TILE_PORTAL],
    }

    TILE_ASSETS = {
        TILE_FLOOR: ("rooms", "floor.png"),
        TILE_WALL: ("rooms", "wall.png"),
        TILE_PORTAL: ("rooms", "portal.png"),
        TILE_PORTAL_INVERTED: ("rooms", "portal_inverted.png"),
    }

    INVERTED_TILE_ASSETS = {
        TILE_FLOOR: ("rooms", "floor_inverted.png"),
        TILE_WALL: ("rooms", "wall_inverted.png"),
        TILE_PORTAL: ("rooms", "portal_inverted.png"),
        TILE_PORTAL_INVERTED: ("rooms", "portal.png"),
    }

    def __init__(self, assets: AssetManager, filename: str):
        self.assets = assets
        self.filename = filename
        self.width = 0
        self.height = 0
        self.start_x = 0
        self.start_y = 0
        self.grid = []
        self.tile_images = {}
        self.inverted_tile_images = {}
        self.load(filename)

    def load(self, filename: str):
        room_path = os.path.join(self.assets.root, "rooms", filename)
        if not os.path.exists(room_path):
            raise FileNotFoundError(f"Room file not found: {room_path}")

        with open(room_path, "rb") as file_handle:
            header = file_handle.read(8)
            if len(header) != 8:
                raise ValueError("Room file header is too short")
            self.width, self.height, self.start_x, self.start_y = struct.unpack("<HHHH", header)
            raw = file_handle.read(self.width * self.height)
            if len(raw) != self.width * self.height:
                raise ValueError("Room file data length does not match width*height")
            self.grid = [list(raw[row_start : row_start + self.width]) for row_start in range(0, len(raw), self.width)]

        for tile_id, path_parts in self.TILE_ASSETS.items():
            self.tile_images[tile_id] = self.assets.get_image(*path_parts)
        for tile_id, path_parts in self.INVERTED_TILE_ASSETS.items():
            self.inverted_tile_images[tile_id] = self.assets.get_image(*path_parts)

    def get_tile(self, x: int, y: int, inverted: bool = False) -> int:
        if x < 0 or y < 0 or x >= self.width or y >= self.height:
            return 0
        tile = self.grid[y][x]
        if inverted:
            return self.invert_tile(tile)
        return tile

    @staticmethod
    def invert_tile(tile_id: int) -> int:
        if tile_id == RoomMap.TILE_FLOOR:
            return RoomMap.TILE_WALL
        if tile_id == RoomMap.TILE_WALL:
            return RoomMap.TILE_FLOOR
        if tile_id == RoomMap.TILE_DOOR_CLOSED:
            return RoomMap.TILE_DOOR_OPEN
        if tile_id == RoomMap.TILE_DOOR_OPEN:
            return RoomMap.TILE_DOOR_CLOSED
        if tile_id == RoomMap.TILE_PORTAL:
            return RoomMap.TILE_PORTAL_INVERTED
        if tile_id == RoomMap.TILE_PORTAL_INVERTED:
            return RoomMap.TILE_PORTAL
        return tile_id

    def is_walkable(self, x: int, y: int, inverted: bool = False) -> bool:
        tile = self.get_tile(x, y, inverted)
        if tile == 0:
            return False
        if tile == self.TILE_FLOOR:
            return True
        if tile == self.TILE_WALL:
            return False
        if tile == self.TILE_DOOR_CLOSED:
            return False
        if tile == self.TILE_DOOR_OPEN:
            return True
        if tile == self.TILE_PORTAL or tile == self.TILE_PORTAL_INVERTED:
            return True
        return False

    def get_tile_image(self, tile_id: int, inverted: bool = False):
        if inverted:
            if tile_id == self.TILE_FLOOR:
                return self.inverted_tile_images.get(self.TILE_WALL) or self.tile_images.get(self.TILE_WALL)
            if tile_id == self.TILE_WALL:
                return self.inverted_tile_images.get(self.TILE_FLOOR) or self.tile_images.get(self.TILE_FLOOR)
            if tile_id == self.TILE_DOOR_CLOSED:
                return self.inverted_tile_images.get(self.TILE_FLOOR) or self.tile_images.get(self.TILE_FLOOR)
            if tile_id == self.TILE_DOOR_OPEN:
                return self.inverted_tile_images.get(self.TILE_WALL) or self.tile_images.get(self.TILE_WALL)
            if tile_id == self.TILE_PORTAL:
                return self.inverted_tile_images.get(self.TILE_PORTAL) or self.tile_images.get(self.TILE_PORTAL)
            if tile_id == self.TILE_PORTAL_INVERTED:
                return self.inverted_tile_images.get(self.TILE_PORTAL_INVERTED) or self.tile_images.get(self.TILE_PORTAL_INVERTED)
            return self.inverted_tile_images.get(tile_id) or self.tile_images.get(tile_id)

        if tile_id == self.TILE_DOOR_CLOSED:
            return self.tile_images.get(self.TILE_WALL)
        if tile_id == self.TILE_DOOR_OPEN:
            return self.tile_images.get(self.TILE_FLOOR)
        return self.tile_images.get(tile_id)

    def get_tile_color(self, tile_id: int, inverted: bool = False):
        if inverted:
            return self.TILE_COLORS_INVERTED.get(tile_id, WHITE)
        return self.TILE_COLORS.get(tile_id, WHITE)

    def is_portal_origin(self, x: int, y: int) -> bool:
        if x < 0 or y < 0 or x >= self.width or y >= self.height:
            return False
        tile_id = self.grid[y][x]
        if tile_id not in (self.TILE_PORTAL, self.TILE_PORTAL_INVERTED):
            return False
        if x > 0 and self.grid[y][x - 1] in (self.TILE_PORTAL, self.TILE_PORTAL_INVERTED):
            return False
        if y > 0 and self.grid[y - 1][x] in (self.TILE_PORTAL, self.TILE_PORTAL_INVERTED):
            return False
        return True


class RoomState:
    MOVE_KEYS = {
        pygame.K_UP: (0, -1),
        pygame.K_w: (0, -1),
        pygame.K_DOWN: (0, 1),
        pygame.K_s: (0, 1),
        pygame.K_LEFT: (-1, 0),
        pygame.K_a: (-1, 0),
        pygame.K_RIGHT: (1, 0),
        pygame.K_d: (1, 0),
    }

    def __init__(self, assets: AssetManager):
        self.assets = assets
        self.pending_command = None
        self.room_map = None
        self.current_level_idx = 0
        self.player_x = 0
        self.player_y = 0
        self.world_inverted = False
        self.tile_size = 32
        self.offset = (0, 0)
        self.font = None
        self.hint_font = None
        self.player_facing = 1
        self.player_sprite = None
        self.move_this_frame = False
        self.distortion_intensity = 0.0
        self.time_elapsed = 0.0
        self.render_surface = None
        self.fade_alpha = 255
        self.fade_direction = -1
        self.level_complete = False
        self.transition_target = None
        self.menu_btn_rect = pygame.Rect(0, 0, 1, 1)
        self.next_btn_rect = pygame.Rect(0, 0, 1, 1)
        sprite_candidates = [
            os.path.join(self.assets.root, "hero", "hero.png"),
            os.path.join(self.assets.root, "rooms", "player.png"),
            os.path.join(self.assets.root, "rooms", "hero.png"),
            os.path.join(self.assets.root, "rooms", "character.png"),
            os.path.join(self.assets.root, "rooms", "hero_idle.png"),
        ]
        for candidate in sprite_candidates:
            if os.path.exists(candidate):
                relative_dir = os.path.relpath(os.path.dirname(candidate), self.assets.root)
                self.player_sprite = self.assets.get_image(relative_dir, os.path.basename(candidate))
                break

    def clear_pending_command(self):
        self.pending_command = None

    def setup_level(self, level_index: int):
        self.current_level_idx = level_index
        filenames = {0: "tutorial.dat", 1: "level1.dat", 2: "level2.dat", 3: "level3.dat"}
        filename = filenames.get(level_index, "tutorial.dat")
        
        try:
            self.room_map = RoomMap(self.assets, filename)
        except FileNotFoundError:
            print(f"Level {filename} not found, falling back to level1.dat")
            self.room_map = RoomMap(self.assets, "level1.dat")
            
        self.fade_alpha = 255
        self.fade_direction = -1
        self.level_complete = False
        self.transition_target = None
        self.assets.play_music("music", "Through_the_Hollow_Arch.flac")
        self.reset()

    def reset(self):
        if not self.room_map:
            return
        self.player_x = self.room_map.start_x
        self.player_y = self.room_map.start_y
        self.world_inverted = False
        self.player_facing = 1
        self.move_this_frame = False
        self.distortion_intensity = 0.0
        self.time_elapsed = 0.0

    def resize(self, width: int, height: int):
        self.tile_size = max(48, int(height * 0.08))
        self.font = get_font(max(16, int(height * 0.035)))
        self.hint_font = get_font(max(14, int(height * 0.025)))
        
        btn_width = int(width * 0.25)
        btn_height = int(height * 0.08)
        self.menu_btn_rect = pygame.Rect(0, 0, btn_width, btn_height)
        self.menu_btn_rect.center = (width // 2 - int(btn_width * 0.6), height // 2 + int(height * 0.1))
        self.next_btn_rect = pygame.Rect(0, 0, btn_width, btn_height)
        self.next_btn_rect.center = (width // 2 + int(btn_width * 0.6), height // 2 + int(height * 0.1))

    def handle_event(self, event):
        if self.fade_direction == 1:
            return None
            
        if self.level_complete:
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if self.menu_btn_rect.collidepoint(event.pos):
                    self.assets.play_sfx("sfx", "click.wav")
                    pygame.mixer.music.fadeout(1000)
                    self.transition_target = "GOTO_MAIN_MENU"
                    self.fade_direction = 1
                elif self.next_btn_rect.collidepoint(event.pos) and self.current_level_idx < 3:
                    self.assets.play_sfx("sfx", "click.wav")
                    pygame.mixer.music.fadeout(1000)
                    self.transition_target = ("START_STORY", self.current_level_idx + 1)
                    self.fade_direction = 1
            return None

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                return ScreenState.PAUSE_MENU

            if event.key == pygame.K_i:
                self.world_inverted = not self.world_inverted
                self.assets.play_sfx("sfx", "click.wav")
                return None
                
            if event.key == pygame.K_p:
                self.level_complete = True
                self.assets.max_unlocked_level = max(self.assets.max_unlocked_level, self.current_level_idx + 1)
                self.assets.save_settings()
                self.assets.play_sfx("sfx", "click.wav")
                return None

        return None

    def update(self, dt, mouse_pos):
        if self.fade_direction == -1:
            self.fade_alpha = max(0, self.fade_alpha - dt * 0.25)
            if self.fade_alpha == 0:
                self.fade_direction = 0
        elif self.fade_direction == 1:
            self.fade_alpha = min(255, self.fade_alpha + dt * 0.25)
            if self.fade_alpha == 255:
                self.fade_direction = 0
                self.pending_command = self.transition_target
                self.transition_target = None
            return
            
        if self.level_complete:
            return

        self.time_elapsed += dt
        if self.world_inverted:
            self.distortion_intensity = min(1.0, self.distortion_intensity + dt * 0.0015)
        else:
            self.distortion_intensity = max(0.0, self.distortion_intensity - dt * 0.0015)

        keys = pygame.key.get_pressed()
        
        pressed_moves = []
        for key, (dx, dy) in self.MOVE_KEYS.items():
            if keys[key]:
                pressed_moves.append((dx, dy))
        
        if pressed_moves and not self.move_this_frame:
            dx, dy = pressed_moves[0]
            target_x = self.player_x + dx
            target_y = self.player_y + dy
            if self.room_map.is_walkable(target_x, target_y, self.world_inverted):
                if dx < 0:
                    self.player_facing = -1
                elif dx > 0:
                    self.player_facing = 1
                self.player_x = target_x
                self.player_y = target_y
                self.move_this_frame = True
                tile_id = self.room_map.get_tile(target_x, target_y, False)
                if tile_id == self.room_map.TILE_PORTAL or tile_id == self.room_map.TILE_PORTAL_INVERTED:
                    self.world_inverted = not self.world_inverted
                    self.assets.play_sfx("sfx", "click.wav")
        
        if not keys[pygame.K_UP] and not keys[pygame.K_w] and not keys[pygame.K_DOWN] and not keys[pygame.K_s] and not keys[pygame.K_LEFT] and not keys[pygame.K_a] and not keys[pygame.K_RIGHT] and not keys[pygame.K_d]:
            self.move_this_frame = False

    def draw(self, screen):
        if not self.room_map:
            return
            
        screen_width, screen_height = screen.get_size()

        map_pixel_width = self.room_map.width * self.tile_size
        map_pixel_height = self.room_map.height * self.tile_size
        
        player_pixel_x = self.player_x * self.tile_size + self.tile_size // 2
        player_pixel_y = self.player_y * self.tile_size + self.tile_size // 2

        camera_x = player_pixel_x - screen_width // 2
        camera_y = player_pixel_y - screen_height // 2

        camera_x = max(0, min(camera_x, map_pixel_width - screen_width))
        camera_y = max(0, min(camera_y, map_pixel_height - screen_height))

        if map_pixel_width < screen_width:
            camera_x = -(screen_width - map_pixel_width) // 2
        if map_pixel_height < screen_height:
            camera_y = -(screen_height - map_pixel_height) // 2

        self.offset = (-camera_x, -camera_y)

        if self.distortion_intensity > 0:
            if self.render_surface is None or self.render_surface.get_size() != screen.get_size():
                self.render_surface = pygame.Surface(screen.get_size())
            draw_surface = self.render_surface
        else:
            draw_surface = screen

        draw_surface.fill((10, 10, 20))

        for y in range(self.room_map.height):
            for x in range(self.room_map.width):
                raw_tile = self.room_map.grid[y][x]
                rect = pygame.Rect(
                    self.offset[0] + x * self.tile_size,
                    self.offset[1] + y * self.tile_size,
                    self.tile_size,
                    self.tile_size,
                )

                if raw_tile in (self.room_map.TILE_PORTAL, self.room_map.TILE_PORTAL_INVERTED):
                    if self.room_map.is_portal_origin(x, y):
                        portal_rect = pygame.Rect(rect.x, rect.y, self.tile_size * 2, self.tile_size * 2)
                        portal_image = self.room_map.get_tile_image(raw_tile, self.world_inverted)
                        if portal_image:
                            portal_image = pygame.transform.smoothscale(portal_image, (portal_rect.width, portal_rect.height))
                            draw_surface.blit(portal_image, portal_rect)
                        else:
                            pygame.draw.rect(draw_surface, self.room_map.get_tile_color(raw_tile, self.world_inverted), portal_rect)
                    else:
                        continue
                else:
                    image = self.room_map.get_tile_image(raw_tile, self.world_inverted)
                    if image:
                        image = pygame.transform.smoothscale(image, (self.tile_size, self.tile_size))
                        draw_surface.blit(image, rect)
                    else:
                        pygame.draw.rect(draw_surface, self.room_map.get_tile_color(raw_tile, self.world_inverted), rect)

        player_rect = pygame.Rect(
            self.offset[0] + self.player_x * self.tile_size,
            self.offset[1] + self.player_y * self.tile_size,
            self.tile_size,
            self.tile_size,
        )
        if self.player_sprite:
            sprite = pygame.transform.smoothscale(self.player_sprite, (self.tile_size, self.tile_size))
            if self.player_facing < 0:
                sprite = pygame.transform.flip(sprite, True, False)
            sprite_rect = sprite.get_rect(center=player_rect.center)
            draw_surface.blit(sprite, sprite_rect)
        else:
            pygame.draw.circle(
                draw_surface,
                (240, 240, 240),
                player_rect.center,
                self.tile_size // 3,
            )
            
        if self.distortion_intensity > 0:
            time_sec = self.time_elapsed / 1000.0
            amplitude = 6 * self.distortion_intensity
            frequency = 0.05
            speed = 5.0
            strip_height = 4
            for y_pos in range(0, screen_height, strip_height):
                offset_x = int(math.sin(y_pos * frequency + time_sec * speed) * amplitude)
                screen.blit(draw_surface, (offset_x, y_pos), (0, y_pos, screen_width, strip_height))

        if self.font:
            level_name = "Tutorial" if self.current_level_idx == 0 else f"Level {self.current_level_idx}"
            title = f"{level_name}"
            text_surface = self.font.render(title, True, WHITE)
            screen.blit(text_surface, (20, 20))

            state_text = "INVERTED" if self.world_inverted else "NORMAL"
            state_surface = self.hint_font.render(f"World: {state_text}", True, WHITE)
            screen.blit(state_surface, (20, 60))

            hint_surface = self.hint_font.render("Use WASD/arrows to move, I to invert, ESC for Pause. Press 'P' to cheat win.", True, WHITE)
            screen.blit(hint_surface, (20, screen.get_height() - 40))
            
        if self.level_complete:
            overlay = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 180))
            screen.blit(overlay, (0, 0))

            title_surface = self.font.render("LEVEL COMPLETED!", True, (100, 255, 100))
            screen.blit(title_surface, title_surface.get_rect(center=(screen_width // 2, screen_height // 2 - int(screen_height * 0.15))))

            mouse_pos = pygame.mouse.get_pos()
            self._draw_button(screen, self.menu_btn_rect, "Main Menu", mouse_pos, (180, 40, 40))
            if self.current_level_idx < 3:
                self._draw_button(screen, self.next_btn_rect, "Next Level", mouse_pos, (60, 160, 80))

        if self.fade_alpha > 0:
            fade_surface = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
            fade_surface.fill((0, 0, 0, min(255, int(self.fade_alpha))))
            screen.blit(fade_surface, (0, 0))

    def _draw_button(self, screen, rect, label, mouse_pos, base_color):
        hovered = rect.collidepoint(mouse_pos)
        color = tuple(min(value + 40, 255) for value in base_color) if hovered else base_color
        pygame.draw.rect(screen, color, rect, border_radius=10)
        if self.hint_font:
            label_surface = self.hint_font.render(label, True, WHITE)
            screen.blit(label_surface, label_surface.get_rect(center=rect.center))

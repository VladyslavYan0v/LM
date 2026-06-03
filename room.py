import os
import struct
import pygame
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
        self.grid = []
        self.tile_images = {}
        self.inverted_tile_images = {}
        self.load(filename)

    def load(self, filename: str):
        room_path = os.path.join(self.assets.root, "rooms", filename)
        if not os.path.exists(room_path):
            raise FileNotFoundError(f"Room file not found: {room_path}")

        with open(room_path, "rb") as file_handle:
            header = file_handle.read(4)
            if len(header) != 4:
                raise ValueError("Room file header is too short")
            self.width, self.height = struct.unpack("<HH", header)
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
        self.room_map = RoomMap(self.assets, "level1.dat")
        self.player_x = 1
        self.player_y = 3
        self.world_inverted = False
        self.tile_size = 32
        self.offset = (0, 0)
        self.font = None
        self.hint_font = None
        self.player_facing = 1
        self.player_sprite = None
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

    def resize(self, width: int, height: int):
        self.tile_size = min(width // self.room_map.width, height // self.room_map.height)
        self.tile_size = max(32, min(self.tile_size, 96))
        grid_width = self.tile_size * self.room_map.width
        grid_height = self.tile_size * self.room_map.height
        self.offset = ((width - grid_width) // 2, (height - grid_height) // 2)
        self.font = get_font(max(16, int(height * 0.035)))
        self.hint_font = get_font(max(14, int(height * 0.025)))

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                return ScreenState.MAIN_MENU

            if event.key == pygame.K_i:
                self.world_inverted = not self.world_inverted
                self.assets.play_sfx("sfx", "click.wav")
                return None

            if event.key in self.MOVE_KEYS:
                dx, dy = self.MOVE_KEYS[event.key]
                target_x = self.player_x + dx
                target_y = self.player_y + dy
                if self.room_map.is_walkable(target_x, target_y, self.world_inverted):
                    if dx < 0:
                        self.player_facing = -1
                    elif dx > 0:
                        self.player_facing = 1
                    self.player_x = target_x
                    self.player_y = target_y
                    tile_id = self.room_map.get_tile(target_x, target_y, False)
                    if tile_id == self.room_map.TILE_PORTAL or tile_id == self.room_map.TILE_PORTAL_INVERTED:
                        self.world_inverted = not self.world_inverted
                        self.assets.play_sfx("sfx", "click.wav")
                return None

        return None

    def update(self, dt, mouse_pos):
        pass

    def draw(self, screen):
        screen.fill((10, 10, 20))

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
                            screen.blit(portal_image, portal_rect)
                        else:
                            pygame.draw.rect(screen, self.room_map.get_tile_color(raw_tile, self.world_inverted), portal_rect)
                    else:
                        # Skip internal portal blocks; the full 2x2 portal is drawn once from its top-left origin.
                        continue
                else:
                    image = self.room_map.get_tile_image(raw_tile, self.world_inverted)
                    if image:
                        image = pygame.transform.smoothscale(image, (self.tile_size, self.tile_size))
                        screen.blit(image, rect)
                    else:
                        pygame.draw.rect(screen, self.room_map.get_tile_color(raw_tile, self.world_inverted), rect)

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
            screen.blit(sprite, sprite_rect)
        else:
            pygame.draw.circle(
                screen,
                (240, 240, 240),
                player_rect.center,
                self.tile_size // 3,
            )

        if self.font:
            title = "Level 1 — World inversion demo"
            text_surface = self.font.render(title, True, WHITE)
            screen.blit(text_surface, (20, 20))

            state_text = "INVERTED" if self.world_inverted else "NORMAL"
            state_surface = self.hint_font.render(f"World: {state_text}", True, WHITE)
            screen.blit(state_surface, (20, 60))

            hint_surface = self.hint_font.render("Use WASD/arrow keys to move, I to invert world, ESC to return", True, WHITE)
            screen.blit(hint_surface, (20, screen.get_height() - 40))

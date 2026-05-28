import pygame
from constants import STAR_FRAME_DURATION


class HorizontalSlider:
    def __init__(self, label, x, y, width, initial_value=0.6):
        self.label = label
        self.rect = pygame.Rect(x, y, width, 10)
        self.value = initial_value
        self.dragging = False

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.inflate(30, 50).collidepoint(event.pos):
                self.dragging = True

        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            self.dragging = False

        if self.dragging and event.type == pygame.MOUSEMOTION:
            mouse_x = event.pos[0]
            relative_x = mouse_x - self.rect.x
            self.value = max(0.0, min(1.0, relative_x / self.rect.width))
            return True

        return False

    def draw(self, screen, font, screen_height):
        knob_radius = int(screen_height * 0.018)
        self.rect.height = int(screen_height * 0.012)

        label_text = f"{self.label}: {int(self.value * 100)}%"
        label_surface = font.render(label_text, True, (255, 255, 255))
        screen.blit(label_surface, (self.rect.x, self.rect.y - int(screen_height * 0.05)))

        pygame.draw.rect(screen, (100, 100, 100), self.rect, border_radius=5)
        knob_x = self.rect.x + self.value * self.rect.width
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
        if self._last_size == size:
            return

        if self.idle_image:
            self._scaled_idle = pygame.transform.smoothscale(self.idle_image, size)
            self.mask = pygame.mask.from_surface(self._scaled_idle)

        if self.hover_image:
            self._scaled_hover = pygame.transform.smoothscale(self.hover_image, size)

        self._last_size = size

    def is_hovering(self, mouse_pos):
        if not self.mask:
            return False

        try:
            return self.mask.get_at(mouse_pos) != 0
        except IndexError:
            return False

    def draw(self, screen):
        sprite = self._scaled_hover if self.hovered and self._scaled_hover else self._scaled_idle
        if sprite:
            screen.blit(sprite, (0, 0))


class AnimatedFullscreenStar(FullscreenLayerItem):
    def __init__(self, name, idle_frames, hover_frames):
        super().__init__(name)
        self.idle_frames = [frame for frame in idle_frames if frame]
        self.hover_frames = [frame for frame in hover_frames if frame]
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
            width, height = size
            self._scaled_idle_frames = [pygame.transform.smoothscale(frame, size) for frame in self.idle_frames]

            hover_width = int(width * self.hover_visual_scale)
            hover_height = int(height * self.hover_visual_scale)
            self._scaled_hover_frames = [pygame.transform.smoothscale(frame, (hover_width, hover_height)) for frame in self.hover_frames]

            center_x, center_y = base_hitbox.center
            self.hover_draw_offset = (
                center_x - int(center_x * self.hover_visual_scale),
                center_y - int(center_y * self.hover_visual_scale),
            )
            self._last_size = size

        self.idle_hitbox = base_hitbox.copy()
        self.active_hitbox = pygame.Rect(0, 0, int(base_hitbox.width * self.hitbox_growth_ratio), int(base_hitbox.height * self.hitbox_growth_ratio))
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
            frame = self._scaled_hover_frames[self.frame_index % len(self._scaled_hover_frames)]
            screen.blit(frame, self.hover_draw_offset)
        elif self._scaled_idle_frames:
            frame = self._scaled_idle_frames[self.frame_index % len(self._scaled_idle_frames)]
            screen.blit(frame, (0, 0))
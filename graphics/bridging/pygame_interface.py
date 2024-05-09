from __future__ import annotations

import inspect
from typing import Tuple, Any, Dict, List

import pygame
from pygame import BLEND_RGB_ADD, BLEND_RGB_MULT, USEREVENT, KEYUP, KEYDOWN, MOUSEBUTTONDOWN, MOUSEBUTTONUP, QUIT

from graphics.bridging.interface import DrawingSurface, Rectangle, GraphicsInterface, \
    InputInterface, FontDefinition, IOEvent

import logging
logger = logging.getLogger(__name__)


class PygameIOEvent(IOEvent):
    def __init__(self, event_type, payload=None, key=None):
        super().__init__(event_type, payload=payload, key=key)

    def get_char(self):
        return pygame.key.name(self.key)


class PygameInputInterface(InputInterface):

    @staticmethod
    def get_fonts_list() -> List[str]:
        return sorted(pygame.font.get_fonts())

    @staticmethod
    def get_mouse_button_clicked() -> str | None:
        button = pygame.mouse.get_pressed(num_buttons=3)
        if button[0]:
            return InputInterface.MOUSE_BUTTON_LEFT
        elif button[2]:
            return InputInterface.MOUSE_BUTTON_RIGHT
        else:
            return None

    @staticmethod
    def get_mouse_position() -> Tuple[int, int]:
        return pygame.mouse.get_pos()

    @staticmethod
    def is_shift_down() -> bool:
        return bool(pygame.key.get_mods() & pygame.KMOD_SHIFT)

    @staticmethod
    def post_event(json_msg: Dict) -> None:
        my_event = pygame.event.Event(USEREVENT, {'control': json_msg})
        pygame.event.post(my_event)

    @staticmethod
    def get_next_events() -> List[IOEvent]:
        io_events = []
        for event in pygame.event.get():
            if event.type == USEREVENT:
                io_events.append(PygameIOEvent(IOEvent.NETWORK_IO, payload=event.control))
            elif event.type == QUIT:
                io_events.append(PygameIOEvent(IOEvent.QUIT))
            elif event.type == KEYUP:
                io_events.append(PygameIOEvent(IOEvent.KEY_UP, key=event.key))
            elif event.type == KEYDOWN:
                io_events.append(PygameIOEvent(IOEvent.KEY_DOWN, key=event.key))
            elif event.type == MOUSEBUTTONDOWN:
                io_events.append(PygameIOEvent(IOEvent.MOUSE_BUTTON_DOWN))
            elif event.type == MOUSEBUTTONUP:
                io_events.append(PygameIOEvent(IOEvent.MOUSE_BUTTON_UP))
        return io_events


class PygameDrawingSurface(DrawingSurface):
    def __init__(self, surface):
        self.surface: pygame.Surface = surface

    def get_surface(self) -> Any:
        return self.surface

    def convert_alpha(self) -> None:
        self.surface.convert_alpha()

    def set_color_key(self, transparent_color_key: Tuple[int, int, int]):
        self.surface.set_colorkey(transparent_color_key)

    def scale(self, size: Tuple[int, int]) -> DrawingSurface:
        return PygameDrawingSurface(pygame.transform.scale(self.surface, size))

    def scale_by(self, size: Tuple[int, int]) -> DrawingSurface:
        return PygameDrawingSurface(pygame.transform.scale_by(self.surface, size))

    def blit(self, image: DrawingSurface, position: Tuple[int, int], blend_rgb_add=False, blend_rgb_mult=False) -> None:
        if blend_rgb_add:
            self.surface.blit(image.get_surface(), position, special_flags=BLEND_RGB_ADD)
        elif blend_rgb_mult:
            self.surface.blit(image.get_surface(), position, special_flags=BLEND_RGB_MULT)
        else:
            self.surface.blit(image.get_surface(), position)

    def fill(self, color: Tuple[int, int, int]) -> None:
        self.surface.fill(color)

    def rotate(self, degrees: float) -> DrawingSurface:
        return PygameDrawingSurface(pygame.transform.rotate(self.surface, degrees))

    def rotate_about(self, angle: float, origin: Tuple[int, int] = (42, 21)):
        image = self.get_surface()
        # offset from pivot to center
        image_rect = image.get_rect(topleft=(-origin[0], -origin[1]))
        offset_center_to_pivot = pygame.math.Vector2((0, 0)) - image_rect.center
        rotated_offset = offset_center_to_pivot.rotate(angle)
        rotated_image_center = (- rotated_offset.x, - rotated_offset.y)
        rotated_image = pygame.transform.rotate(image, angle)
        rotated_image_rect = rotated_image.get_rect(center=rotated_image_center)
        return \
            PygameDrawingSurface(rotated_image), \
            Rectangle(rotated_image_rect.x, rotated_image_rect.y, rotated_image_rect.width, rotated_image_rect.height)

    def get_height(self) -> int:
        return self.surface.get_height()

    def get_width(self) -> int:
        return self.surface.get_width()

    def set_alpha(self, value: int) -> None:
        self.surface.set_alpha(value)

    def copy(self) -> DrawingSurface:
        return PygameDrawingSurface(self.surface.copy())


_circle_cache = {}


def _circle_points(r):
    r = int(round(r))
    if r in _circle_cache:
        return _circle_cache[r]
    x, y, e = r, 0, 1 - r
    _circle_cache[r] = points = []
    while x >= y:
        points.append((x, y))
        y += 1
        if e < 0:
            e += 2 * y - 1
        else:
            x -= 1
            e += 2 * (y - x) - 1
    points += [(y, x) for x, y in points if x > y]
    points += [(-x, y) for x, y in points if x]
    points += [(x, -y) for x, y in points if y]
    points.sort()
    return points


class PygameGraphicsInterface(GraphicsInterface):

    def __init__(self):
        self.clock = pygame.time.Clock()
        self.font_cache = {}
        pygame.init()

    def get_inverted_mask(self, sprite: DrawingSurface) -> DrawingSurface:
        dark_overlay = pygame.mask.from_surface(sprite.get_surface())
        dark_overlay.invert()
        dark_overlay = dark_overlay.to_surface()
        return PygameDrawingSurface(dark_overlay)

    def get_mask(self, sprite: DrawingSurface) -> DrawingSurface:
        mask = pygame.mask.from_surface(sprite.get_surface()).to_surface()
        return PygameDrawingSurface(pygame.Surface(mask.get_size()))

    def draw_highlight_text(
            self,
            text: str,
            font_def: FontDefinition,
            fg_color: Tuple[int, int, int] = pygame.Color('dodgerblue'),
            bg_color: Tuple[int, int, int] = (255, 255, 255),
            border_size=2
    ) -> DrawingSurface:

        str_hash = f"{text}###{fg_color[0]},{fg_color[1]},{fg_color[2]}--{bg_color[0]},{bg_color[1]},{bg_color[2]}--"\
                   f"{font_def.get_face()}-{font_def.get_size()}-{font_def.is_bold()}-{font_def.is_italic()}"

        if str_hash not in self.font_cache:
            logger.info(f"Rendering highlight text! {inspect.stack()[1][3]}")

            font = pygame.font.SysFont(
                font_def.get_face(),
                font_def.get_size(),
                font_def.is_bold(),
                font_def.is_italic()
            )
            text_surface = font.render(text, True, fg_color).convert_alpha()
            w = text_surface.get_width() + 2 * border_size
            h = font.get_height()
            osurf = pygame.Surface((w, h + 2 * border_size)).convert_alpha()
            osurf.fill((0, 0, 0, 0))
            surf = osurf.copy()
            osurf.blit(font.render(text, True, bg_color).convert_alpha(), (0, 0))
            for dx, dy in _circle_points(border_size):
                surf.blit(osurf, (dx + border_size, dy + border_size))

            surf.blit(text_surface, (border_size, border_size))
            self.font_cache[str_hash] = PygameDrawingSurface(surf)
        return self.font_cache[str_hash]

    def tick(self, param) -> None:
        self.clock.tick(param)

    def set_display_caption(self, caption: str) -> None:
        pygame.display.set_caption(caption)

    def get_display_caption(self) -> str:
        return pygame.display.get_caption()[0]

    def create_screen(self, size: Tuple[int, int]) -> DrawingSurface:
        return PygameDrawingSurface(pygame.display.set_mode(size))

    def create_drawing_surface(self, size: Tuple[int, int]) -> DrawingSurface:
        return PygameDrawingSurface(pygame.Surface(size))

    def load_asset(self, file_path: str) -> DrawingSurface:
        return PygameDrawingSurface(pygame.image.load(file_path).convert_alpha())

    def fill_rectangle(
            self, surface: DrawingSurface, color: Tuple[int, int, int], rect: Rectangle
    ) -> None:
        logger.info(f"Filling rectangle: {inspect.stack()[1][3]}")
        pygame.draw.rect(surface.get_surface(), color, rect.get_tuple(), 0)

    def draw_rectangle(
            self,
            surface: DrawingSurface,
            color: Tuple[int, int, int],
            rect: Rectangle,
            border_width: int
    ) -> None:
        logger.info(f"Drawing rectangle: {inspect.stack()[1][3]}")
        pygame.draw.rect(surface.get_surface(), color, rect.get_tuple(), width=border_width)

    def draw_text(
            self,
            font_definition: FontDefinition,
            input_text: str,
            color: Tuple[int, int, int]
    ) -> DrawingSurface:
        logger.info(f"Drawing text: {inspect.stack()[1][3]}")
        font = pygame.font.SysFont(
            font_definition.get_face(),
            font_definition.get_size(),
            font_definition.is_bold(),
            font_definition.is_italic()
        )
        surface = PygameDrawingSurface(font.render(input_text, False, color))
        return surface

    def flip(self):
        pygame.display.flip()

    def quit(self):
        pygame.quit()

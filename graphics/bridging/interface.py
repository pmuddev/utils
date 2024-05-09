from __future__ import annotations
from typing import Tuple, Any, Dict, List


class Rectangle:
    def __init__(self, x: int, y: int, width: int, height: int):
        self._x = x
        self._y = y
        self._width = width
        self._height = height

    def get_width(self) -> int:
        return self._width

    def get_height(self) -> int:
        return self._height

    def get_x(self) -> int:
        return self._x

    def get_y(self) -> int:
        return self._y

    def get_tuple(self) -> Tuple[int, int, int, int]:
        return self._x, self._y, self._width, self._height

    def contains_point(self, mouse_x: int, mouse_y: int) -> bool:
        return self._x <= mouse_x <= self._x + self._width and self._y <= mouse_y <= self._y + self._height

    def __repr__(self):
        return f"Rectangle({self._x}, {self._y}, {self._width}, {self._height})"


class FontDefinition:
    def __init__(self, face: str, size: int, bold=False, italic=False):
        self._face = face
        self._size = size
        self._bold = bold
        self._italic = italic

    def get_size(self):
        return self._size

    def get_face(self):
        return self._face

    def is_bold(self):
        return self._bold

    def is_italic(self):
        return self._italic

    def decrease_size(self):
        self._size -= 1

    def increase_size(self):
        self._size += 1


class IOEvent:
    QUIT = 0
    MOUSE_BUTTON_DOWN = 10
    MOUSE_BUTTON_UP = 11
    KEY_DOWN = 20
    KEY_UP = 21
    NETWORK_IO = 99

    def __init__(self, event_type, payload=None, key=None):
        self.key = key
        self.payload = payload
        self.type = event_type

    def get_char(self):
        raise NotImplementedError("Attempting to call Abstract function.")


class InputInterface:
    MOUSE_BUTTON_LEFT = "left"
    MOUSE_BUTTON_RIGHT = "right"
    MOUSE_BUTTON_MIDDLE = "middle"

    @staticmethod
    def get_mouse_button_clicked() -> str:
        raise NotImplementedError()

    @staticmethod
    def get_mouse_position() -> Tuple[int, int]:
        raise NotImplementedError()

    @staticmethod
    def is_shift_down():
        raise NotImplementedError()

    @staticmethod
    def post_event(json_msg: Dict):
        raise NotImplementedError()

    @staticmethod
    def get_next_events() -> List[IOEvent]:
        raise NotImplementedError()

    @staticmethod
    def get_fonts_list() -> List[str]:
        raise NotImplementedError()


class DrawingSurface:

    def get_surface(self) -> Any:
        raise NotImplementedError()

    def scale(self, size: Tuple[int, int]) -> DrawingSurface:
        raise NotImplementedError()

    def scale_by(self, size: Tuple[int, int]) -> DrawingSurface:
        raise NotImplementedError()

    def rotate(self, degrees: int) -> DrawingSurface:
        raise NotImplementedError()

    def blit(self, img: DrawingSurface, position: Tuple[int, int], blend_rgb_add=False, blend_rgb_mult=False) -> None:
        raise NotImplementedError()

    def fill(self, color: Tuple[int, int, int]) -> None:
        raise NotImplementedError()

    def get_height(self) -> int:
        raise NotImplementedError()

    def get_width(self) -> int:
        raise NotImplementedError()

    def set_alpha(self, value: int) -> None:
        raise NotImplementedError()

    def copy(self) -> DrawingSurface:
        raise NotImplementedError()

    def set_color_key(self, transparent_color_key: Tuple[int, int, int]):
        raise NotImplementedError()

    def convert_alpha(self) -> None:
        raise NotImplementedError()


class GraphicsInterface:

    def draw_highlight_text(
            self,
            text: str,
            font_def: FontDefinition,
            fg_color: Tuple[int, int, int] = None,
            bg_color: Tuple[int, int, int] = None,
            border_size=2
    ) -> DrawingSurface:
        raise NotImplementedError()

    def create_screen(self, size: Tuple[int, int]) -> DrawingSurface:
        raise NotImplementedError()

    def create_drawing_surface(self, size: Tuple[int, int]) -> DrawingSurface:
        raise NotImplementedError()

    def load_asset(self, file_path: str) -> DrawingSurface:
        raise NotImplementedError()

    def fill_rectangle(
            self,
            surface: DrawingSurface,
            fill_color: Tuple[int, int, int],
            rect: Rectangle
    ) -> None:
        raise NotImplementedError()

    def draw_rectangle(
            self,
            surface: DrawingSurface,
            fill_color: Tuple[int, int, int],
            rect: Rectangle,
            border_width: int
    ) -> None:
        raise NotImplementedError()

    def tick(self, param) -> None:
        raise NotImplementedError()

    def set_display_caption(self, version_info: str) -> None:
        raise NotImplementedError()

    def get_display_caption(self) -> str:
        raise NotImplementedError()

    def draw_text(
            self,
            font_definition: FontDefinition,
            input_text: str,
            color: Tuple[int, int, int]
    ) -> DrawingSurface:
        raise NotImplementedError()

    def flip(self):
        raise NotImplementedError()

    def quit(self):
        raise NotImplementedError()

    def get_inverted_mask(self, sprite: DrawingSurface) -> DrawingSurface:
        raise NotImplementedError()

    def get_mask(self, sprite: DrawingSurface) -> DrawingSurface:
        raise NotImplementedError()

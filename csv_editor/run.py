from __future__ import annotations

import cProfile
import io
import json
import pstats
import sys
import time
import zlib
from base64 import b64decode
from pstats import SortKey
from typing import List, Optional, Union
import copy
import logging

logger = logging.getLogger(__name__)


from pygame.constants import *

import math
from graphics.bridging.interface import GraphicsInterface, DrawingSurface, Rectangle, InputInterface, FontDefinition, IOEvent
from graphics.bridging.pygame_interface import PygameInputInterface, PygameGraphicsInterface

PROFILER_ENABLED = False
PROFILER = cProfile.Profile()


VALID_CHARS = " `1234567890-=qwertyuiop[]\\asdfghjkl;'zxcvbnm,./"
SHIFT_CHARS = ' ~!@#$%^&*()_+QWERTYUIOP{}|ASDFGHJKL:"ZXCVBNM<>?'


class Spreadsheet:
    def __init__(self):
        self.data = {}
        self.cursor = [0, 0]
        self.mark = [0, 0]

    def move_cursor(self, row: int, col: int) -> None:
        self.cursor = [row, col]

    def get_cursor(self) -> Tuple[int, int]:
        return copy.copy(self.cursor)
            
    def set(self, row: int, col: int, val: str) -> None:
        if row not in self.data:
            self.data[row] = {}
        self.data[row][col] = val

    def get(self, row: int, col: int) -> Optional[str]:
        if row not in self.data or col not in self.data[row]:
            return None
        else:
            return self.data[row][col]


class App:

    TARGET_FRAME_RATE = 160
    W = 640
    H = 480
    SIZE = W, H

    def __init__(self):
        self.graphics_interface: GraphicsInterface = PygameGraphicsInterface()
        self.input_interface: InputInterface = PygameInputInterface()
        self.fps_log = []
        self.screen = self.graphics_interface.create_screen(self.SIZE)
        self.running = True
        self.max_row = 100
        self.max_col = 100
        self.focus_row = 0
        self.focus_col = 0

        self.dirty = True
        
        self.cursor_graphic = None
        self.column_width = 40
        self.row_height = 20
        self.background = None
        self.version_info = "csved"

        self.toggle_input_box = False
        self.input_box_contents = ""

        self.spreadsheet = Spreadsheet()
        
        self.graphics_interface.set_display_caption(self.version_info)

    def parse_events():
        pass
    
    def run(self) -> None:
        logger.debug("Connecting...")
        logger.debug("Done.")

        while self.running:
            self.parse_events()
            self.screen.fill((0, 0, 0))
            self.draw()
            self.graphics_interface.flip()

        self.graphics_interface.quit()

    def draw_grid(self, surface: DrawingSurface, rows, cols):
        cell = self.graphics_interface.create_drawing_surface([self.column_width, self.row_height])
        self.graphics_interface.draw_rectangle(cell, [200, 200, 200], Rectangle(0, 0, self.column_width, self.row_height), 2)
        for row in range(0, rows):
            for col in range(0, cols):
                surface.blit(cell, [col * self.column_width, row * self.row_height])

        #surface.blit(self.graphics_interface.draw_text(FontDefinition("arial", 16), "hello", [255, 255, 255]), [0, 0])

        
    def draw(self):
        if self.background is None:
            self.background = self.graphics_interface.create_drawing_surface([640, 480])
            self.draw_grid(self.background, 20, 40)
            
        self.screen.blit(self.background, [0, 0])

        if self.cursor_graphic is None:
            self.cursor_graphic = self.graphics_interface.create_drawing_surface([self.column_width, self.row_height])
            self.graphics_interface.draw_rectangle(self.cursor_graphic, [255,255,0], Rectangle(0, 0, self.column_width, self.row_height), 4)

        cursor_pos = self.spreadsheet.get_cursor()
        self.screen.blit(self.cursor_graphic, [cursor_pos[1] * self.column_width, cursor_pos[0] * self.row_height])       
        

    def parse_events(self) -> None:
        events = self.input_interface.get_next_events()
        for event in events:
            if event.type == IOEvent.QUIT:
                logger.debug("Received quit.")
                self.running = False
            elif event.type == IOEvent.MOUSE_BUTTON_DOWN:
                self.parse_mouse_button_down()
            elif event.type == IOEvent.MOUSE_BUTTON_UP:
                self.parse_mouse_button_up()
            elif event.type == IOEvent.KEY_DOWN:
                self.parse_keyboard_input_down(event)
            elif event.type == IOEvent.KEY_UP:
                self.parse_keyboard_input_up(event)

    def parse_mouse_button_down(self):
        pass

    def parse_mouse_button_up(self):
        pass
                
    def parse_keyboard_input_up(self, event: IOEvent):
        pass

    def parse_keyboard_input_down(self, event: IOEvent):
        self.dirty = True
        
        logger.info(f"Key down: {event.key}")
        if self.toggle_input_box:
            self.redirect_input_to_prompt(event)
        elif event.key == K_RETURN:
            logger.info("Starting I/O box")
            self.input_box_contents = ""
            self.toggle_input_box = True
            self.input_box_dirty = True

        elif event.key == K_DOWN:
            logger.info("moving down")
            current_row, current_col  = self.spreadsheet.get_cursor()
            self.spreadsheet.move_cursor(min(self.max_row, current_row+1), current_col)
        elif event.key == K_UP:
            current_row, current_col  = self.spreadsheet.get_cursor()
            self.spreadsheet.move_cursor(max(0, current_row-1), current_col)
        elif event.key == K_RIGHT:
            current_row, current_col  = self.spreadsheet.get_cursor()
            self.spreadsheet.move_cursor(current_row, min(self.max_col, current_col+1))
        elif event.key == K_LEFT:
            current_row, current_col  = self.spreadsheet.get_cursor()
            self.spreadsheet.move_cursor(current_row, max(0, current_col-1))

    def redirect_input_to_prompt(self, event: IOEvent):
        if event.key == K_RETURN:
            logger.info(f"Typed: {self.input_box_contents}")
            self.input_box_contents = ""
            self.toggle_input_box = False
        elif event.key == K_BACKSPACE:
            self.input_box_contents = self.input_box_contents[:-1]
        elif event.key == K_SPACE:
            self.input_box_contents += " "
        else:
            char = event.get_char()
            shift_down = self.input_interface.is_shift_down()
            if char in VALID_CHARS and not shift_down:
                self.input_box_contents += char
            elif char in VALID_CHARS and shift_down:
                self.input_box_contents += SHIFT_CHARS[VALID_CHARS.index(char)]
        self.input_box_dirty = True

        
if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG,
                        format='[%(asctime)s] [%(filename)s:%(lineno)s - %(funcName)s] - %(message)s')
    app = App()
    app.run()

    if PROFILER_ENABLED:
        PROFILER.disable()
        s = io.StringIO()
        ps = pstats.Stats(PROFILER, stream=s).sort_stats(SortKey.CUMULATIVE)
        ps.print_stats()
        print(s.getvalue())

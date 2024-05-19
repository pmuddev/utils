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
import re

logger = logging.getLogger(__name__)


from pygame.constants import *

import math
from graphics.bridging.interface import GraphicsInterface, DrawingSurface, Rectangle, InputInterface, FontDefinition, IOEvent
from graphics.bridging.pygame_interface import PygameInputInterface, PygameGraphicsInterface

SS_CELL_WIDTH_PARAM = "ss.cell_width"
SS_CELL_HEIGHT_PARAM = "ss.cell_height"
SS_BORDER_WIDTH_PARAM = "ss.cell_border_width"
SS_FONT_SIZE_PARAM = "ss.font_size"
SS_FONT_FACE_PARAM = "ss.courier_new"

SS_CELL_WIDTH_VALUE = 12
SS_CELL_HEIGHT_VALUE = 20
SS_CELL_BORDER_WIDTH = 1
SS_CELL_TEXT_PADDING_VALUE = 1
SS_FONT_SIZE_VALUE = 16
SS_FONT_FACE_VALUE = "courier new"
SS_MARK_COLOR = [200, 0, 0]
SS_CURSOR_HIGHLIGHT_COLOR = [200, 200, 0]
SS_CURSOR_BORDER_WIDTH = 1

PROFILER_ENABLED = False
PROFILER = cProfile.Profile()

VALID_CHARS = " `1234567890-=qwertyuiop[]\\asdfghjkl;'zxcvbnm,./"
SHIFT_CHARS = ' ~!@#$%^&*()_+QWERTYUIOP{}|ASDFGHJKL:"ZXCVBNM<>?'


class Cell:
    def __init__(self, row: int, col: int):
        self.row: int = row
        self.col: int = col

    def copy(self) -> Cell:
        return Cell(self.row, self.col)


class Spreadsheet:
    def __init__(self):
        self.data = {}
        self.cursor = Cell(0, 0)
        self.mark = Cell(0, 0)

    def move_cursor(self, cell: Cell) -> None:
        self.cursor = cell.copy()

    def get_cursor(self) -> Cell:
        return self.cursor.copy()

    def move_mark(self, cell: Cell) -> None:
        self.mark = cell.copy()

    def get_mark(self) -> Cell:
        return self.mark.copy()

    def get_bounding_box(self) -> Tuple[Cell, Cell]:
        bbox_min = Cell(
            min(self.cursor.row, self.mark.row),
            min(self.cursor.col, self.mark.col)
        )
        bbox_max = Cell(
            max(self.cursor.row, self.mark.row),
            max(self.cursor.col, self.mark.col)
        )
        return (bbox_min, bbox_max)

    def get_selected_cells(self, include_empty=False) -> List[Cell]:
        ret = []
        bbox_min, bbox_max = self.get_bounding_box()
        for row in range(bbox_min.row, bbox_max.row + 1):
            if include_empty or row in self.data:
                for col in range(bbox_min.col, bbox_max.col +1):
                    if include_empty or col in self.data[row]:
                        ret.append(Cell(row, col))
        return ret          

    def delete(self, cell: Cell) -> None:
        self.set(cell, None)
    
    def set(self, cell: Cell, val: str) -> None:
        if val is not None:
            if cell.row not in self.data:
                self.data[cell.row] = {}
            self.data[cell.row][cell.col] = val
        elif cell.row in self.data and cell.col in self.data[cell.row]:
            self.data[cell.row].pop(cell.col)        

    def get(self, cell: Cell) -> Optional[str]:
        if cell.row not in self.data or cell.col not in self.data[cell.row]:
            return None
        else:
            return self.data[cell.row][cell.col]

def iterate_function_v2(cell: Cell, spreadsheet: Spreadsheet):
    def colorize(cell_val):
        if cell_val == "0":
            return None
        else:
            return "bg(0,0,0);fg(0,0,0)??1"

    def get_content(cell_val: str) -> int:
        if cell_val is not None and "??" in cell_val:
            return int(cell_val.split("??")[1])
        elif cell_val is not None:
            return int(cell_val)
        else:
            return 0

    current_state = get_content(spreadsheet.get(Cell(cell.row, cell.col)))
    neighbours = [  
        get_content(spreadsheet.get(Cell(cell.row - 1, cell.col - 1))),
        get_content(spreadsheet.get(Cell(cell.row - 1, cell.col))),
        get_content(spreadsheet.get(Cell(cell.row - 1, cell.col + 1))),
        get_content(spreadsheet.get(Cell(cell.row, cell.col -1))),
        get_content(spreadsheet.get(Cell(cell.row, cell.col + 1))),
        get_content(spreadsheet.get(Cell(cell.row + 1, cell.col -1))),
        get_content(spreadsheet.get(Cell(cell.row + 1, cell.col))),
        get_content(spreadsheet.get(Cell(cell.row + 1, cell.col + 1))),
    ]

    alive_neighbours = sum(neighbours)
    if current_state == 1:
        if alive_neighbours < 2 or alive_neighbours > 3:
            return (cell, colorize("0"))
        else:
            return (cell, colorize("1"))
    else:
        if alive_neighbours == 3:
            return (cell, colorize("1"))
        else:
            return (cell, colorize("0"))


        
def iterate_function_v1(cell: Cell, spreadsheet: Spreadsheet):
    rule = "01101110"

    def colorize(cell_val):
        if cell_val == "0":
            return "bg(255,255,255);fg(255,255,255)??0"
        else:
            return "bg(0,0,0);fg(0,0,0)??1"

    def get_content(cell_val):
        if cell_val is not None and "??" in cell_val:
            return cell_val.split("??")[1]
        else:
            return cell_val
        
        
    if spreadsheet.get(cell) is None:
        # Check parents
        tl = get_content(spreadsheet.get(Cell(cell.row - 1, cell.col - 1)))
        tc = get_content(spreadsheet.get(Cell(cell.row - 1, cell.col)))
        tr = get_content(spreadsheet.get(Cell(cell.row - 1, cell.col + 1)))

        # Validate
        count_parents = 0
        for parent in [tl, tc, tr]:
            if parent in ["0", "1"]:
                count_parents +=1

        if count_parents < 3 and count_parents > 0:
            return (cell, colorize("0"))
        elif count_parents == 0:
            return (cell, None)
                
        # check value
        val_map = {
            "111": rule[0],
            "110": rule[1],
            "101": rule[2],
            "100": rule[3],
            "011": rule[4],
            "010": rule[5],
            "001": rule[6],
            "000": rule[7]
        }
        return (cell, colorize(val_map[tl+tc+tr]))
    else:
        return (cell, spreadsheet.get(cell))

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
        self.text_cache = {}
        self.cursor_graphic = None
        self.background = None
        self.version_info = "csved"
        self.mark_graphic = None
        
        self.toggle_input_box = False
        self.input_box_contents = ""

        self.spreadsheet = Spreadsheet()
        self.graphics_interface.set_display_caption(self.version_info)

    def run(self) -> None:
        logger.debug("Connecting...")
        logger.debug("Done.")

        while self.running:
            self.parse_events()
            self.screen.fill((0, 0, 0))
            self.draw()
            self.graphics_interface.flip()

        self.graphics_interface.quit()

    def draw_grid(self, surface: DrawingSurface, rows, cols) -> None:
        cell = self.graphics_interface.create_drawing_surface([SS_CELL_WIDTH_VALUE, SS_CELL_HEIGHT_VALUE])
        cell.fill([255, 255, 255])
        self.graphics_interface.draw_rectangle(
            cell,
            [127, 127, 127],
            Rectangle(0, 0, SS_CELL_WIDTH_VALUE, SS_CELL_HEIGHT_VALUE),
            SS_CELL_BORDER_WIDTH
        )
        for row in range(0, rows):
            for col in range(0, cols):
                surface.blit(cell, [col * SS_CELL_WIDTH_VALUE, row * SS_CELL_HEIGHT_VALUE])


        
    def draw(self) -> None:
        if self.background is None:
            self.background = self.graphics_interface.create_drawing_surface([640, 480])
            self.draw_grid(self.background, 25, 60)
            
        self.screen.blit(self.background, [0, 0])

        for row in self.spreadsheet.data:
            for col in self.spreadsheet.data[row]:
                text = self.spreadsheet.get(Cell(row, col))
                if text not in self.text_cache:

                    if "??" in text:
                        formatting, content_text = text.split("??")
                    else:
                        formatting = None
                        content_text = text
                        
                        
                    bg_color = None
                    fg_color = [0, 0, 0]
                    if formatting is not None:
                        bg_pattern = re.compile(r".*bg\((\d+),(\d+),(\d+)\).*")
                        bg_matcher = bg_pattern.match(formatting)
                        if bg_matcher:
                            bg_color = [
                                int(bg_matcher.group(1)),
                                int(bg_matcher.group(2)),
                                int(bg_matcher.group(3))
                            ]

                        fg_pattern = re.compile(r".*fg\((\d+),(\d+),(\d+)\).*")
                        fg_matcher = fg_pattern.match(formatting)
                        if fg_matcher:
                            fg_color = [
                                int(fg_matcher.group(1)),
                                int(fg_matcher.group(2)),
                                int(fg_matcher.group(3))
                            ]


                    rendered_text = self.graphics_interface.draw_text(
                        FontDefinition(
                            SS_FONT_FACE_VALUE,
                            SS_FONT_SIZE_VALUE
                        ),
                        content_text,
                        fg_color
                    )

                    if bg_color is not None:
                        text_surface = self.graphics_interface.create_drawing_surface(
                            [rendered_text.get_width(), rendered_text.get_height()]
                        )
                        text_surface.fill(bg_color)
                        text_surface.blit(rendered_text, [0,0])
                    
                        self.text_cache[text] = text_surface
                    else:
                        self.text_cache[text] = rendered_text
                
                self.screen.blit(
                    self.text_cache[text],
                    [
                        SS_CELL_TEXT_PADDING_VALUE + col * SS_CELL_WIDTH_VALUE,
                        SS_CELL_TEXT_PADDING_VALUE + row * SS_CELL_HEIGHT_VALUE
                    ]
                )
            
        bbox_min, bbox_max = self.spreadsheet.get_bounding_box()
        bbox_width = bbox_max.col - bbox_min.col + 1
        bbox_height = bbox_max.row - bbox_min.row + 1

        if self.dirty or self.mark_graphic is None:
            self.mark_graphic = self.graphics_interface.create_drawing_surface([SS_CELL_WIDTH_VALUE * bbox_width, SS_CELL_HEIGHT_VALUE * bbox_height])
            self.mark_graphic.convert_alpha()
            self.mark_graphic.set_alpha(100)
            self.mark_graphic.fill(SS_MARK_COLOR)
        self.screen.blit(
            self.mark_graphic,
            [bbox_min.col * SS_CELL_WIDTH_VALUE, bbox_min.row * SS_CELL_HEIGHT_VALUE]
        )
        
        
        if self.cursor_graphic is None:
            self.cursor_graphic = self.graphics_interface.create_drawing_surface([SS_CELL_WIDTH_VALUE, SS_CELL_HEIGHT_VALUE])
            self.cursor_graphic.set_color_key((0,0,0))
            self.cursor_graphic.fill((0,0,0)) 
            self.graphics_interface.draw_rectangle(
                self.cursor_graphic,
                SS_CURSOR_HIGHLIGHT_COLOR,
                Rectangle(0, 0, SS_CELL_WIDTH_VALUE, SS_CELL_HEIGHT_VALUE),
                SS_CURSOR_BORDER_WIDTH
            )

        cursor_pos: Cell = self.spreadsheet.get_cursor()
        self.screen.blit(
            self.cursor_graphic,
            [
                cursor_pos.col * SS_CELL_WIDTH_VALUE,
                cursor_pos.row * SS_CELL_HEIGHT_VALUE
            ]
        )       
        

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
        current_pos: Cell  = self.spreadsheet.get_cursor()
        current_mark: Cell = self.spreadsheet.get_mark()
        
        logger.info(f"Key down: {event.key}")
        if self.toggle_input_box:
            self.redirect_input_to_prompt(event)
        elif event.key == K_RETURN:
            logger.info("Starting I/O box")
            self.input_box_contents = ""
            self.toggle_input_box = True
            self.input_box_dirty = True

        elif event.key == K_DOWN:
            target = Cell(
                min(self.max_row, current_pos.row + 1),
                current_pos.col
            )
            self.spreadsheet.move_cursor(target)
            if not self.input_interface.is_shift_down():
                self.spreadsheet.move_mark(target)

        elif event.key == K_UP:
            target = Cell(
                max(0, current_pos.row-1),
                current_pos.col
            )
            self.spreadsheet.move_cursor(target)
            if not self.input_interface.is_shift_down():
                self.spreadsheet.move_mark(target)

        elif event.key == K_RIGHT:
            target = Cell(
                current_pos.row,
                min(self.max_col, current_pos.col+1)
            )
            self.spreadsheet.move_cursor(target)
            if not self.input_interface.is_shift_down():
                self.spreadsheet.move_mark(target)

        elif event.key == K_LEFT:
            target = Cell(
                current_pos.row,
                max(0, current_pos.col-1)
            )
            self.spreadsheet.move_cursor(target)
            if not self.input_interface.is_shift_down():
                self.spreadsheet.move_mark(target)
        elif event.key == K_DELETE:
            for cell in self.spreadsheet.get_selected_cells():
                self.spreadsheet.delete(cell)
        elif event.key == K_SPACE:
            result = []
            for cell in self.spreadsheet.get_selected_cells(include_empty=True):
                result.append(iterate_function_v2(cell, self.spreadsheet))
            for cell, val in result:
                self.spreadsheet.set(cell, val)

    def redirect_input_to_prompt(self, event: IOEvent):
        if event.key == K_RETURN:
            current_pos = self.spreadsheet.get_cursor()
            self.spreadsheet.set(
                current_pos,
                self.input_box_contents
            )
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

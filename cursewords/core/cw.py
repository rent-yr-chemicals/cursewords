import curses
from sys import stdout

from cursewords import Directional, Coord
from cursewords.core.actions import Actions
from cursewords.core.library import Library
from cursewords.core.aware import ColorPaletteAware
from cursewords.container.puzzle import Puzzle
from cursewords.gui.ui import UI
from cursewords.container.square import Square
from cursewords.container.word import Word
from cursewords.gui.colors import ColorPalette, default_theme

import time

class CurseWords(Actions):
    
    def __init__(self,win=None,mode='normal'):

        self.inited = False

        self.ui = None
        self.library = None
        self.puz = None
        self.win = win

        self._init_colors()

        self.fillable = 0
        self.currently_filled = 0

    def _init_colors(self):

        curses.use_default_colors()
        self.colors = ColorPalette(default_theme)
        ColorPaletteAware.color_func_set(self.colors.color)

    def initialize(self,path=None):

        self.ui = UI(win=self.win)
        self.library = Library()

        if path:
            self.puz = Puzzle(path=path)

        self.inited = True

    def current_square(self):
        return self.puz.squares[self.ui.solver.cursor.y][self.ui.solver.cursor.x]

    def current_word(self):
        return self.current_square().words[self.ui.solver.direction]
        
    def loop(self):

        while True:

            self.win.touchwin()
            self.ui.redraw()
            self.win.refresh()
            self.ui.handle_input()

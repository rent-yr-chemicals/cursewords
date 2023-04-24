import curses

from string import ascii_letters, digits
from functools import partialmethod
from cursewords import Coord, Directional
from cursewords.core.aware import CWAware, ColorPaletteAware
from cursewords.etc.special_chars import BLOCK

ALLOWED_CHARACTERS = ascii_letters + digits + '@#$%&+?'

class Square(CWAware,ColorPaletteAware):

    inner_size = Coord(1,3)
    border_size = Coord(1,1)

    grid = None

    SQ_BLNK = 0b00
    SQ_NORM = 0b01
    SQ_BLCK = 0b10
    SQ_SLCT = 0b11

    @staticmethod
    def get_dimens():
        return Square.inner_size, Square.border_size

    @staticmethod
    def link_grid(grid):
        Square.grid = grid

    def __init__(self, y, x, state, solution):

        self.coords = Coord(y,x)
        self.solution = solution
        self._state = None if state == '-' else state

        self.is_block = True if solution == '.' else False
        self.is_shaded = False
        self.is_given = False
        self.is_marked_bad = False
        self.prev_marked_bad = False

        self.rebus_solution = None
        self.rebus_state = None

        self.n = None
        self.words = Directional(across=None,down=None)
        self.neighbors = dict()

        self.is_locked = self.is_given

        self._old_state = self.state

    def link_word(self,word):
        old_words = self.words
        if word.direction.across:
            self.words = Directional(across=word,down=old_words.down)
        else:
            self.words = Directional(across=old_words.across,down=word)

    def link_neighbor(self, direction, neighbor, looped):
        self.neighbors[direction] = (neighbor, looped)

    def edit(self,content=None,op=None):

        if self.is_block:
            raise ValueError
        if self.is_locked:
            return

        if op == 'fill':
            if not content or not all(char in ALLOWED_CHARACTERS for char in content):
                raise ValueError
            content = content.upper()

        self.state = content
        self._update()

    fill = partialmethod(edit, op='fill')
    clear = partialmethod(edit, op='clear', content=None)

    def _update(self):

        if self.state != self._old_state:
            self.grid.need_redraw = True
            if self.is_marked_bad:
                self.is_marked_bad = False
                self.prev_marked_bad = True

        if self.state and not self._old_state:
            self.cw.puz.filled += 1
        elif self._old_state and not self.state:
            self.cw.puz.filled -= 1

        self._old_state = self.state

    def _set_state(self,value):
        if value:
            self._state = value[0]
            if len(value) > 1:
                self.rebus_state = value
        else:
            self._state = self.rebus_state = None

    def _get_state(self):
        if self.rebus_state:
            return self.rebus_state
        else:
            return self._state

    state = property(_get_state, _set_state)

    def check(self,silent=False):

        if self.is_block or not self.state:
            return True
        
        check_ok = self.state[0] == self.solution

        if not silent:
            self.is_locked = check_ok
            self.is_given = check_ok
            self.is_marked_bad = not check_ok
            self.grid.need_redraw = True

        return check_ok

    # Helper functions for grid drawing
    # XXX TO DO: should probably move these to grid class

    def get_n(self):

        if self.n:
            return str(self.n)
        else:
            return ''

    def get_fill(self):

        if self.is_block:
            return BLOCK*self.inner_size.x
        elif self.state is not None:
            return self.state
        else:
            return ''

    def get_attr(self):

        if self.is_block:
            return 0

        keys = ['square']

        if self in self.cw.current_word():
            keys.append('highlighted')
            if self == self.cw.current_square():
                keys.append('current')

        if self.is_shaded:
            keys.append('shaded')

        if self.is_marked_bad:
            keys.append('bad')

        elif self.is_locked:
            keys.append('locked')

        if self.cw.current_word().refs is not None:
            if any((word.n, word.direction) in self.cw.current_word().refs for word in self.words):
                keys.append('shaded')

        return self.cw.colors.color(*keys)

    def get_ch_key(self, cursor=None):

        if cursor is None:
            cursor = self.cw.ui.solver.cursor

        if self.is_block:
            return 'b'
        elif cursor in self:
            return 's'
        else:
            return 'p'

    def get_ch_key2(self, cursor=None):

        if self.is_block:
            return self.SQ_BLCK
        elif cursor in self:
            return self.SQ_SLCT
        else:
            return self.SQ_NORM


    def __contains__(self,item):

        from cursewords.container.word import Word

        if isinstance(item, Coord):
            if item == self.coords:
                return True
            else:
                return False
        elif isinstance(item, Word):
            if item in self.words:
                return True
            else:
                return False
        else:
            return False
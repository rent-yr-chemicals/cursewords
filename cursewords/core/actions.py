from cursewords import Coord, Directional
from cursewords.core.aware import CWAware

from time import time

class Actions(CWAware):

    # Summary:
    # - "move" actions:
    #     - move_cursor_to (absolute coordinates)
    #     - move_relative (relative to current square)
    #         - calls move_cursor_to
    #     - next_word
    #         - calls move_cursor_to
    #         - may call toggle_direction
    #     - prev_word
    #         - calls move_cursor_to
    #         - may call toggle_direction
    #     - move_to_next_valid
    #         - calls move_cursor_to
    #         - may call toggle_direction
    #     - move_to_next_empty
    #         - calls move_to_next_valid
    # - "edit" actions
    #     - fill_square
    #     - clear_square
    # - "check" actions
    # - toggle_direction

    def notify(self, obj, bad=False, lifetime=5):

        self.cw.ui.status_bar.notify(str(obj), color=['bad'] if bad else [], lifetime=lifetime)

    def this_file(self):
        return self.ui.browser.interior.this_file()

    def open_file(self, key):

        file = self.cw.library.open_file(key)

        if file:
            self.cw.puz = file
            self.ui.browser.close()
            self.ui.solver.open(file)

    def close_file(self, prompt_save=False):

        self.save(prompt=prompt_save)

        self.cw.puz = None
        self.ui.solver.close()
        self.ui.browser.open()

    def save(self, prompt=True):

        if prompt:
            self.cw.ui.console.open(text='cw.puz.save("{}")'.format(self.cw.puz.path), position=len(self.cw.puz.path)+17)
        else:
            self.cw.puz.save(self.cw.puz.path)

    def toggle_direction(self):

        old = self.cw.ui.solver.direction
        self.cw.ui.solver.direction = Directional(across=not old.across,down=not old.down)

    def move_relative(self, dy, dx):

        target = self.cw.ui.solver.cursor + Coord(dy, dx)

        return self.move_cursor_to(*target)

    def move_cursor_to(self, y, x, toggle_direction=False):

        if self.puz.is_valid_coord(y,x):
            if not self.cw.puz.squares[y][x].is_block:
                self.cw.ui.solver.cursor = Coord(y, x)
                if toggle_direction:
                    self.toggle_direction()
                return True
        return False

    def next_word(self):

        do_toggle = False

        current = self.cw.current_word()
        new = current.next

        if current.direction != new.direction:
            do_toggle = True

        return self.move_cursor_to(*new.start,toggle_direction=do_toggle)

    def prev_word(self):

        do_toggle = False

        current = self.cw.current_word()
        new = current.prev

        if current.direction != new.direction:
            do_toggle = True

        return self.move_cursor_to(*new.start,toggle_direction=do_toggle)

    def fill_square(self,content,move=True):

        square = self.cw.current_square()

        square.fill(content)

        if move:

            if square == self.cw.current_word().squares[-1]:
                self.next_word()
            else:
                dy, dx = map(int,self.cw.ui.solver.direction)
                self.move_to_next_valid(dy, dx)

    def clear_square(self,move=True):

        square = self.cw.current_square()
        square.clear()
        if move:
            dy, dx = map(int,self.cw.ui.solver.direction)
            self.move_to_next_valid(-dy, -dx)

    def move_to_next_valid(self, dy, dx):

        new, do_toggle = self.cw.current_square().neighbors[(dy, dx)]

        return self.move_cursor_to(*new.coords,toggle_direction=do_toggle)

    def move_to_next_empty(self,dy, dx):

        start = self.cw.current_square()

        while True:

            self.move_to_next_valid(dy, dx)
            current = self.cw.current_square()
            if not current.get_fill():
                return True
            if current == start:
                return False

    def is_valid_coord(self,y,x):

        if y < 0 or x < 0:
            return False
        elif y >= self.cw.puz.height or x >= self.cw.puz.width:
            return False
        else:
            return True

    def check_square(self):

        self.cw.current_square().check()

    def check_word(self):

        for square in self.cw.current_word():
            square.check()

    def check_grid(self):

        for row in self.cw.puz.squares:
            for square in row:
                square.check()

    def check_silent(self):

        #self.notify('checking...'+str(time()))

        for row in self.cw.puz.squares:
            for square in row:
                if not square.check(silent=True):
                    return False
        return True

    def exit(self):
        raise SystemExit(0)
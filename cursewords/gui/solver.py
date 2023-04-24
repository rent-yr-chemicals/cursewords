from sys import stdout
from functools import partial
from collections import defaultdict
import datetime

from cursewords import Coord, Directional
from cursewords.gui import dimens_from_boundaries
from cursewords.gui.components import ComponentContainer
from cursewords.gui.grid import Grid
from cursewords.gui.clues import CluePanel
from cursewords.gui.info import InfoPanel

class Solver(ComponentContainer):

    def __init__(self, hei, wid, y, x, win=None, src=None):

        ComponentContainer.__init__(self, hei, wid, y, x, win)

        if src is not None:
            self.visible = True
            self.focused = True

        self.src = src

        self.grid = Grid(1, 1, 0, 0, win=self.win)
        self.clues = CluePanel(1, 1,0, 0, win=self.win)
        self.info = InfoPanel(1, 1, 0, 0, win=self.win)

        self.add_component(self.grid)
        self.add_component(self.clues)
        self.add_component(self.info)

        self.paused = True
        self._old_paused = self.paused
        self.finished = False

        self.cursor = None
        self.direction = None

        self.key_bindings = defaultdict(lambda: self.start)
        self.key_bindings[4] = partial(self.cw.close_file)

    # def init_keys(self):

    #     self.bind_key(4, self.cw.close_file)

    def open(self,src):

        self.visible = True
        self.finished = False
        self.src = src

        self.pause()

        self.cursor = self.src.words.across[0].start
        self.direction = Directional(across=True,down=False)

        for component in self.components:
            component.open(self.src)

        if src.title:
            print('\33]0;'+src.title+' | CurseWords™\a', end='')
            stdout.flush()

        self.resize(self.hei, self.wid, self.y, self.x)

    def close(self):

        self.cw.library.update_status(self.src)
        self.cw.library.touch()
        self.visible = False
        self.focused = False
        self.finished = False
        self.src = None

        for component in self.components:
            component.close()

        print('\33]0;CurseWords™\a', end='')
        stdout.flush()

    def show(self):
        self.paused = False
        self.focused = False
        self.grid.focused = True

    def start(self):
        self.src.timer.resume()
        if self.cw.library[self.src]['start_date'] is None:
            self.cw.library[self.src]['start_date'] = datetime.datetime.now().isoformat(sep=' ')[:19]
        self.show()

    def pause(self):
        self.src.timer.pause()
        self.paused = True
        if self.cw.ui.get_focus():
            self.cw.ui.get_focus().focused = False
        self.focused = True

    def finish_puzzle(self):

        self.src.timer.lock()
        self.cw.check_grid()
        self.src.complete = True
        self.need_check = False

        self.cw.library.update_status(self.src)
        if self.cw.library[self.src]['completion_date'] is None:
            self.cw.library[self.src]['completion_date'] = datetime.datetime.now().isoformat(sep=' ')[:19]
        
        if self.paused:
            self.show()

        self.finished = True

    def predraw(self):

        if self.src is not None:

            if self.src.complete or (self.src.filled == self.src.fillable and self.cw.check_silent()):
                if not self.finished:
                    self.finish_puzzle()

        if self._old_paused != self.paused:
            self._old_paused = self.paused
            self.need_redraw = True

        ComponentContainer.predraw(self)

    def draw(self):
        if self.src is None:
            return
        self._draw_status()
        ComponentContainer.draw(self)

    def _draw_status(self):
        time_str = self.src.timer.fmt_time()
        time_str = '{:>{}}'.format(time_str, self.clues.wid)
        self.win.addstr(0, self.grid.wid + self.margin.x, time_str)
        status = 'Progress: {}% ({}/{})'.format((100*self.src.filled)//self.src.fillable, self.src.filled, self.src.fillable)
        if self.cw.current_square().rebus_state is not None:
            status += '   |   Rebus content: "{}"'.format(self.cw.current_square().rebus_state)
        self.win.addstr(0, self.grid.wid + self.margin.x, status)

    def resize(self, hei, wid, y, x):

        ComponentContainer.resize(self, hei, wid, y, x)

        self.grid.fit_to_source()

        self.clues.resize(*dimens_from_boundaries(
            y_min = 2,
            x_min = self.grid.wid + self.margin.x,
            y_max = self.hei,
            x_max = self.wid
        ))

        self.info.resize(*dimens_from_boundaries(
            y_min = self.grid.hei + self.margin.y,
            x_min = 0,
            y_max = self.hei,
            x_max = self.grid.wid
        ))
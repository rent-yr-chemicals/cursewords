import curses

from cursewords import Directional, Coord
from cursewords.core.aware import CWAware
from cursewords.gui import dimens_from_boundaries
from cursewords.gui.components import ComponentContainer
from cursewords.gui.solver import Solver
from cursewords.gui.console import Console
from cursewords.gui.browser import Browser
from cursewords.gui.status import StatusBar


class UI(ComponentContainer):

    margin = Coord(1,3)

    def __init__(self,win=None):

        self.inited = False

        hei, wid = win.getmaxyx()

        ComponentContainer.__init__(self, hei, wid, 0, 0, win=win)

        self.browser = None
        self.solver = None
        self.console = None

        self.visible = True
        self.need_redraw = True

        self.block_input = False

    def initialize(self):

        self.browser = Browser(1, 1, 0, 0, win=self.win)
        self.solver = Solver(1, 1, 0, 0, win=self.win)
        self.console = Console(1, 1, 0, 0, win=self.win)
        self.status_bar = StatusBar(1, 1, 0, 0, win=self.win)

        self.components.append(self.browser)
        self.components.append(self.solver)
        self.components.append(self.console)
        self.components.append(self.status_bar)

        for component in self.components:
            component.init_keys()

        self.resize()

        if self.cw.puz is not None:
            self.solver.open(self.cw.puz)
        else:
            self.browser.open()

        self.win.erase()

        self.inited = True

    def resize(self):

        self.hei, self.wid = self.win.getmaxyx()

        self.console.resize(*dimens_from_boundaries(
            y_min=self.hei-1,
            x_min=self.margin.x,
            y_max=self.hei,
            x_max=self.wid - self.margin.x
        ))

        self.status_bar.resize(*dimens_from_boundaries(
            y_min=self.hei-1,
            x_min=self.margin.x,
            y_max=self.hei,
            x_max=self.wid - self.margin.x
        ))

        self.solver.resize(*dimens_from_boundaries(
            y_min=self.margin.y,
            x_min=self.margin.x,
            y_max=self.hei - 5,
            x_max=self.wid - self.margin.x
        ))

        self.browser.resize(*dimens_from_boundaries(
            y_min=self.margin.y,
            x_min=self.margin.x,
            y_max=self.console.y - self.margin.y,
            x_max=self.wid - self.margin.x
        ))

        self.win.erase()
        self.need_redraw = True

    def redraw(self):

        self.predraw()
        self.draw()

    def handle_input(self):

        key = self.win.getch()

        if key == -1:
            return

        if not self.block_input:
            if key == curses.KEY_MOUSE:
                self.handle_mouse()
            elif key == curses.KEY_RESIZE:
                self.resize()
            else:
                focus = self.get_focus()
                if focus:
                    focus.key_bindings[key]()
        curses.flushinp()
        return

    def handle_mouse(self):

        _, win_x, win_y, _, bstate = curses.getmouse()
        left_click = bool(bstate & curses.BUTTON1_PRESSED)
        scroll_down = bool(bstate & curses.BUTTON2_PRESSED) or bool(bstate & 2**21)
        right_click = bool(bstate & curses.BUTTON3_PRESSED)
        scroll_up = bool(bstate & curses.BUTTON4_PRESSED)

        scroll = int(scroll_down) - int(scroll_up)

        if self.browser.visible and scroll:
            self.browser.interior.move(d=scroll)
            self.browser.interior.old_first_line += 3 * scroll

    # def handle_mouse(self):

    #     _, win_x, win_y, _, bstate = curses.getmouse()

    #     if not (bstate & curses.BUTTON1_PRESSED):
    #         return

    #     if (win_y,win_x) in self.grid:
    #         win_y -= self.grid.y
    #         win_x -= self.grid.x
    #         sq = self.grid._winyx_to_sq_yx(win_y, win_x)
    #         rel = self.grid._winyx_to_rel_yx(win_y, win_x)
    #         if None in sq:
    #             return
    #         elif 0 in rel:
    #             return
    #         else:
    #             if sq in self.cw.current_square():
    #                 self.cw.toggle_direction()
    #             else:
    #                 self.cw.move_cursor_to(*sq)



    # def draw_time(self,start,current):

    #     hours, minutes = divmod(current - start, 3600)
    #     minutes, seconds = divmod(minutes, 60)
    #     timer_str = '{:>2}:{:0>2}:{:0>2}'.format(int(hours), int(minutes), int(seconds))
    #     self.win.addstr(1, self.wid - 9 - self.margin.x, timer_str)

    # def resize(self):

    #     self.grid.resize(self.grid.const_hei, self.grid.const_wid, self.margin.y, self.margin.x)
    #     self.clues.resize(*self._dimens_from_boundaries(
    #         y_min=self.margin.y + 2,
    #         x_min=self.grid.x + self.grid.wid + self.margin.x,
    #         y_max=self.console.y - self.margin.y,
    #         x_max=self.wid - self.margin.x
    #     ))
    #     self.info.resize(*self._dimens_from_boundaries(
    #         y_min=2*self.margin.y + self.grid.hei,
    #         x_min=self.margin.x,
    #         y_max=self.console.y - self.margin.y,
    #         x_max=self.margin.x + self.grid.wid
    #     ))

    # def initialize(self, src=None):

    #     for i, _ in enumerate(self.grid.make_cache()):
    #         self.win.erase()
    #         n_dots = (i // 16) % 4
    #         self.win.addstr(0,0,'Loading' + '.'*n_dots, 0)
    #         self.win.refresh()

    #     self.cursor = self.cw.words.across[0].data.start
    #     self.grid.focus()

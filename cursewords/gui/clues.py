#coding=utf-8
import curses

from textwrap import wrap
from cursewords import Coord, Directional
from cursewords.gui.components import UIComponent, ComponentContainer

class CluePanel(ComponentContainer):

    def __init__(self,hei,wid,y,x,win=None):

        ComponentContainer.__init__(self,hei,wid,y,x,win=win)

        self.current_square = None
        self.current_column = None

        self.src = None
        self.is_initialized = False

        across_win = ClueColumn(1, 1, self.y, self.x, win=self.win, title='ACROSS', direction=Directional(across=True,down=False))
        down_win = ClueColumn(1, 1, self.y, self.x, win=self.win, title='DOWN', direction=Directional(across=False,down=True))

        self.columns = Directional(across=across_win, down=down_win)
        self.add_component(self.columns.across)
        self.add_component(self.columns.down)

    def open(self, src):

        self.src = src
        self.visible = True
        self.win.bkgd(' ', self.color('grid_lines'))

        self.columns.across.words = self.src.words.across
        self.columns.down.words = self.src.words.down
        self.columns.across.visible = True
        self.columns.down.visible = True


        self.is_initialized = True

    def close(self):

        self.src = None
        self.visible = False
        self.win.bkgd(' ',0)

        self.columns.across.words = None
        self.columns.down.words = None
        self.columns.across.visible = False
        self.columns.down.visible = False

        self.is_initialized = False

    def resize(self,*args):

        ComponentContainer.resize(self,*args)

        hei = self.hei - 2*self.margin.y
        inner_hspace = self.wid - 3*self.margin.x
        across_wid = inner_hspace//2
        down_wid = across_wid + inner_hspace % 2
        down_x = across_wid + 2*self.margin.x

        self.columns.down.resize(hei, down_wid, self.margin.y, down_x)
        self.columns.across.resize(hei, across_wid, self.margin.y, self.margin.x)

    def predraw(self):

        if self.is_initialized:
            if self.cw.current_square() != self.current_square:
                self.need_redraw = True
                self.current_square = self.cw.current_square()
            if self.current_column != self.cw.ui.solver.direction:
                self.need_redraw = True
                self.current_column = self.cw.ui.solver.direction

        ComponentContainer.predraw(self)

    def draw(self):

        if self.need_redraw:

            if self.cw.ui.solver.paused:
                self.win.bkgd(' ', self.color('grid_lines','paused'))
            else:
                self.win.bkgd(' ', self.color('grid_lines'))

            self.win.erase()
            self.draw_borders()
            ComponentContainer.draw(self)

    def draw_borders(self):

        self.win.hline(0,2,curses.ACS_HLINE,self.wid-4)
        self.win.hline(self.hei-1,2,curses.ACS_HLINE,self.wid-4)
        self.win.vline(1,1,curses.ACS_VLINE,self.hei-2)
        self.win.vline(1,self.wid-2,curses.ACS_VLINE,self.hei-2)

        self.win.addch(0,1,curses.ACS_ULCORNER)
        self.win.addch(0,self.wid-2,curses.ACS_URCORNER)
        self.win.addch(self.hei-1,1,curses.ACS_LLCORNER)
        self.win.addch(self.hei-1,self.wid-2,curses.ACS_LRCORNER)

        self.win.addch(0,self.columns.down.x-2,curses.ACS_TTEE)
        self.win.addch(self.hei-1,self.columns.down.x-2,curses.ACS_BTEE)
        self.win.vline(1,self.columns.down.x-2,curses.ACS_VLINE,self.hei-2)

class ClueColumn(UIComponent):

    def __init__(self, hei, wid, y, x, win=None, title=None, words=None, direction=None):

        UIComponent.__init__(self, hei, wid, y, x, win=win)

        self.title = title
        self.words = words
        self.direction = direction

        self.lines = []
        self.lines_hidden = []

    def compute_lines(self):

        label_width = len(str(self.words[-1].n) + '. ') # assuming words are properly sorted
        indent_padding = ' '*label_width
        text_space = self.wid - label_width
        if text_space < 0:
            return

        self.lines = []
        self.lines_hidden = []

        for word in self.words:

            label = '{:<{}}'.format(str(word.n)+'.', label_width)
            wrapped = ['{:<{}}'.format(line,text_space) for line in wrap(word.clue, text_space)]
            lines = [(label if i == 0 else indent_padding) + line for i, line in enumerate(wrapped)]
            self.lines.append((word,len(lines),lines))

            wrapped = ['{:<{}}'.format(line,text_space) for line in wrap('░'*len(word.clue), text_space)]
            lines = [(label if i == 0 else indent_padding) + line for i, line in enumerate(wrapped)]
            self.lines_hidden.append((word,len(lines),lines))

    def compute_offset(self):

        if not self.lines:
            return 0

        v_space = self.hei - 2

        end_clue = 0
        for word, n_lines, _ in self.lines:
            end_clue += n_lines
            if word in self.cw.current_square().words:
                end_clue -= 1
                break

        if end_clue < v_space:
            return 0
        else:
            return end_clue - v_space + 1


    def resize(self,*args):
        UIComponent.resize(self,*args)
        if self.words:
            self.compute_lines()

    def draw(self):

        if not self.words:
            return

        if not self.need_redraw:
            return

        if not self.lines:
            self.compute_lines()
            if not self.lines:
                return

        offset = self.compute_offset()

        if self.cw.ui.solver.paused:
            base_keys = ['clue', 'paused']
            self.win.bkgd(' ', self.color(*base_keys))
            lines = self.lines_hidden
        else:
            base_keys = ['clue']
            self.win.bkgd(' ', self.color('normal'))
            if self.direction == self.cw.ui.solver.direction:
                base_keys.append('active_column')
            lines = self.lines

        if self.title:
            self.win.addstr(0,0,self.title,self.color(*base_keys,'title'))

        y = 2
        current = 0

        for word, _, clue_lines in lines:
            keys = []
            if self.direction == self.cw.ui.solver.direction:
                keys.append('active_column')
            if word in self.cw.current_square().words:
                keys.append('highlighted')
            if self.cw.current_word().refs is not None:
                if (word.n, word.direction) in self.cw.current_word().refs:
                    keys.append('shaded')
            for line in clue_lines:
                if current < offset:
                    pass
                else:
                    try:
                        self.win.addstr(y,0,line,self.color(*base_keys,*keys))
                        y += 1
                    except curses.error:
                        return
                current += 1

        self.need_redraw = False
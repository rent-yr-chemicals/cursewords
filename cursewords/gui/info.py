#coding=utf-8
import curses
from textwrap import wrap
from cursewords.gui.components import UIComponent

class InfoPanel(UIComponent):

    def __init__(self, *args, **kwargs):

        UIComponent.__init__(self, *args, **kwargs)
        self.old_word = None
        self.src = None

    def open(self, src):

        self.src = src

        self.visible = True
        self.old_word = self.cw.current_word()

    def close(self):

        self.src = None
        self.visible = False

    def predraw(self):

        if self.src is not None:
            if self.cw.current_word != self.old_word:
                self.old_word = self.cw.current_word()
                self.need_redraw = True

        UIComponent.predraw(self)

    def draw(self):

        if self.src is None:
            return

        if not self.need_redraw:
            return

        base_keys = ['info']
        if self.cw.ui.solver.paused:
            base_keys.append('paused')

        self.draw_box(0, 0, 4, self.wid - 1, self.color(*base_keys, 'border'))

        this_word = self.cw.current_word()

        clue_space = self.wid - 4
        text = '░'*len(this_word.clue) if self.cw.ui.solver.paused else this_word.clue
        n = this_word.n
        d = this_word.direction

        label = '{}-{}: '.format(n, 'ACROSS' if d.across else 'DOWN')

        clue_lines = [' {:<{}} '.format(line, clue_space) for line in wrap(label+text, clue_space)]
        for y in range(1,4):
            try:
                self.win.addstr(y, 1, clue_lines[y-1], self.color(*base_keys, 'clue'))
            except IndexError:
                self.win.addstr(y, 1, ' '*(clue_space+2), self.color(*base_keys, 'clue'))

        self.win.chgat(1, 2, len(label), self.color(*base_keys, 'clue') | curses.A_BOLD)

        title_lines = wrap(self.cw.puz.title,self.wid)
        author = self.cw.puz.author.strip()
        copyright = self.cw.puz.copyright.strip()
        notes = self.cw.puz.notes.strip()

        y = 6

        for line in title_lines:
            try:
                self.win.addstr(y, 0, line, self.color(*base_keys) | curses.A_BOLD)
                y += 1
            except curses.error:
                break

        try:
            self.win.addstr(y, 0, author, self.color(*base_keys))
            y += 2
        except curses.error:
            pass

        if copyright:
            try:
                self.win.addstr(y, 0, copyright, self.color(*base_keys,'copyright'))
                y += 2
            except curses.error:
                pass

        if notes:
            lines = wrap('Notes: "'+notes+'"', self.wid)
            for i,line in enumerate(lines):
                try:
                    self.win.addstr(y, 0, line, self.color(*base_keys))
                    if i == 0:
                        self.win.chgat(y,0,5, self.color(*base_keys) | curses.A_BOLD)
                    y += 1
                except curses.error:
                    break

        self.need_redraw = False
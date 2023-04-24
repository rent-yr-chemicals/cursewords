import curses
import os
from string import ascii_lowercase, ascii_uppercase

from cursewords.gui.components import UIComponent

class Console(UIComponent):

    def __init__(self, hei, wid, y, x, win=None):

        UIComponent.__init__(self, hei, wid, y, x, win=win)

        self.prev_focus = None

        self.position = 0
        self.prompt = ' > '
        self.text = ''
        self.exception = None
        self.message = None

        self.history_buffer = None
        self.history_position = 0

        self.old_text = self.text
        self.old_position = self.position

        history_path = os.path.expanduser('~/.local/share/cursewords/history')
        if os.path.isfile(history_path):
            with open(history_path,'r') as f:
                self.history = f.read().splitlines()
        else:
            self.history = None

    def init_keys(self):

        self.bind_key(27, self.close)
        self.bind_key('\n', self.execute)

        self.bind_key(curses.KEY_LEFT, self.move_cursor, -1)
        self.bind_key(curses.KEY_RIGHT, self.move_cursor, +1)

        self.bind_key(curses.KEY_UP, self.scroll_history, 1)
        self.bind_key(curses.KEY_DOWN, self.scroll_history, -1)

        for key in map(chr,range(32,127)):
            self.bind_key(key, self.add_ch, key)
        self.bind_key(curses.KEY_BACKSPACE, self.delete_ch)

    def predraw(self):

        UIComponent.predraw(self)

        if self.visible:
            self.need_redraw = True
            # if self.text != self.old_text or self.position != self.old_position:
            #     self.old_text = self.text
            #     self.old_position = self.position
            #     self.need_redraw = True

    def draw(self):

        if self.exception:
            self.win.insstr(0, 0, '{:<{}}'.format(str(self.exception),self.wid), self.color('console', 'message','bad'))
            self.close()
            return

        if self.message:
            self.win.insstr(0, 0, '{:<{}}'.format(str(self.message),self.wid), self.color('console', 'message'))
            self.close()
            return

        space = self.wid - len(self.prompt + self.text) - 1

        self.win.addstr(0, 0, self.prompt, self.color('console', 'prompt'))
        self.win.insstr(' '+self.text+' '*space, self.color('console'))

        self.cw.ui.win.move(self.y, self.x + len(self.prompt) + 1 + self.position)

        self.need_redraw = False

    def open(self, text='', position=0, message=None, exception=None):

        self.visible = True
        self.cw.ui.status_bar.visible = False
        if self.cw.ui.status_bar.message:
            self.cw.ui.status_bar.message.kill()

        curses.curs_set(1)

        self.prev_focus = self.cw.ui.get_focus()
        if self.prev_focus:
            self.prev_focus.focused = False
        self.focused = True

        #self.prev_focus = next(component.get_focus() for component in self.cw.ui.components)
        #curses.cbreak()
        #self.prev_focus = next(component for component in self.cw.ui.components if component.focused)
        #self.focus()

        self.position = position
        self.text = text
        self.exception = None
        self.message = None

        if self.history:
            self.history_buffer = [text] + self.history
        else:
            self.history_buffer = [text]

        self.history_position = 0

    def close(self):

        curses.curs_set(0)
        self.cw.ui.win.move(0,0)

        self.visible = False
        self.cw.ui.status_bar.visible = True

        if self.cw.ui.get_focus() == self:
            self.prev_focus.focused = True

        self.focused = False

        self.position = 0
        self.text = ''
        self.exception = None
        self.message = None

    def execute(self):

        if not self.text:
            return

        if self.history:
            if self.text != self.history[0]:
                self.history = [self.text] + self.history
        else:
            self.history = [self.text]

        global cw, p
        cw = self.cw
        p = self.cw.notify

        success = False

        try:
            eval(self.text)
        except Exception:
            try:
                exec(self.text)
            except Exception as ex:
                exception = repr(ex)
                self.cw.notify(exception, bad=True)

        self.close()

        # if success:
        #     if self.message:
        #         self.need_redraw = True
        #     else:
        #         self.close()

    def add_ch(self,ch):

        before, after = self.text[:self.position], self.text[self.position:]
        self.text = before + ch + after
        self.move_cursor(1)
        self.history_buffer[self.history_position] = self.text

    def delete_ch(self):

        if len(self.text) > 0:
            before, after = self.text[:self.position], self.text[self.position:]
            self.text = before[:-1] + after
            self.move_cursor(-1)
            self.history_buffer[self.history_position] = self.text
        else:
            self.close()

    def move_cursor(self,d):

        new = self.position + d
        if new < 0 or new > len(self.text):
            return
        else:
            self.position += d

    def scroll_history(self,d):
        
        current = self.history_position
        new = current + d

        if new < 0 or new >= len(self.history_buffer):
            return
        else:
            self.history_position = new
            self.text = self.history_buffer[new]
            self.position = len(self.text)

    def save_history(self):

        data_dir = os.path.expanduser('~/.local/share/cursewords/')

        try:
            with open(data_dir+'history','w') as f:
                f.write('\n'.join(self.history))
        except FileNotFoundError:
            os.makedirs(data_dir)
            with open(data_dir+'history','w') as f:
                f.write('\n'.join(self.history))

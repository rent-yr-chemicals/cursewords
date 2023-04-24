from time import time

from cursewords.core.aware import ColorPaletteAware
from cursewords.gui.components import UIComponent
from cursewords.etc.truncate import truncate

class StatusBar(UIComponent):

    def __init__(self, hei, wid, y, x, win=None):

        UIComponent.__init__(self, hei, wid, y, x, win=win)

        self.visible = True
        self.message = None
        self._old_message = self.message

    def predraw(self):

        if self.message:
            if not self.message.is_alive():
                self.message = None

        if self._old_message != self.message:
            self._old_message = self.message
            self.need_redraw = True

        UIComponent.predraw(self)

    def draw(self):

        if self.need_redraw:

            self.win.erase()

            if self.message:

                self.win.insstr(0, 0, *self.message.get_content(self.wid))

            self.need_redraw = False

    def notify(self, text, color=[], lifetime=5):
        self.message = Message(text, color, lifetime)


class Message(ColorPaletteAware):

    def __init__(self, text, color=[], lifetime=5):

        self.born = time()
        self.lifetime = lifetime
        self._kill = False
        self.text = text
        self.attr = self.color('message', *color)

    def get_content(self, space):
        text = truncate(self.text, space)
        return text, self.attr

    def kill(self): # :(
        self._kill = True

    def is_alive(self):
        if self._kill:
            return False
        else:
            return time() - self.born < self.lifetime
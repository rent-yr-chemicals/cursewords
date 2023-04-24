#coding=utf-8

import curses
from collections import defaultdict
from functools import partial

from cursewords import Coord
from cursewords.core.aware import CWAware, ColorPaletteAware

class UIComponent(CWAware,ColorPaletteAware):

    margin = Coord(1,3)

    def __init__(self, hei, wid, y, x, win=None):

        from cursewords.gui.ui import UI

        self.visible = False
        self.old_visible = self.visible
        self.focused = False
        self.need_redraw = False

        self.parent = None

        if win is not None:
            if isinstance(self, UI):
                self.win = win
            else:
                self.win = win.derwin(hei,wid,y,x)

        self.hei, self.wid, self.y, self.x = hei, wid, y, x

        self.abs_y = y
        self.abs_x = x

        self.key_bindings = defaultdict(lambda: lambda: None)

    def __contains__(self, coords):

        y, x = coords

        if y < self.abs_y or x < abs_x:
            return False
        elif y > self.abs_y + self.hei or x > self.abs_x + self.wid:
            return False
        else:
            return True

    def get_focus(self):
        if self.focused:
            return self
        else:
            return None

    def bind_key(self, key, func, *args, **kwargs):

        if isinstance(key,str):
            key = ord(key)

        self.key_bindings[key] = partial(func, *args, **kwargs)

    def resize(self, hei, wid, y, x):
        
        self.win.erase()

        try:
            self.win.resize(hei, wid)
        except curses.error:
            self.win.mvderwin(0, 0)
            self.win.resize(hei, wid)

        try:
            self.win.mvderwin(y, x)
        except curses.error:
            self.win.resize(hei, wid)
            self.win.mvderwin(y, x)

        self.hei, self.wid = self.win.getmaxyx()
        self.y, self.x = self.win.getparyx()

        self.abs_y = self.y
        self.abs_x = self.x

        if self.parent:
            self.abs_y += self.parent.abs_y
            self.abs_x += self.parent.abs_x

        self.need_redraw = True

    def predraw(self):

        if self.visible != self.old_visible:
            self.old_visible = self.visible
            self.need_redraw = True
            if not self.visible:
                self.win.erase()

    def draw_box(self, ymin, xmin, ymax, xmax, attr=0):

        self.win.hline(ymin, xmin + 1, curses.ACS_HLINE, xmax - xmin - 1, attr)
        self.win.hline(ymax, xmin + 1, curses.ACS_HLINE, xmax - xmin - 1, attr)
        self.win.vline(ymin + 1, xmin, curses.ACS_VLINE, ymax - ymin - 1, attr)
        self.win.vline(ymin + 1, xmax, curses.ACS_VLINE, ymax - ymin - 1, attr)
        self.win.addch(ymin, xmin, curses.ACS_ULCORNER, attr)
        self.win.addch(ymin, xmax, curses.ACS_URCORNER, attr)
        self.win.addch(ymax, xmin, curses.ACS_LLCORNER, attr)
        self.win.addch(ymax, xmax, curses.ACS_LRCORNER, attr)

    def draw(self):

        pass

    def click(self, event):

        pass

    def init_keys(self):

        pass

class ComponentContainer(UIComponent):

    def __init__(self, hei, wid, y, x, win=None):
        UIComponent.__init__(self, hei, wid, y, x, win=win)
        self.components = []

    def predraw(self):
        UIComponent.predraw(self)
        for component in self.components:
            component.predraw()

    def draw(self):
        for component in self.components:
            if self.need_redraw:
                component.need_redraw = True
            if component.visible:
                component.draw()
        self.need_redraw = False

    def init_keys(self):
        for component in self.components:
            component.init_keys()

    def get_focus(self):
        if self.focused:
            return self
        for component in self.components:
            obj = component.get_focus()
            if obj is not None:
                return obj
        return None

    def add_component(self, component):
        self.components.append(component)
        component.parent = self
        component.abs_y = component.y + self.abs_y
        component.abs_x = component.x + self.abs_x
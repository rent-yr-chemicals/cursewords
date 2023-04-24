#coding=utf-8

import curses

from textwrap import wrap
from time import time

from cursewords.gui.components import UIComponent, ComponentContainer
from cursewords.etc.truncate import trunc_and_pad

class Browser(ComponentContainer):

    header_left = 'Welcome to CurseWords™!'
    header_right = 'Version 69.420.1312'
    warranty_or_lack_thereof = (
        'DISCLAIMER: This is free software, distributed in the hope that it will, frankly, never see the light of day,'
        ' and is provided with absolutely no warranty, without even the IMPLIED warranty of MERCHANTABILITY,'
        ' FITNESS FOR A PARTICULAR PURPOSE, nor even SUITABILITY FOR VIEWING BY HUMAN EYES. The code contained'
        ' herein is unstable, poorly designed, and is provided with an airtight, 100% guarantee to break.'
        ' If you\'re able to run it, don\'t blame us.'
    )

    def __init__(self,hei,wid,y,x,win=None):

        ComponentContainer.__init__(self,hei,wid,y,x,win=win)

        self.interior = BrowserInterior(1, 1, 0, 0, win=self.win)
        self.add_component(self.interior)

        self.unwarranty_lines = []

        self.last_drawn = time()

        self.headers = {
            'title': 'Title',
            'author': 'Author',
            'source': 'Source',
            'status': 'Status',
            'tags': 'Tags',
            'import_date': 'Imported',
            'start_date': 'Started',
            'completion_date': 'Completed'
        }

    # def init_keys(self):
    #     ComponentContainer.init_keys(self)
    #     self.bind_key(':', self.cw.ui.console.open)

    def open(self):

        self.visible = True

        for component in self.components:
            component.open()

        self.resize(self.hei, self.wid, self.y, self.x)

    def close(self):

        self.visible = False

        for component in self.components:
            component.close()

    def resize(self, hei, wid, y, x):

        ComponentContainer.resize(self, hei, wid, y, x)

        self.unwarranty_lines = wrap(self.warranty_or_lack_thereof, self.wid)

        try:
            self.interior.resize(self.hei - 4 - len(self.unwarranty_lines), self.wid, 3, 0)
        except curses.error:
            pass

    def predraw(self):

        if self.cw.library.last_touched > self.last_drawn:
            self.need_redraw = True

        if self.interior._old_fields != self.interior.fields:
            self.need_redraw = True

        if self.interior._old_ratios != self.interior.column_ratios:
            self.need_redraw = True

        ComponentContainer.predraw(self)

    def draw(self):

        if self.need_redraw:

            self.last_drawn = time()

            self.win.erase()
            self.win.addstr(0, 0, self.header_left, curses.A_BOLD)
            self.win.addstr(0, self.wid - 1 - len(self.header_right), self.header_right, self.color('info','copyright'))
            
            column_headers = []
            for field, wid in zip(self.interior.fields, self.interior.column_widths):
                header_attr = ['column_headers']
                field_displayed = self.headers[field]
                if field in self.cw.library.sort_by:
                    header_attr.append('sort_key')
                    sort_level = self.cw.library.sort_by.index(field) + 1
                    if self.cw.library.sort_reverse[field]:
                        header_text = trunc_and_pad(field_displayed, wid-4) + '僚 ' + str(sort_level)
                    else:
                        header_text = trunc_and_pad(field_displayed, wid-4) + '寮 ' + str(sort_level)
                else:
                    header_text = trunc_and_pad(field_displayed, wid)
                column_headers.append((header_text, header_attr))
                #= map(trunc_and_pad, self.interior.fields, self.interior.column_widths)

            self.win.move(2,0)

            for i, (header_field, header_attr) in enumerate(column_headers):
                if i != 0:
                    self.win.addch(curses.ACS_VLINE, self.color(*header_attr, 'grid_lines'))
                self.win.addstr(header_field, self.color(*header_attr))

            y = self.hei - len(self.unwarranty_lines)
            for i, line in enumerate(self.unwarranty_lines):
                if i == 0:
                    self.win.addstr(y, 0, line[:10], self.color('info','copyright') | curses.A_BOLD)
                    self.win.addstr(y, 10, line[10:], self.color('info','copyright'))
                else:
                    self.win.addstr(y, 0, line, self.color('info','copyright'))
                y += 1

        ComponentContainer.draw(self)
        
class BrowserInterior(UIComponent):

    def __init__(self,hei,wid,y,x,win=None):

        UIComponent.__init__(self,hei,wid,y,x,win=win)

        self.lines = None
        self.need_recompute_lines = False
        self.need_recompute_columns = False

        self.cursor = 0
        self._old_cursor = self.cursor

        self.first_line = 0
        self.old_first_line = 0

        self._column_widths = None
        self.column_ratios = [16,6,2,3,2,2,2]
        self._old_ratios = self.column_ratios
        self.last_drawn = time()

        self.fields = [
            'title',
            'author',
            'source',
            'status',
            'import_date',
            'start_date',
            'completion_date'
        ]

        self._old_fields = self.fields

        self.display_functions = {
            'title': lambda item, wid: (item['title'].strip(), 'normal'),
            'author': lambda item, wid: (item['author'].strip(), 'normal'),
            'source': lambda item, wid: (item['source'].strip() if item['source'] is not None else '', 'normal'),
            'status': lambda item, wid: self._format_item_status(item),
            'tags': lambda item, wid: (' '.join([tag for tag in item['tags']]), 'normal'),
            'import_date': lambda item, wid: ('{:>{}}'.format(item['import_date'].split(' ')[0], wid) if item['import_date'] is not None else '', 'normal'),
            'start_date': lambda item, wid: ('{:>{}}'.format(item['start_date'].split(' ')[0], wid) if item['start_date'] is not None else '', 'normal'),
            'completion_date': lambda item, wid: ('{:>{}}'.format(item['completion_date'].split(' ')[0], wid) if item['completion_date'] is not None else '', 'normal')
        }

    def init_keys(self):

        self.bind_key(':', self.cw.ui.console.open)
        self.bind_key(curses.KEY_DOWN, self.move, d=1)
        self.bind_key(curses.KEY_UP, self.move, d=-1)
        self.bind_key(curses.KEY_RIGHT, self.open_file)
        self.bind_key('\n', self.open_file)
        self.bind_key(4, self.cw.exit)

    def open(self):

        self.visible = True
        self.focused = True
        self.need_recompute_lines = True
        self.need_recompute_columns = True

        self.cursor = 0
        self._old_cursor = self.cursor

        self.win.bkgd(' ', self.color('normal'))

    def close(self):

        self.visible = False
        self.focused = False

        self.win.bkgd(' ', self.color('none'))

    def this_file(self):
        return self.cw.library[self.cursor]

    def open_file(self):
        self.cw.open_file(self.cursor)

    def tag(self,tag=None,append=False):
        self.cw.library.tag_file(self.cursor, tag, append=append)

    def move(self, d=1):
        new = self.cursor + d
        if new < len(self.lines) and new >= 0:
            self.cursor = new

    def resize(self, *args):
        UIComponent.resize(self, *args)
        self.need_recompute_columns = True
        self.need_recompute_lines = True

    @property
    def column_widths(self):
        if self._column_widths is not None:
            return self._column_widths
        else:
            ratios = self.column_ratios[:len(self.fields)]
            usable = self.wid - (len(ratios)*3 - 1)
            assert usable >= len(ratios)
            result = [max(1,(item*usable)//sum(ratios)) for item in ratios]
            err = usable - sum(result)
            i_stretch = self.column_ratios.index(max(ratios))
            result = [item + err if i == i_stretch else item for i,item in enumerate(result)]
            self._column_widths = result
            self.need_recompute_columns = False
            return result

    def predraw(self):

        if self.cursor != self._old_cursor:
            self._old_cursor = self.cursor
            self.need_redraw = True

        if self.cw.library.last_touched > self.last_drawn:
            self.need_recompute_lines = True

        if self._old_ratios != self.column_ratios:
            self._old_ratios = self.column_ratios
            self.need_recompute_columns = True

        if self._old_fields != self.fields:
            self.need_recompute_columns = True
            self._old_fields = self.fields
            if len(self.column_ratios) < len(self.fields):
                self.column_ratios += [1] * (len(self.fields) - len(self.column_ratios))

        if self.need_recompute_columns:
            self._column_widths = None
            self.need_recompute_lines = True
            self.need_redraw = True

        if self.need_recompute_lines:
            self._get_lines(force=True)

        UIComponent.predraw(self)

    def draw(self):

        if not self.need_redraw:
            return

        self.last_drawn = time()

        self.win.erase()

        y = 0

        lines = self._get_lines()

        self.first_line = self._get_first_line()
        self.old_first_line = self.first_line

        try:

            for line in lines[self.first_line:]:
                    self._draw_libitem(y, line)
                    y += 1

            if y < self.hei:
                x = self.column_widths[0] + 2
                self.win.vline(y, x, curses.ACS_VLINE, y - self.hei, self.color('grid_lines'))
                x += self.column_widths[1] + 3
                self.win.vline(y, x, curses.ACS_VLINE, y - self.hei, self.color('grid_lines'))
                x = self.column_widths[2] + 3
                self.win.vline(y, x, curses.ACS_VLINE, y - self.hei, self.color('grid_lines'))

        except curses.error:
            pass

        self.need_redraw = False

    def _get_lines(self,force=False):

        if force or self.lines is None:

            self.lines = []

            for i,item in enumerate(self.cw.library.list_items()):                

                line_items = []

                for field, wid in zip(self.fields, self.column_widths):
                    field_text, field_attr = self.display_functions[field](item, wid)
                    line_items.append((trunc_and_pad(field_text, wid), field_attr))

                base_attr = ['browser_item']
                if i % 2:
                    base_attr.append('shaded')

                self.lines.append((line_items, base_attr))

            self.need_redraw = True

        return self.lines

    def _format_item_status(self, item):

        # * xx% --:--:--

        status = item['status']
        attr = ['item_status']

        if status['filled'] > 0 or status['timer'] > 0:
            in_progress = True
        else:
            in_progress = False

        if not (in_progress or status['complete']):
            return '', attr

        if status['complete']:
            mark = '🗹'
        elif in_progress:
            mark = ''
        else:
            mark = ''

        if in_progress or status['complete']:
            pct = str((status['filled']*100)//status['fillable'])+'%'
        else:
            pct = ''

        if status['timer'] > 0:
            hours, minutes = divmod(status['timer'], 3600)
            minutes, seconds = divmod(minutes, 60)
            time_str = '{:>2}:{:0>2}:{:0>2}'.format(int(hours), int(minutes), int(seconds))
        else:
            time_str = '-:--:--'

        line = '{:<2} {:>4} {:>8}'.format(mark, pct, time_str)

        if status['complete']:
            attr.append('complete')
        elif in_progress:
            attr.append('in_progress')

        return line, attr
    
    def _draw_libitem(self, y, line):

        line_content, base_color = line

        line_color = []

        if y + self.first_line == self.cursor:
            line_color.append('current')

        self.win.move(y, 0)
        for i, (item, item_color) in enumerate(line_content):
            if i != 0:
                self.win.addch(curses.ACS_VLINE, self.color('grid_lines', *base_color, *line_color))
            self.win.addstr(item, self.color(*base_color, *line_color, *item_color))

    def _get_first_line(self):
        '''Stolen (more or less verbatim) from ranger.gui.widgets.browsercolumn :P'''
        offset = 8
        total_lines = len(self.lines)
        hei = self.hei
        cursor = self.cursor
        old = self.old_first_line
        cursor_relative = cursor - old

        # Note: "upper" and "lower" refer to line index, not position on screen
        # (i.e. "upper" = "bottom of screen", "lower" = "top of screen")
        upper_limit = hei - 1 - offset
        lower_limit = offset

        if old < 0:
            return 0

        if total_lines < hei:
            return 0

        # if hei//2 < offset:
        #     return min(dirsize - winsize, max(0, index - (hei//2)))

        if old > total_lines - hei:
            self.old_first_line = total_lines - hei
            return self._get_first_line()

        if cursor_relative < upper_limit and cursor_relative > lower_limit:
            return old

        if cursor_relative > upper_limit:
            return min(total_lines - hei, old + (cursor_relative - upper_limit))

        if cursor_relative < upper_limit:
            return max(0, old - (lower_limit - cursor_relative))

        return old
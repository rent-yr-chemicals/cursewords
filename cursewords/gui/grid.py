import curses

from functools import partial
from string import ascii_lowercase,ascii_uppercase
from textwrap import wrap

from cursewords import YX, Coord, HAS_FANCY_CHARS
from cursewords.gui.components import UIComponent
from cursewords.container.square import Square
from cursewords.etc.special_chars import lines, intersections, plain_ints, BLOCK

from time import time

START_INTER_CHARS = 0xE800

class Grid(UIComponent):

    margin = Coord(1,3)

    def __init__(self, hei, wid, y, x, win=None):

        UIComponent.__init__(self, hei, wid, y, x, win=win)

        self.src = None
        self.is_initialized = False
        self.is_ready = False

        self.grid_hei = 0
        self.grid_wid = 0

        self._grid_template_cache = dict()
        self._cache_gen = None

        self.old_cursor = None
        self.old_direction = None

        self.build_prog = 0

    def init_keys(self):

        #self.bind_key(' ', self.cw.notify, 'foo')
        self.bind_key(' ', self.cw.toggle_direction)

        self.bind_key(curses.KEY_DOWN, self.cw.move_to_next_valid, 1, 0)
        self.bind_key(curses.KEY_UP, self.cw.move_to_next_valid, -1, 0)
        self.bind_key(curses.KEY_RIGHT, self.cw.move_to_next_valid, 0, 1)
        self.bind_key(curses.KEY_LEFT, self.cw.move_to_next_valid, 0, -1)

        self.bind_key('\t', self.cw.next_word)
        self.bind_key(curses.KEY_BTAB, self.cw.prev_word)

        self.bind_key(curses.KEY_BACKSPACE, self.cw.clear_square)
        self.bind_key(curses.KEY_DC, self.cw.clear_square, False)

        for key in ascii_lowercase:
            self.bind_key(key, self.cw.fill_square, key)
        for key in ascii_uppercase:
            self.bind_key(key, self.cw.fill_square, key, False)

        self.bind_key('?', self.cw.check_grid)

        self.bind_key(':', self.cw.ui.console.open)
        self.bind_key(27, self.cw.ui.console.open, text='cw.fill_square("")', position=16)
        self.bind_key(18, self.cw.ui.console.open, text='cw.fill_square("")', position=16)

        self.bind_key(24, self.cw.save, prompt=False)
        self.bind_key(5, self.cw.save, prompt=True)
        self.bind_key(4,self.cw.close_file)

    def open(self,src):

        self.cw.ui.block_input = True
        self.src = src
        self.visible = True

        self.build()

    def close(self):

        self.src = None
        self.visible = False
        self.win.bkgd(' ',0)

        self.focused = False
        self.old_cursor = None
        self.old_direction = None
        self.grid_hei = 0
        self.grid_wid = 0
        self._grid_template_cache = dict()
        self.is_initialized = False
        self.is_ready = False

    def build(self):

        # sanity check, should never be true here
        if self.src is None:
            return

        self.grid_hei, self.grid_wid = self.src.height, self.src.width
        self.fit_to_source()

        # placeholder, make fancy later
        self.old_cursor = self.cw.ui.solver.cursor
        self.old_direction = self.cw.ui.solver.direction

        Square.link_grid(self)

        self._cache_gen = self.make_cache()
        self.cw.ui.win.nodelay(1)
        curses.cbreak()
        self.is_initialized = True

    def fit_to_source(self):

        if self.src:
            hei, wid = self._get_win_dimens()
            UIComponent.resize(self, hei, wid, 0, 0)
        else:
            UIComponent.resize(self, 1, 1, 0, 0)

    def make_cache(self):

        i = 0

        for y in range(self.grid_hei):
            for x in range(self.grid_wid):
                self._grid_template_cache[(y,x)] = self._make_grid_template(cursor=Coord(y,x))
                yield i
                i += 1


    def predraw(self):

        # if initialized, do additional checks
        if self.is_initialized:
            if self.cw.ui.solver.cursor != self.old_cursor or self.cw.ui.solver.direction != self.old_direction:
                self.old_cursor = self.cw.ui.solver.cursor
                self.old_direction = self.cw.ui.solver.direction
                self.need_redraw = True

        # redraw if visibility changed, erase if invisible
        UIComponent.predraw(self)

    def draw(self):

        if not self.need_redraw:
            return

        if self.src is None or not self.is_initialized:
            return

        win = self.win

        bkgd_keys = ['grid_lines']
        if self.cw.ui.solver.paused:
            bkgd_keys.append('paused')
        win.bkgd(' ',self.color(*bkgd_keys))

        win.erase()

        if not self.is_ready:
            try:
                #build_progress = 0
                build_progress = next(self._cache_gen)
                build_pct = (build_progress * 100) // (self.grid_hei * self.grid_wid)
                n_dots = (build_progress // 20) % 4
                message_ellipsis = '{:<3}'.format('.'*n_dots)
                self.win.addstr(1,3,'Loading{} {:>3}%'.format(message_ellipsis, build_pct), self.color('normal'))
                return
            except StopIteration:
                self.is_ready = True
                self.cw.ui.block_input = False
                self.cw.ui.win.nodelay(0)
                curses.halfdelay(5)

        template = self._grid_template_cache.get(self.cw.ui.solver.cursor, self._make_grid_template(cursor=self.cw.ui.solver.cursor))

        for y in range(self.margin.y, self.hei - self.margin.y):

            line_template = template[y - self.margin.y]

            win.move(y, self.margin.x)

            for item in line_template:

                if isinstance(item,dict):
                    text = item['fmt'].format(item['fill_func']())
                    if len(text) > 3:
                        text = text[0:2] + b'\xE2\x80\xA6'.decode('utf-8')
                    attr = item['attr_func']()
                    item = (text, attr)

                win.addstr(*item)

        if self.cw.ui.solver.paused:
            self._draw_paused_message()

        self.need_redraw = False

    def _draw_paused_message(self):

            start_x = self.margin.x + 2
            end_x = self.wid - (self.margin.x + 3)
            inner_space = end_x - start_x - 3

            message_text = '[PAUSED - Press any key to resume]' if self.src.timer.elapsed else '[Press any key to begin]'
            exit_text = '[Press CTRL-D to exit]'
            #message_text = ''
            #exit_text = ''

            message = wrap(message_text, inner_space), self.color('grid_lines'), 'center'
            title_lines = wrap(self.src.title, inner_space), self.color('normal') | curses.A_BOLD, 'center'
            author_lines = wrap(self.src.author, inner_space), self.color('normal'), 'center'
            note_lines = wrap(self.src.notes, inner_space), self.color('normal'), 'left'
            copyright_lines = wrap(self.src.copyright, inner_space), self.color('grid_lines'), 'left'
            exit = wrap(exit_text, inner_space), self.color('grid_lines'), 'left'

            vpadding = '', self.color('normal'), 'left'

            all_lines = [message, title_lines, author_lines, copyright_lines, exit]

            lines = [(text, attr, alignment) for sublist, attr, alignment in all_lines for text in sublist+[''] if sublist][:-1]
            avail = self.hei - 4
            avail -= len(lines)
            avail -= 2
            if note_lines:
                avail -= 1

            if avail < len(note_lines[0]):
                new_note_lines = note_lines[0][:avail - 1] + [note_lines[0][avail][:-1]+'…']
                note_lines = new_note_lines, note_lines[1], note_lines[2]

            all_lines = [message, title_lines, author_lines, note_lines, copyright_lines, exit]

            lines = [(text, attr, alignment) for sublist, attr, alignment in all_lines for text in sublist+[''] if sublist][:-1]
            lines = [vpadding] + lines + [vpadding]

            text_hei = len(lines)
            start_y = max((self.hei//2) - (text_hei//2) - 1, 1)
            end_y = min(start_y + text_hei + 1, self.hei - 2)
            
            self.draw_box(start_y, start_x, end_y, end_x, self.color('normal'))

            y = start_y + 1
            for text, attr, alignment in lines:
                # if y == end_y:
                #     break
                if alignment == 'center':
                    line = ' {:^{}} '.format(text, inner_space)
                else:
                    line = ' {:<{}} '.format(text, inner_space)
                try:
                    self.win.addstr(y, start_x + 1, line, attr)
                except curses.error:
                    return
                y += 1

    def _get_win_dimens(self):
        # Cover height/width of the puzzle itself to
        # dimensions in characters of the displayed grid
        sq_inner_size, sq_border_size = Square.get_dimens()

        return map(
            lambda inner, border, grid, margin: inner * grid + border * (grid + 1) + 2 * margin,
            sq_inner_size, sq_border_size, (self.grid_hei, self.grid_wid), self.margin
        )

    def _make_grid_template(self, cursor=None):

        if self.src.squares[cursor.y][cursor.x].is_block:
            return None

        sq_inner_size, sq_border_size = Square.inner_size, Square.border_size

        lines=[]

        for y in range(self.margin.y, self.hei-self.margin.y):

            line = []

            rel_y = self._winyx_to_rel_yx(y=y, x=None).y

            if rel_y:

                for x in range(self.margin.x, self.wid-self.margin.x):

                    sq_y,sq_x = self._winyx_to_sq_yx(y=y, x=x)
                    rel_x = self._winyx_to_rel_yx(y=y, x=x).x

                    if rel_x == 0:

                        line += [(self._get_border_ch(y, x, cursor=cursor,direction='v'),)]

                    elif rel_x == 1 and sq_x is not None:

                        # fill text/attributes are the only parts that can't be
                        # pre-computed, so we're just including a formatter and
                        # links to the current square's methods
                        sq = self.src.squares[sq_y][sq_x]
                        line += [ {
                            'fmt': '{{:^{}}}'.format(sq_inner_size.x),
                            'fill_func': partial(self._draw_sq, sq),
                            'attr_func': partial(self._get_sq_attr, sq)
                           # 'fill_func': sq.get_fill,
                           # 'attr_func': sq.get_attr
                        } ]

                    else:
                        continue

            else:

                for x in range(self.margin.x,self.wid-self.margin.x):

                    sq_y,sq_x = self._winyx_to_sq_yx(y=y, x=x)
                    rel_x = self._winyx_to_rel_yx(y=y, x=x).x

                    if rel_x == 0:

                        inter_ch = self._get_inter_ch2(y,x,cursor=cursor)
                        line += [(inter_ch,)]

                    elif rel_x == 1 and sq_x is not None: # sanity check -- sq_x *should* never be None here

                        border_ch = self._get_border_ch(y, x, cursor=cursor, direction='h')

                        if sq_y is not None and self.src.squares[sq_y][sq_x].n:
                            n = str(self.src.squares[sq_y][sq_x].n)
                            if sq_y > 0:
                                attr = curses.A_REVERSE if self.src.squares[sq_y - 1][sq_x].is_block else 0
                            else:
                                attr = 0
                            line += [(n,attr), (border_ch * (sq_inner_size.x-len(n)),)]
                        else:
                            line += [(border_ch * sq_inner_size.x,)]

                    else:
                        continue

            lines.append(line)

        return lines

    def _draw_sq(self, sq):

        if self.cw.ui.solver.paused:
            return BLOCK*3 if sq.is_block else ''
        else:
            return sq.get_fill()

    def _get_sq_attr(self, sq):

        if self.cw.ui.solver.paused:
            return 0
        else:
            return sq.get_attr()

    def _get_inter_ch(self, y, x, cursor=None):

        s,e = self._winyx_to_sq_yx(y,x)
        n,w = self._winyx_to_sq_yx(y-1,x-1)

        keys = []

        for sq_y,sq_x in [(n,w),(n,e),(s,w),(s,e)]:

            if None in (sq_y,sq_x):
                keys.append('n')
            else:
                sq = self.src.squares[sq_y][sq_x]
                keys.append(sq.get_ch_key(cursor=cursor))

        return intersections[keys]

    def _get_inter_ch2(self, y, x, cursor=None):

        s, e = self._winyx_to_sq_yx(y, x)
        n, w = self._winyx_to_sq_yx(y-1, x-1)

        result = 0

        if HAS_FANCY_CHARS:

            for i, (y, x) in enumerate([(n, w), (n, e), (s, w), (s, e)]):
                if None in (y, x):
                    pass
                else:
                    sq = self.src.squares[y][x]
                    result |= sq.get_ch_key2(cursor=cursor) << 2*i

            result += START_INTER_CHARS
            return chr(result)

        else:

            keys = []

            for (y, x) in [(n, w), (n, e), (s, w), (s, e)]:
                if None in (y, x):
                    keys.append(0)
                else:
                    keys.append(1)

            return plain_ints[tuple(keys)]


    def _get_border_ch(self, y, x, cursor=None, direction=None):

        sq_yx2 = self._winyx_to_sq_yx(y,x)

        if direction == 'h':

            sq_yx1 = self._winyx_to_sq_yx(y-1,x)

        elif direction == 'v':

            sq_yx1 = self._winyx_to_sq_yx(y,x-1)

        keys = [direction]

        for coords in [sq_yx1,sq_yx2]:
            if None in coords:
                    keys.append('n')
            else:
                sq = self.src.squares[coords.y][coords.x]
                keys.append(sq.get_ch_key(cursor=cursor))

        if HAS_FANCY_CHARS:
            return lines[keys]
        else:
            if direction == 'h':
                return '═' if 's' in keys else '━'
            else:
                return '║' if 's' in keys else '┃'
            return lines[keys]

    def _sq_yx_to_winyx(self, y=None, x=None, xshift=0, yshift=0):

        # by default, returns coords of the intersection at the
        # upper-left corner of the square. To access coordinates
        # inside the square, use xshift and yshift

        inner,border = Square.get_dimens()
        sq_total = inner + border

        if y == None:
            win_y = None
        else:
            win_y = self.margin.y + y * sq_total.y
            win_y += yshift
        
        if x == None:
            win_x = None
        else:
            win_x = self.margin.x + x * sq_total.x
            win_x += xshift

        return YX(win_y,win_x)


    def _winyx_to_sq_yx(self, y=None, x=None):

        # Convert window coordinates to grid coordinates

        inner,border = Square.get_dimens()
        sq_total = inner + border

        if y is None:
            sq_y = None
        else:
            sq_y = (y - self.margin.y) // sq_total.y
            if sq_y not in range(self.grid_hei):
                sq_y = None

        if x is None:
            sq_x = None
        else:
            sq_x = (x - self.margin.x) // sq_total.x
            if sq_x not in range(self.grid_wid):
                sq_x = None

        return YX(sq_y,sq_x)

    def _winyx_to_rel_yx(self, y=None, x=None):

        # Convert window coordinates to relative coordinates within a grid square

        inner,border = Square.get_dimens()
        sq_total = inner + border

        if y is None:
            rel_y = None
        else:
            rel_y = (y - self.margin.y) % sq_total.y

        if x is None:
            rel_x = None
        else:
            rel_x = (x - self.margin.x) % sq_total.x

        return YX(rel_y, rel_x)
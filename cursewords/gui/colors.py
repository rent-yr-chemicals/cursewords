import curses
from functools import lru_cache

black = curses.COLOR_BLACK
blue = curses.COLOR_BLUE
cyan = curses.COLOR_CYAN
green = curses.COLOR_GREEN
magenta = curses.COLOR_MAGENTA
red = curses.COLOR_RED
white = curses.COLOR_WHITE
yellow = curses.COLOR_YELLOW
bright = 8

normal = curses.A_NORMAL
bold = curses.A_BOLD
blink = curses.A_BLINK
reverse = curses.A_REVERSE
underline = curses.A_UNDERLINE
invisible = curses.A_INVIS
dim = curses.A_DIM

class ColorKeys(object):

    def __init__(self,*keys):

        for key in keys:
            self.__dict__[key] = True

class ColorPalette(object):

    next_avail = 1

    def __init__(self, selector_func):
        self.selector = selector_func
        self._color_dict = dict()
        
    def new_color(self,fg, bg, attr):
        curses.init_pair(ColorPalette.next_avail, fg, bg)
        self._color_dict[(fg, bg, attr)] = curses.color_pair(ColorPalette.next_avail) | attr
        ColorPalette.next_avail += 1

    @lru_cache(maxsize=None)
    def color(self,*keys):
        fg, bg, attr = self.selector(ColorKeys(*keys))
        try:
            return self._color_dict[(fg, bg, attr)]
        except KeyError:
            self.new_color(fg, bg, attr)
            return self._color_dict[(fg, bg, attr)]

COLOR_KEYS = [
    'none', 'normal', 'bad', 'paused',
    'border', 'grid_lines', 'title',
    'square','current','highlighted','locked','shaded',
    'clue','active_column',
    'console','prompt','message',
    'info','copyright','author','notes',
    'column_headers', 'sort_key',
    'browser_item', 'item_status', 'in_progress', 'complete',
]

for key in COLOR_KEYS:
    setattr(ColorKeys,key,False)

# From kitty.conf:
#
# color100  #959696
# color101  #eff0f1
# color104  #3daee9
# color108  #93cee9
# color109  #d5eaf7
# color111  #ffee00
# color112  #e5ccff
# color137  #55aa00
# color138  #aaff7f
#
# xterm256 default:
#
# color223  #ffd7af

def default_theme(keys):

    fg = black
    bg = white + bright
    attr = normal

    if keys.square:

        attr |= bold

        if keys.highlighted:
            if keys.shaded:
                if keys.current:
                    bg = 111
                else:
                    bg = 112
            else:
                if keys.current:
                    bg = 109
                else:
                    bg = 108
        elif keys.shaded:
            bg = 223
        if keys.bad:
            fg = red
        elif keys.locked:
            fg = black
            attr = normal

    elif keys.console:
        if keys.prompt:
            fg = white
            fg += bright
            bg = 104

    elif keys.message:
        bg = 101
        if keys.bad:
            fg = red
            fg += bright
            attr |= bold

    elif keys.info:
        if keys.border:
            fg += bright
            #fg = 100
            #bg = -1
        elif keys.clue:
            bg = white + bright
            fg = black
            if keys.paused:
                fg += bright
        elif keys.copyright:
            fg = 100
            bg = -1
        else:
            fg = -1
            bg = -1

    elif keys.clue:
        if keys.paused:
            fg = 100
        else:
            if keys.highlighted or keys.title:
                attr |= bold
            if keys.active_column:
                if keys.highlighted:
                    bg = 108
            else:
                fg = 100
                if keys.highlighted:
                    bg = 109
            if keys.shaded:
                bg = 223

    elif keys.browser_item:
        if keys.current:
            bg = 104
        elif keys.shaded:
            bg = 109
        if keys.item_status:
            if keys.complete:
                if keys.current:
                    fg = 138
                else:
                    fg = 137
            # elif keys.in_progress:
            #     fg = curses.COLOR_YELLOW

    elif keys.column_headers:
        bg = 108
        if keys.sort_key:
            attr |= bold

    elif keys.normal:
        fg = black
        bg = white + bright
        attr = normal

    elif keys.none:
        fg = -1
        bg = -1

    if keys.grid_lines:
        if keys.paused:
            fg = 101
            bg = white
            bg += bright
        else:
            fg += bright

    return fg, bg, attr


    # Why were these left here?
    #
    # curses.init_pair(6, curses.COLOR_RED, 108) #bad hightlight circle
    # curses.init_pair(7, curses.COLOR_RED, 223) #bad circle
    # curses.init_pair(8, curses.COLOR_BLACK, 223) #circle
    # curses.init_pair(9, curses.COLOR_BLACK, 108) #highlight circle

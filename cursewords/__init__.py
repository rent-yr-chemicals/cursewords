def check_box_glyphs():
    import os
    import sys

    if os.environ['TERM'] != 'xterm-kitty':
        return False

    char_range = [(0xe800, 0xe900), (0x24dc, 0x24e0)]

    sys.path.insert(0,os.environ['KITTY_INSTALLATION_DIR'])
    from kitty.fonts.box_drawing import box_chars
    
    for block in char_range:
        for code_pt in range(*block):
            if chr(code_pt) not in box_chars:
                return False

    return True



class YX(tuple):
    def __new__(self,y,x):
        return super(YX,self).__new__(self,(y,x))
    def __init__(self,y,x):
        self.y = y
        self.x = x

class Coord(YX):
    def __add__(self,other):
        assert isinstance(other,Coord), 'Operand {} is of type {}'.format(str(other),str(type(other)))
        return Coord(self.y+other.y,self.x+other.x)
    def __radd__(self,other):
        assert isinstance(other,Coord), 'Operand {} is of type {}'.format(str(other),str(type(other)))
        return Coord(other.y+self.y,other.x+self.x)
    def __mul__(self,other):
        return Coord(self.y*other,self.x*other)
    def __rmul__(self,other):
        return Coord(self.y*other,self.x*other)

class Directional(tuple):
    def __new__(self,down=None,across=None):
        return super(Directional,self).__new__(self,(down,across))
    def __init__(self,down=None,across=None):
        self.down = down
        self.across = across
    def __getitem__(self,key):
        if isinstance(key,Directional):
            if key.down:
                return self.down
            elif key.across:
                return self.across
            else:
                return None
        else:
            return tuple.__getitem__(self,key)

HAS_FANCY_CHARS = check_box_glyphs()

from cursewords.main import main
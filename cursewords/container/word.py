import re

from cursewords import Coord, Directional
from cursewords.core.aware import CWAware
from cursewords.container.square import Square

class Word(object):

    def __init__(self, y, x, direction, word, clue, n):

        self.start = Coord(y,x)
        self.direction = direction
        self.solution = word
        self.clue = clue
        self.n = n

        self.squares = []
        self.next = None
        self.prev = None

        self.refs = self._parse_crossrefs()

    def link_squares(self,squares):

        d = Coord(*map(int,self.direction))
        square_coords = [self.start+(i*d) for i in range(len(self.solution))]      

        for y,x in square_coords:

            sq = squares[y][x]
            self.squares.append(sq)
            sq.link_word(self)

    def _parse_crossrefs(self):
        matches = re.finditer(r'(?P<nums>(\d+-/?,? ?(?: and )?)+)(?P<direction>across|down)',self.clue,re.IGNORECASE)
        if not matches:
            return None
        else:
            result = []
            for match in matches:
                direction = Directional(across=True, down=False) if match.group('direction').lower() == 'across' else Directional(across=False, down=True)
                for n in re.findall(r'\d+', match.group('nums')):
                    n = int(n.rstrip('-'))
                    result.append((n, direction))
            return result

    def __contains__(self,item):

        if isinstance(item,Coord):
            if any([sq.coords == item for sq in self.squares]):
                return True
            else:
                return False

        elif isinstance(item,Square):
            if item in self.squares:
                return True
            else:
                return False
        else:
            return False

    def __len__(self):
        return len(self.squares)

    def __getitem__(self,key):
        return self.squares[key]

    def __iter__(self):
        return iter(self.squares)

    def __reversed__(self):
        return reversed(self.squares)

    def __str__(self):
        return str(self.solution)

class Clue(object):

    def __init__(self,text):
        self.text=text

    def _parse_crossrefs(self):
        matches = re.findall(r'((?:\d*-,? ?(?: and )?)*)(across|down)',s,re.IGNORECASE)
        return refs
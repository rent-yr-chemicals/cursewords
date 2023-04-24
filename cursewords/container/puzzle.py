import re
import sys
import os.path
from shutil import get_terminal_size
from textwrap import wrap
from collections import namedtuple

from cursewords import Coord, Directional
from cursewords.container.square import Square
from cursewords.container.word import Word
from cursewords.etc.special_chars import webding_to_unicode, unicode_to_webding
from cursewords.etc.timer import Timer

ACROSS = 0
DOWN = 1

def b_int(bts,endian='little'):
    return int.from_bytes(bts,endian)

def int_b(i,length=2,endian='little'):
    return i.to_bytes(length,endian)

class FileReadError(Exception):
    pass

class ChecksumError(Exception):
    pass

BufferItem = namedtuple('BufferItem', ['offset', 'size', 'parse_method'], defaults=[bytes])

class PuzzleBuffer(object):

    items = [
        'file_cksum', 'magic', 'CIB_cksum', 'masked_low_cksums', 'masked_high_cksums', 
        'version', 'reserved_0x1C', 'scrambled_cksum', 'reserved_0x20',
        'width', 'height', 'n_clues', 'unknown_bitmask', 'scrambled_tag', 
        'solution', 'state', 'title', 'author', 'copyright', 'clues', 'notes', 'etc'
    ]

    file_cksum = BufferItem(0x00, 0x02, b_int)
    magic = BufferItem(0x02, 0x0C, lambda x: x.decode('ascii'))
    CIB_cksum = BufferItem(0x0E, 0x02, b_int)
    masked_low_cksums = BufferItem(0x10, 0x04, list)
    masked_high_cksums = BufferItem(0x14, 0x04, list)
    version = BufferItem(0x18, 0x04, lambda x: x.decode('ascii'))
    reserved_0x1C = BufferItem(0x1C, 0x02)
    scrambled_cksum = BufferItem(0x1E, 0x02, b_int)
    reserved_0x20 = BufferItem(0x20, 0x0C)
    width = BufferItem(0x2C, 0x01, b_int)
    height = BufferItem(0x2D, 0x01, b_int)
    n_clues = BufferItem(0x2E, 0x02, b_int)
    unknown_bitmask = BufferItem(0x30, 0x02, b_int)
    scrambled_tag = BufferItem(0x32, 0x02, b_int)

    begin_var_data = 0x34

    def __init__(self):

        self._pointer = 0x00
        self.content = b''
        self.header_garbage = b''
        self.size = 0

        self.solution = None
        self.state = None
        self.title = None
        self.author = None
        self.copyright = None
        self.clues = []
        self.notes = None
        self.etc = None

    def open(self, path):

        with open(path, 'rb') as f:
            self.content = f.read()

        self.size = len(self.content)

    def prune_garbage(self):

        start = 0x00

        while True:
            self.seek(start + 0x02)
            magic = self.read(0x0C)
            if magic == b'ACROSS&DOWN\x00':
                break
            elif magic == b'':
                raise FileReadError('Unable to buffer content - format not recognized... why are you doing this to me?')
            else:
                start += 1

        self.header_garbage = self.content[:start]
        self.content = self.content[start:]
        self.size = len(self.content)

    def load(self, path):

        self.open(path)
        self.prune_garbage()

        self.seek(self.width.offset)
        w = b_int(self.read(1))
        h = b_int(self.read(1))
        l = w*h
        n = b_int(self.read(2))

        self.solution = BufferItem(self.begin_var_data, l, lambda x: x.decode('ascii'))
        self.state = BufferItem(self.begin_var_data + l, l, lambda x: x.decode('ascii'))

        items = []
        offset = self.begin_var_data + 2*l
        self.seek(offset)

        for _ in range(n + 4):
            length = 0
            while True:
                ch = self.read(1)
                if ch == b'\x00':
                    break
                else:
                    length += 1
            bufitem = BufferItem(offset, length, lambda x: x.decode('iso-8859-1'))
            items.append(bufitem)
            offset += length + 1

        self.title = items[0]
        self.author = items[1]
        self.copyright = items[2]
        self.clues = items[3:-1]
        self.notes = items[-1]

        self.etc = BufferItem(offset, self.size - offset)

    def checksum_region(self, offset, length, initial_value=0):
        cksum = initial_value
        self.seek(offset)
        for i in range(length):
                if cksum & 1:
                        cksum = (cksum >> 1) + 0x8000
                else:
                        cksum = cksum >> 1
                cksum += b_int(self.read(1))
                cksum &= 0xFFFF
        return cksum

    def seek(self, offset, whence=0):

        if whence == 0:
            pointer = offset
        elif whence == 1:
            pointer = self._pointer + offset
        elif whence == 2:
            pointer = self.size - offset
        else:
            raise ValueError

        if pointer < 0:
            raise OSError
        else:
            self._pointer = pointer
            return self._pointer

    def read(self, n_bytes=None):

        if n_bytes is None or n_bytes < 0:
            self._pointer = self.size
            return self.content
        else:
            old_pointer = self._pointer
            self._pointer += n_bytes
            return self.content[old_pointer:self._pointer]

    def clear(self):

        self._pointer = 0x00
        self.content = b''
        self.size = 0

        self.solution = None
        self.state = None
        self.title = None
        self.author = None
        self.copyright = None
        self.clues = []
        self.notes = None
        self.etc = None

class Puzzle(object):

    low_cksum_masks = [0x49, 0x43, 0x48, 0x45]
    high_cksum_masks = [0x41, 0x54, 0x45, 0x44]

    def __init__(self, path=None, validate=True):

        self.path = path

        self.pre_garbage = None

        self.file_cksum = None
        self.magic = None
        self.CIB_cksum = None
        self.masked_low_cksums = None
        self.masked_high_cksums = None
        self.version = None
        self.reserved_0x1C = None
        self.scrambled_cksum = None
        self.reserved_0x20 = None
        self.width = None
        self.height = None
        self.n_clues = None
        self.unknown_bitmask = None
        self.scrambled_tag = None

        self.solution = []
        self.state = []

        self.title = None
        self.author = None
        self.copyright = None
        self.notes = None
        self.clues = []

        self.words = Directional(across=[], down=[])
        self.squares = []

        self.fillable = 0
        self.filled = 0
        self.checked = 0
        self.given = 0
        self.bad = 0
        self.prev_bad = 0
        self.complete = False

        self.etc = dict()
        self.rebus_dict = dict()
        self.user_rebus = None

        self.timer = Timer()
        self.buffer = PuzzleBuffer()
        self.load(validate=validate)

    def load(self, validate=True):

        self.buffer.load(self.path)
        self.parse_file()
        if validate:
            _ = self.validate()
        self._init_squares()
        self._init_words()

        if self.filled == self.fillable:
            complete = True
            for row in self.squares:
                for square in row:
                    if not square.check(silent=True):
                        complete = False
            if complete:
                self.complete = True

    def checksum_object(self, obj, initial_value=0):
        cksum = initial_value
        for byte in obj:
                if cksum & 1:
                        cksum = (cksum >> 1) + 0x8000
                else:
                        cksum = cksum >> 1
                cksum += byte
                cksum &= 0xFFFF
        return cksum

    def parse_file(self):

        buff = self.buffer

        for key in buff.items:
            if key == 'etc':
                pass
            elif key == 'clues':
                for buffer_clue in buff.clues:
                    buff.seek(buffer_clue.offset)
                    clue = buffer_clue.parse_method(buff.read(buffer_clue.size))
                    self.clues.append(clue)
            else:
                item = getattr(buff, key)
                buff.seek(item.offset)
                item_content = item.parse_method(buff.read(item.size))
                setattr(self, key, item_content)

        self.solution = [self.solution[i:i+self.width] for i in range(0,self.height*self.width,self.width)]
        self.state = [self.state[i:i+self.width] for i in range(0,self.height*self.width,self.width)]

        buff.seek(buff.etc.offset)

        while True:
        
            heading = buff.read(0x04).decode('ascii')

            if not heading:
                break
            else:
                data_length = b_int(buff.read(0x02))
                cksum = b_int(buff.read(0x02))
                data = buff.read(data_length)
                _ = buff.read(1)

                if len(data) != data_length:
                    print('ptr at: '+str(buff._pointer))
                    print('file len: '+str(len(buff.content)))
                    raise FileReadError('uh... no?')

                self.etc[heading] = {'cksum': cksum, 'data_length': data_length, 'data': data}

        if 'GRBS' in self.etc:
            assert 'RTBL' in self.etc or all(byte == 0 for byte in self.etc['GRBS']['data'])

        if 'RTBL' in self.etc:
            RTBL = self.etc['RTBL']['data'].rstrip(b';').split(b';')
            self.rebus_dict = {int(x): self._parse_special(y) for x, y in map(lambda x: x.split(b':'), RTBL)}

        if 'RUSR' in self.etc:
            self.user_rebus = self.etc['RUSR']['data'].split(b'\x00')

        if 'LTIM' in self.etc:
            elapsed, _ = self.etc['LTIM']['data'].decode('ascii').split(',')
            elapsed = int(elapsed)
            self.timer.set(elapsed)

    def get_CIB_cksum(self, init=0):
        return self.buffer.checksum_region(self.buffer.width.offset, 8, init)

    def get_solution_cksum(self, init=0):
        #return self.buffer.checksum_region(self.buffer.solution.offset, self.buffer.solution.size, init)
        solution_bytes = ''.join(self.solution).encode('ascii')
        return self.checksum_object(solution_bytes, init)

    def get_state_cksum(self, init=0):
        #return self.buffer.checksum_region(self.buffer.state.offset, self.buffer.state.size, init)
        state_bytes = ''.join(self.state).encode('ascii')
        return self.checksum_object(state_bytes, init)

    def get_partial_cksum(self, init=0):
        cksum = init
        if self.title:
            #cksum = self.buffer.checksum_region(self.buffer.title.offset, self.buffer.title.size + 1, cksum)
            cksum = self.checksum_object(self.title.encode('iso-8859-1') + b'\x00', cksum)
        if self.author:
            #cksum = self.buffer.checksum_region(self.buffer.author.offset, self.buffer.author.size + 1, cksum)
            cksum = self.checksum_object(self.author.encode('iso-8859-1') + b'\x00', cksum)
        if self.copyright:
            #cksum = self.buffer.checksum_region(self.buffer.copyright.offset, self.buffer.copyright.size + 1, cksum)
            cksum = self.checksum_object(self.copyright.encode('iso-8859-1') + b'\x00', cksum)
        for clue in self.clues:
            #cksum = self.buffer.checksum_region(clue.offset, clue.size, cksum)
            cksum = self.checksum_object(clue.encode('iso-8859-1'), cksum)
        if self.notes and (self.version >= '1.3'):
            #cksum = self.buffer.checksum_region(self.buffer.notes.offset, self.buffer.notes.size + 1, cksum)
            cksum = self.checksum_object(self.notes.encode('iso-8859-1') + b'\x00', cksum)
        return cksum

    def get_file_cksum(self, init=0):
        cksum = self.get_CIB_cksum(init)
        cksum = self.get_solution_cksum(cksum)
        cksum = self.get_state_cksum(cksum)
        cksum = self.get_partial_cksum(cksum)
        return cksum

    def validate(self, ignore=False):

        CIB_calc = self.get_CIB_cksum()
        file_cksum_calc = self.get_file_cksum()
        mask_cksums = [CIB_calc, self.get_solution_cksum(), self.get_state_cksum(), self.get_partial_cksum()]
        masked_low_calc = [ msk ^ (ck & 0xFF) for msk, ck in zip(self.low_cksum_masks, mask_cksums)]
        masked_high_calc = [ msk ^ ((ck & 0xFF00) >> 8) for msk, ck in zip(self.high_cksum_masks, mask_cksums)]

        etc_cksums = {}

        for key in self.etc:
            cksum = self.checksum_object(self.etc[key]['data'])
            etc_cksums[key] = cksum

        if not ignore:

            bad = []
            
            if CIB_calc != self.CIB_cksum:
                bad.append('bad CIB checksum')
            if file_cksum_calc != self.file_cksum:
                bad.append('bad file checksum')
            for i in range(4):
                if masked_low_calc[i] != self.masked_low_cksums[i]:
                    bad.append('bad masked checksum (low, i={})'.format(i))
                if masked_high_calc[i] != self.masked_high_cksums[i]:
                    bad.append('bad masked checksum (high, i={})'.format(i))
            for key in self.etc:
                if etc_cksums[key] != self.etc[key]['cksum']:
                    bad.append('Bad {} checksum'.format(key))

            if bad:
                raise ChecksumError(', '.join(bad))

        return file_cksum_calc, CIB_calc, masked_low_calc, masked_high_calc, etc_cksums

    #XXX TO DO: rewrite all of this, it's a mess
    def save(self, path):

        data_buffer = bytes()

        updated_state = []
        for row in self.squares:
            line = ''
            for square in row:
                if square.state is None:
                    line += '-'
                elif square.is_block:
                    line += '.'
                else:
                    line += square.state[0]
            updated_state.append(line)
        self.state = updated_state

        updated_file_cksum = self.CIB_cksum
        updated_file_cksum = self.get_solution_cksum(updated_file_cksum)
        updated_file_cksum = self.get_state_cksum(updated_file_cksum)
        updated_file_cksum = self.get_partial_cksum(updated_file_cksum)
        self.file_cksum = updated_file_cksum

        mask_cksums = [self.get_CIB_cksum(), self.get_solution_cksum(), self.get_state_cksum(), self.get_partial_cksum()]
        self.masked_low_cksums = [ msk ^ (ck & 0xFF) for msk, ck in zip(self.low_cksum_masks, mask_cksums)]
        self.masked_high_cksums = [ msk ^ ((ck & 0xFF00) >> 8) for msk, ck in zip(self.high_cksum_masks, mask_cksums)]

        # updated_state_cksum = self.checksum_object(state_bytes)
        # self.masked_low_cksums[2] = self.low_cksum_masks[2] ^ (updated_state_cksum & 0xFF)
        # self.masked_high_cksums[2] = self.high_cksum_masks[2] ^ ((updated_state_cksum & 0xFF00) >> 8)

        updated_GEXT = b''
        updated_RUSR = b''

        for row in self.squares:
            for square in row:

                shaded = int(square.is_shaded) and 0x80
                given = int(square.is_given or square.is_locked) and 0x40
                bad = int(square.is_marked_bad) and 0x20
                prev_bad = int(square.prev_marked_bad) and 0x10
                new = shaded | given | bad | prev_bad
                updated_GEXT += bytes([new])

                rebus_text = self._encode_special(square.rebus_state)
                updated_RUSR += rebus_text + b'\x00'

        updated_LTIM = '{},1'.format(self.timer.elapsed).encode('ascii')

        GEXT_cksum = self.checksum_object(updated_GEXT)
        RUSR_cksum = self.checksum_object(updated_RUSR)
        LTIM_cksum = self.checksum_object(updated_LTIM)

        if 'GEXT' in self.etc:
            assert len(updated_GEXT) == self.etc['GEXT']['data_length']

        self.etc['GEXT'] = {'data_length': len(updated_GEXT), 'cksum': GEXT_cksum, 'data': updated_GEXT}
        self.etc['RUSR'] = {'data_length': len(updated_RUSR), 'cksum': RUSR_cksum, 'data': updated_RUSR}
        self.etc['LTIM'] = {'data_length': len(updated_LTIM), 'cksum': LTIM_cksum, 'data': updated_LTIM}

        #file_cksum, CIB_cksum, masked_low_cksums, masked_high_cksums, etc_cksums = self.validate

        if self.buffer.header_garbage:
            data_buffer += self.buffer.header_garbage

        data_buffer += int_b(self.file_cksum)
        data_buffer += self.magic.encode('ascii')
        data_buffer += int_b(self.CIB_cksum)
        data_buffer += bytes(self.masked_low_cksums)
        data_buffer += bytes(self.masked_high_cksums)
        data_buffer += self.version.encode('ascii')
        data_buffer += self.reserved_0x1C
        data_buffer += int_b(self.scrambled_cksum)
        data_buffer += self.reserved_0x20
        data_buffer += bytes([self.width,self.height])
        data_buffer += int_b(self.n_clues)
        data_buffer += int_b(self.unknown_bitmask)
        data_buffer += int_b(self.scrambled_tag)

        for line in self.solution:
            data_buffer += line.encode('ascii')

        for line in self.state:
            data_buffer += line.encode('ascii')

        data_buffer += self.title.encode('iso-8859-1') + b'\x00'
        data_buffer += self.author.encode('iso-8859-1') + b'\x00'
        data_buffer += self.copyright.encode('iso-8859-1') + b'\x00'

        for clue in self.clues:
            data_buffer += clue.encode('iso-8859-1') + b'\x00'

        data_buffer += self.notes.encode('iso-8859-1') + b'\x00'

        for key in ['GRBS', 'RTBL', 'LTIM', 'GEXT', 'RUSR']:
            if not key in self.etc:
                continue
            data_buffer += key.encode('ascii')
            data_buffer += int_b(self.etc[key]['data_length'])
            data_buffer += int_b(self.etc[key]['cksum'])
            data_buffer += self.etc[key]['data']
            data_buffer += b'\x00'

        with open(os.path.expanduser(path),'wb') as f:
            f.write(data_buffer)

    def _parse_special(self,byte_string):
        if len(byte_string) == 3 and byte_string[0] == 91 and byte_string[2] == 93:
            try:
                result = chr(webding_to_unicode(byte_string[1]))
            except StopIteration:
                result = byte_string.decode('ascii')
        else:
            return byte_string.decode('ascii')

    def _encode_special(self,string):
        if not string:
            return b''
        if len(string) == 1:
            try:
                char_code = webding_to_unicode(ord(string))
                return b'[' + char_code + b']'
            except StopIteration:
                return string.encode('ascii')
        else:
            return string.encode('ascii')

    def _init_squares(self):

        for y in range(self.height):
            row = []
            for x in range(self.width):
                square = self._load_square_data(y, x)
                if square.is_given:
                    self.given += 1
                if square.is_marked_bad:
                    self.bad += 1
                if square.prev_marked_bad:
                    self.prev_bad += 1
                if square.is_given or square.is_marked_bad or square.prev_marked_bad:
                    self.checked += 1
                if not square.is_block:
                    self.fillable += 1
                    if square.state:
                        self.filled += 1
                row.append(square)
            self.squares.append(row)

        for row in self.squares:
            for square in row:
                for d in [(0,1),(0,-1),(1,0),(-1,0)]:
                    (nbr_y, nbr_x), looped = self._next_valid_neighbor(square.coords, Coord(*d))
                    square.link_neighbor(d, self.squares[nbr_y][nbr_x], looped)

    def _load_square_data(self, y, x):
        
        square = Square(y, x, self.state[y][x], self.solution[y][x])

        yx = y*self.width + x

        if 'GEXT' in self.etc:

            sq_GEXT = self.etc['GEXT']['data'][yx]

            square.is_shaded = sq_GEXT & 0x80
            square.is_given = sq_GEXT & 0x40
            square.is_marked_bad = sq_GEXT & 0x20
            square.prev_marked_bad = sq_GEXT & 0x10

        if 'GRBS' in self.etc:
            square.rebus_solution = self.rebus_dict.get(self.etc['GRBS']['data'][yx], None)

        if 'RUSR' in self.etc:
            state = self._parse_special(self.user_rebus[yx])
            square.rebus_state = state if state else None

        return square

    def _init_words(self):

        word_list = self._get_word_list()
        n = 0

        for i,(y,x,direction,word) in enumerate(word_list):

            sq = self.squares[y][x]

            if not sq.n:
                n += 1
                sq.n = n

            down = bool(direction)
            across = not down

            wd = Word(y, x, Directional(across=across,down=down), word, self.clues[i], n)
            wd.link_squares(self.squares)

            try:
                wd.prev = self.words[wd.direction][-1]
                self.words[wd.direction][-1].next =  wd
            except IndexError:
                pass

            self.words[wd.direction].append(wd)

        self.words.across[0].prev = self.words.down[-1]
        self.words.down[0].prev = self.words.across[-1]
        self.words.across[-1].next = self.words.down[0]
        self.words.down[-1].next = self.words.across[0]

    def _get_word_list(self):

        # Processes solution and return a list of tuples
        # of the form (y,x,direction,word), with direction
        # values corresponding to 0 = Across, 1 = Down

        solution_transpose = [''.join([row[i] for row in self.solution]) for i in range(self.width)]

        words = []
        for y in range(self.height):
            for m in re.finditer('[^\.]{2,}',self.solution[y]):
                    words.append((y,m.start(),ACROSS,m.group()))
        for x in range(self.width):
            for m in re.finditer('[^\.]{2,}',solution_transpose[x]):
                    words.append((m.start(),x,DOWN,m.group()))
        words.sort()
        return words

    def _next_valid_neighbor(self, start, direction):

        height, width = self.height, self.width

        old = start
        current = start + direction
        do_continue = False
        looped = False

        while True:

            if not self.is_valid_coord(*current):
                current = current + Coord(*reversed(direction))
                current = Coord(*map(lambda a, b: a % b, current, (height, width)))
                do_continue = True
            elif self.squares[current.y][current.x].is_block:
                current = current + direction
                do_continue = True

            if old == (height - 1, width - 1) and current == (0, 0):
                looped = True
            elif current == (height - 1, width - 1) and old == (0, 0):
                looped = True

            if do_continue:
                old = current
                do_continue = False
                continue
            else:
                break

        return current,looped

    def is_valid_coord(self,y,x):

        if y < 0 or x < 0:
            return False
        elif y >= self.height or x >= self.width:
            return False
        else:
            return True
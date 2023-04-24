import os
import shutil
import json
import collections.abc
import datetime
from re import search
from time import time
from indexed import IndexedOrderedDict

from cursewords.core.aware import CWAware
from cursewords.container.puzzle import Puzzle, FileReadError

class Library(CWAware):

    def __init__(self, libdir='~/.local/share/cursewords/library/', libfile='libcache.json'):

        self.last_touched = 0

        self._title_alt = lambda x:''.join([x.split('#')[0],'#{:0>3}'.format(x.split('#')[1].split(' ')[0])]+x.split('#')[1].split(' ')[1:]) if len(x.split('#'))>1 else x;
        self.title_alt = lambda x: (not self.lib[x]['title'], self._title_alt(self.lib[x]['title'].strip().lower()))

        self.sort_funcs = {
            'title': lambda x: (not self.lib[x]['title'], self.lib[x]['title'].strip()),
            'title_alt': self.title_alt,
            'author': lambda x: self.lib[x]['author'].strip(),
            'source': lambda x: (self.lib[x]['source'] is None, self.lib[x]['source']),
            'status': self._status_sort,
            'tags': lambda x: self.lib[x]['tags'],
            'import_date': lambda x: datetime.datetime.strptime(self.lib[x]['import_date'],'%Y-%m-%d %H:%M:%S')
        }

        self.sort_by = ['import_date','status','title','source']
        self.sort_reverse = {key: False for key in self.sort_funcs}
        self.sort_reverse['import_date'] = True

        self.libdir = os.path.expanduser(libdir)
        self.libcache = os.path.join(os.path.expanduser(libdir), libfile)

        try:
            with open(self.libcache, 'r') as f:
                try:
                    self.lib = json.load(f, object_pairs_hook=IndexedOrderedDict)
                except json.decoder.JSONDecodeError:
                    raise FileNotFoundError
        except FileNotFoundError:
            self.lib = IndexedOrderedDict()

        self._filter = None
        self.filtered_lib = self.lib

        self.touch()

    def touch(self): # ;)

        self.last_touched = time()
        self.resort()
        self.refilter()
        self.save_lib()

    def filter(self, refine=False, expand=False, negate=False, **kwargs):

        if not kwargs:
            self._filter = None
            self.touch()
            return

        def match(pattern):
            return lambda x: bool(search(pattern, x))

        def filter_func(item):
            for key in kwargs:
                    val = kwargs[key]
                    if isinstance(val,dict) and 'match' in val:
                        val = match(val['match'])
                    if hasattr(val, '__call__'):
                            if not val(item[key]):
                                    return False
                    else:
                            if item[key] != kwargs[key]:
                                    return False
            return True

        old_filter = self._filter
        if negate:
            new_filter = lambda x: not filter_func(x)
        else:
            new_filter = filter_func

        if refine:
            old_filter = self._filter
            self._filter = lambda x: new_filter(x) and old_filter(x)
        elif expand:
            old_filter = self._filter
            self._filter = lambda x: new_filter(x) or old_filter(x)
        else:
            self._filter = new_filter

        self.touch()

    def refilter(self):

        if self.cw.inited and self.cw.ui.inited:
            self.cw.ui.browser.interior.cursor = 0

        if self._filter is None:
            self.filtered_lib = self.lib
            return

        self.filtered_lib = IndexedOrderedDict()
        for key, val in self.lib.items():
            if self._filter(val):
                self.filtered_lib[key] = val

    # filter shortcuts for convenience
    def clear_filter(self):
        self.filter()

    def refine_filter(self, **kwargs):
        self.filter(refine=True, **kwargs)

    def expand_filter(self, **kwargs):
        self.filter(expand=True, **kwargs)

    def filter_completed(self, refine=False, expand=False, negate=False):
        self.filter(status=lambda x: x['complete'], refine=refine, expand=expand, negate=negate)

    def filter_in_progress(self, refine=False, expand=False, negate=False):
        self.filter(start_date=lambda x: x is not None, status=lambda x: not x['complete'], refine=refine, expand=expand, negate=negate)

    def filter_by_source(self, source, refine=False, expand=False, negate=False):
        self.filter(source={'match': source}, refine=refine, expand=expand, negate=negate)

    def filter_new(self, refine=False, expand=False, negate=False):
        self.filter(start_date=None, refine=refine, expand=expand, negate=negate)

    def sort(self, *keys, reverse=dict()):

        for key in keys:
            if key not in self.sort_funcs: #['title','author','source','status','tags','imported']:
                raise ValueError
        else:
            self.sort_by = keys
            for key in reverse:
                self.sort_reverse[key] = reverse[key]
            self.touch()

    def resort(self):

        for key in reversed(self.sort_by):
            # func = lambda x: self.sort_funcs[key](x)
            self.lib.sort(key=self.sort_funcs[key], reverse=self.sort_reverse[key])

    def save_lib(self):

        with open(self.libcache, 'w') as f:
            json.dump(self.lib, f)

    def import_file(self, path, source=None):

        path = os.path.expanduser(path)

        if not os.path.exists(path):
            return 1

        try:
            puz = Puzzle(path)
        except:
            return 2

        filename = os.path.basename(path)
        target = os.path.join(self.libdir, filename)

        if os.path.exists(target):
            return 3

        try:
            shutil.copy2(path, target)
        except:
            return 4

        if os.path.exists(target):

            key = target

            title = puz.title
            author = puz.author

            fillable = puz.fillable
            filled = puz.filled
            checked = puz.checked
            given = puz.given
            bad = puz.bad
            prev_bad = puz.prev_bad
            complete = puz.complete
            timer = puz.timer.elapsed

            import_date = datetime.datetime.now().isoformat(sep=' ')[:19]

            if complete:
                completion_date = import_date
            else:
                completion_date = None

            if filled != 0 or timer != 0:
                start_date = import_date
                in_progress = True
            else:
                start_date = None
                in_progress = False

            tags = []

            new_entry = {
                'path': target,
                'title': title,
                'author': author,
                'status': {
                    'fillable': fillable,
                    'filled': filled,
                    'checked': checked,
                    'given': given,
                    'bad': bad,
                    'prev_bad': prev_bad,
                    'complete': complete,
                    'timer': timer
                },
                'source': source,
                'tags': tags,
                'import_date': import_date,
                'start_date': start_date,
                'completion_date': completion_date
            }

            self.lib[key] = new_entry

            self.touch()

            return 0

        return -1

    def open_file(self, key):

        target = self[key]['path']

        try:
            puz = Puzzle(target)
            return puz
        except (KeyError, FileReadError):
            return None

    def update_status(self, puz):

        status = {
            'fillable': puz.fillable,
            'filled': puz.filled,
            'checked': puz.checked,
            'given': puz.given,
            'bad': puz.bad,
            'prev_bad': puz.prev_bad,
            'complete': puz.complete,
            'timer': puz.timer.elapsed
        }

        self[puz]['status'] = status

        self.touch()

    def tag_file(self, key, tag=None, append=False):

        if append and tag is not None:
            self[key]['tags'].append(tag)
        else:
            self[key]['tags'] = [tag] if tag is not None else []

        self.touch()

    def set_source(self, *args):

        if len(args) == 1:
            key = self.cw.this_file()['path']
            source = args[0]
        elif len(args) == 2:
            key, source = args
        else:
            raise TypeError
            
        self[key]['source'] = source
        self.touch()

    def list_items(self):
        return self.filtered_lib.values()

    def _status_sort(self,x):

        status = self.lib[x]['status']
        pct = (status['filled']*100)//status['fillable']
        timer = status['timer']
        complete = status['complete']
        in_progress = status['filled'] > 0 or timer > 0

        if complete:
            prog_key = 2
        elif in_progress:
            prog_key = 0
        else:
            prog_key = 1

        return (prog_key, pct, timer)

    def __getitem__(self, obj):

        if isinstance(obj, int):
            try:
                result = self.filtered_lib.values()[obj]
            except IndexError:
                raise KeyError
        elif isinstance(obj, str):
            result = self.lib[obj]
        elif isinstance(obj, Puzzle):
            result = self.lib[obj.path]
        else:
            raise ValueError

        return result

    # dict of files, addressable by path
    # each dict entry should contain:
    #   - path (again)?
    #   - title
    #   - author
    #   - date imported
    #   - date started
    #   - date completed
    #   - source (manually provided by user)
    #   - status:
    #       - progress (how many filled in)
    #       - completion (all filled AND all correct)
    #       - "cheating": how many checked, how many revealed
    #       - timer state
    # 
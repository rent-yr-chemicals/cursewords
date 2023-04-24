#!/usr/bin/env python3

import curses
import sys
import os
import signal

from cursewords.core.cw import CurseWords
from cursewords.core.aware import CWAware

def handleSIGHUP(signalNumber, frame):
    if cw.ui.console.history:
        cw.ui.console.save_history()
    if cw.library.lib:
        cw.library.save_lib()
    sys.exit(1)

def run(win, import_paths, import_source):
    
    MOUSEMASK = curses.ALL_MOUSE_EVENTS | curses.REPORT_MOUSE_POSITION
    curses.mousemask(MOUSEMASK)
    curses.mouseinterval(0)
    curses.curs_set(0)
    curses.halfdelay(5)

    cw = CurseWords(win=win)
    CWAware.cw_set(cw)
    cw.initialize()
    cw.ui.initialize()

    signal.signal(signal.SIGHUP, handleSIGHUP)

    if import_paths is not None:
        imported = 0
        err_list = []
        for path in import_paths:
            ret = cw.library.import_file(path, source=import_source)
            if ret == 0:
                imported += 1
            elif ret == 1:
                err_list.append((path, 'file not found'))
            elif ret == 2:
                err_list.append((path, 'could not parse file'))
            elif ret == 3:
                err_list.append((path, 'file already in library'))
            elif ret == 4:
                err_list.append((path, 'could not copy to library'))
            else:
                err_list.append((path, 'import failed - unknown error'))
        if err_list:
            err_str = ', '.join(['{} - {}'.format(os.path.basename(item_path), item_error) for item_path, item_error in err_list])
            cw.notify('Successfully imported {} of {} files; {} failed imports: {}'.format(imported, len(import_paths), len(err_list), err_str))
        else:
            cw.notify('Successfully imported {} of {} files'.format(imported, len(import_paths)))

    exit_code = 0

    try:
        cw.loop()
    except SystemExit as ex:
        exit_code = ex.code
    except KeyboardInterrupt:
        exit_code = -1
    except Exception:
        raise
    finally:
        if cw.ui.console.history:
            cw.ui.console.save_history()
        if cw.library.lib:
            cw.library.save_lib()
    
    return exit_code

def main(args):

    import_paths = None
    import_source = None

    args = args[1:]

    if args:
        if args[0] == '--source':
            try:
                import_source = args[1]
                args = args[2:]
            except IndexError:
                sys.exit(1)
        import_paths = [os.path.expanduser(arg) for arg in args]

    os.environ.setdefault('ESCDELAY', '0')
    exit = curses.wrapper(run, import_paths, import_source)
    os.system('clear')
    return exit

if __name__ == '__main__':
    
    sys.exit(main(sys.argv))
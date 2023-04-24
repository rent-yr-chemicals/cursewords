#!/usr/bin/env python3

import sys
import os
import fcntl

os.system('clear')
print('\33]0;CurseWords™\a', end='')
sys.stdout.flush()

lock_file = os.open(os.path.expanduser('~/.local/share/cursewords/process_running.lock'), os.O_WRONLY | os.O_CREAT)

try:
    fcntl.lockf(lock_file, fcntl.LOCK_EX | fcntl.LOCK_NB)
    already_running = False
except IOError:
    already_running = True

if already_running:
    print('Unable to launch - another CurseWords™ instance seems to be running')
    _ = input('Press [ENTER] to close')
    sys.exit(-1)
else:
    import cursewords
    sys.exit(cursewords.main(sys.argv))


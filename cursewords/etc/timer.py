from time import time


class Timer(object):

    def __init__(self):
        self._time_at_start = 0
        self._elapsed = 0
        self.running = False
        self.locked = False

    def lockable(func):
        def wrapped(self, *args, **kwargs):
            if self.locked:
                return
            else:
                func(self, *args, **kwargs)
        return wrapped

    def lock(self):
        self.pause()
        self.locked = True

    @lockable
    def start(self):
        self._time_at_start = int(time())
        self._elapsed = 0
        self.running = True

    @lockable
    def pause(self):
        self._elapsed = self.elapsed
        self.running = False

    @lockable
    def resume(self):
        self._time_at_start = int(time())
        self.running = True

    @lockable
    def stop(self):
        self._time_at_start = 0
        self._elapsed = 0
        self.running = False

    @lockable
    def set(self, value):
        self._time_at_start = 0
        self._elapsed = value

    @property    
    def elapsed(self):
        if not self.running:
            return self._elapsed
        else:
            return self._elapsed + int(time()) - self._time_at_start

    def fmt_time(self):
        hours, minutes = divmod(self.elapsed, 3600)
        minutes, seconds = divmod(minutes, 60)
        return '{:>2}:{:0>2}:{:0>2}'.format(int(hours), int(minutes), int(seconds))
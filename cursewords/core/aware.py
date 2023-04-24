class CWAware(object):

    @staticmethod
    def cw_set(cw):
        CWAware.cw = cw

    def __init__(self):
        pass

class ColorPaletteAware(object):

    @staticmethod
    def color_func_set(func):
        ColorPaletteAware.color = func

    def __init__(self):
        pass
def dimens_from_boundaries(y_min=0, x_min=0, y_max=1, x_max=1):

    hei = y_max - y_min
    wid = x_max - x_min

    return hei, wid, y_min, x_min
def truncate(string, space):
    if space < 1:
        raise ValueError('...um, no.')
    elif space == 1:
        result = string[:1]
    else:
        if len(string) > space:
            result = string[:space-1].rstrip() + '…'
        else:
            result = string
    return result

def trunc_and_pad(string, space, before=1, after=1):
    result = truncate(string, space)
    return ' {:<{}} '.format(result,space)

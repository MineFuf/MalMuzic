from os import path
from typing import List

def path_joins(*ps):
    if len(ps) == 0:
        return ''
    s = ps[0]
    for p in ps[1:]:
        s = path.join(s, p)
    return s
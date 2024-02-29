from toolz import pipe
from toolz.curried import map

from common.tiles import LeastPrivilegedAccesTiles, render

pipe(LeastPrivilegedAccesTiles, map(render), list)

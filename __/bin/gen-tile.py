#!/usr/bin/env python
"""
"""
import math
from os.path import join

import aspen
root = aspen.find_root()
aspen.configure(['--root', root])

from gmerc import ll2px
from gheat import check_png


for zoom in [0,1,2,3,4]:
    width, height = ll2px(-90, 180, zoom)
    numcols = int(math.ceil(width / 256.0))
    numrows = int(math.ceil(height / 256.0))
    for x in range(numcols):
        for y in range(numrows):
            fspath = join( aspen.paths.root
                         , str(zoom)
                         , "%d,%d" % (x, y)
                          ) + '.png'
            check_png(x, y, zoom, fspath)

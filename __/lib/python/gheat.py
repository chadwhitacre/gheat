import math
import os
import sqlite3
import stat
import sys
from datetime import datetime
from os.path import dirname, isfile, isdir, join

import aspen

if __name__ == '__main__':
    root = aspen.find_root()
    aspen.configure(['--root', root])

from PIL import Image, ImageChops
from aspen.handlers.static import wsgi as static_handler
from aspen.utils import translate
from httpy import Response
from gmerc import ll2px, px2ll


ZOOM_FADED = 15 # zoom level at which the map should be totally faded
COLORS = Image.open(join(aspen.paths.__, 'etc', 'colors.png')) # @@: why not gen?
colors = COLORS.load()


class Dot(object):

    def __init__(self, zoom):
        """Takes a zoom level.
        """
        dotpath = join(aspen.paths.__, 'etc', 'dots', 'dot%d.png' % zoom)
        self.dot = Image.open(dotpath)
        self.white = Image.new(self.dot.mode, self.dot.size, 'white')
        self.half_size = self.dot.size[0] / 2

DOTS = dict()
for zoom in range(31):
    DOTS[zoom] = Dot(zoom)


def isstale(fspath, n,s,e,w):
    """Given a path and three ints, return a boolean.

    calc lat/lng bounds of this tile (include half-dot-width of padding)
    SELECT count(uid) FROM points WHERE modtime < modtime_tile

    """
    if not isfile(fspath):
        return True

    modtime_png = datetime.fromtimestamp(os.stat(fspath)[stat.ST_MTIME])

    db = sqlite3.connect(join(aspen.paths.__, 'var', 'points.db'))
    db.row_factory = sqlite3.Row
    points = db.cursor()
    points = points.execute("""

        SELECT count(uid)
          FROM points
         WHERE lat <= ?
           AND lat >= ?
           AND lng <= ?
           AND lng >= ?

         AND modtime > ?

        """, (n,s,e,w, modtime_png))

    numpoints = points.fetchone()[0] # this is guaranteed to exist, right?
    return numpoints > 0


def check_png(x, y, zoom, fspath):
    """Given three ints and a png filepath, recreate the file as necessary.
    """

    DOT = DOTS[zoom]


    # Translate tile to pixel coords.
    # ===============================

    x1 = x * 256
    x2 = x1 + 255
    y1 = y * 256
    y2 = y1 + 255


    # Expand bounds by one-half dot width.
    # ====================================

    x1 = x1 - DOT.half_size
    x2 = x2 + DOT.half_size
    y1 = y1 - DOT.half_size
    y2 = y2 + DOT.half_size
    expanded_size = (x2-x1, y2-y1)


    # Translate new pixel bounds to lat/lng.
    # ======================================

    n, w = px2ll(x1, y1, zoom)
    s, e = px2ll(x2, y2, zoom)
    #print n,s,e,w


    # Create/recreate the tile if needed.
    # ===================================

    if isstale(fspath, n,s,e,w):
        #print "[re]creating", fspath


        # Start up a new tile.
        # ====================

        opacity = 256 - ((256 / ZOOM_FADED) * (zoom + 1))
        tile = Image.new('RGBA', (256, 256), 'white')#(0, 0, 0, opacity))


        # Get *all* points within lat/lng bounds.
        # =======================================

        db = sqlite3.connect(join(aspen.paths.__, 'var', 'points.db'))
        db.row_factory = sqlite3.Row
        points = db.cursor()
        points.execute("""

            SELECT *
              FROM points
             WHERE lat <= ?
               AND lat >= ?
               AND lng <= ?
               AND lng >= ?

        """, (n, s, e, w))


        # Now do heatmap thing.
        # =====================
        # multiply dots, invert, colorize, transparency

        dots = Image.new('RGB', expanded_size, 'white')
        for point in points:
        #for point in list(points)[:100]:
            x, y = ll2px(point['lat'], point['lng'], zoom)
            #print x, y
            x = x - x1 # account for tile offset relative to overall map
            y = y - y1
            #print x, y
            dot = Image.blend(DOT.dot, DOT.white, point['intensity'])
            dot_placed = Image.new('RGB', expanded_size, 'white')
            dot_placed.paste(DOT.dot, (x-DOT.half_size, y-DOT.half_size))
            dots = ImageChops.multiply(dots, dot_placed)
            #sys.stdout.write('.'); sys.stdout.flush()


        # Trim back to 256 x 256 and invert.
        # ==================================
        # Do this before performing the remaining image manipulations so we
        # don't waste time: the extra space was only for multiply.

        overlay = dots.crop(( DOT.half_size
                            , DOT.half_size
                            , 256 + DOT.half_size
                            , 256 + DOT.half_size
                             ))
        #print overlay.size
        #print
        overlay = ImageChops.invert(overlay)


        # Colorize.
        # =========
        # The 'colors' image is a 1px by 256px rainbow.

        pix = overlay.load()
        for x in range(256):
            for y in range(256):
                val = pix[x, y]
                val = colors[0, val[0]]
                pix[x, y] = val


        # Make it transparent.
        # ====================
        # Create an empty image and then paste the overlay on it with a
        # mask.

        tile = Image.new('RGBA', (256, 256), (0,0,0,0))
        mask = Image.new('RGBA', (256, 256), (255, 255, 255, opacity))
        tile.paste(overlay, None, mask)


        # Save to disk.
        # =============
        # @@: Observe thread-safety.

        dirpath = dirname(fspath)
        #print dirpath
        if not isdir(dirpath):
            #print "creating", dirpath
            os.mkdir(dirpath)
        #print "saving", fspath
        tile.save(fspath, 'PNG')


def wsgi(environ, start_response):

    path = environ['PATH_INFO']
    fspath = translate(environ['PATH_TRANSLATED'], path)

    if path.endswith('.png'):

        # Parse and validate input.
        # =========================
        # URL paths are of the form /<zoom>/<x>,<y>.png, e.g.: /3/0,1.png

        raw = path[:-4]
        try:
            assert raw.count('/') == 2, "%d /'s" % raw.count('/')
            foo, zoom, xy = raw.split('/')
            assert xy.count(',') == 1, "%d /'s" % xy.count(',')
            x, y = xy.split(',')
            assert zoom.isdigit() and x.isdigit() and y.isdigit(), "not digits"
            zoom = int(zoom)
            x = int(x)
            y = int(y)
            assert 0 <= zoom <= 30, "bad zoom: %d" % zoom
        except AssertionError, err:
            print err.args[0]
            raise Response(400, headers=[('CONTENT-TYPE','text/plain')])

        check_png(x, y, zoom, fspath)

    environ['PATH_TRANSLATED'] = fspath
    return static_handler(environ, start_response)


# Launch a thread to monitor __/var/points.db?

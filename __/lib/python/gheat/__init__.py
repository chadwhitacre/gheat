import logging
import math
import os
import sqlite3
import stat
import sys

import aspen
from aspen import ConfigurationError, restarter
from aspen.handlers.static import wsgi as static_handler
from aspen.utils import translate


# Logging config
# ==============

logging.basicConfig(level=logging.INFO) # Ack! This should be in Aspen. :^(
log = logging.getLogger('gheat')


# Configuration
# =============
# Set some things that backends will need.

SIZE = 256 # tile size, square assumed; NB: changing this breaks gmerc calls!
ZOOM_FADED = 15 # zoom level at which the map should be totally faded
COLORS_DIR = os.path.join(aspen.paths.__, 'etc', 'colors')
COLORS_NAME = aspen.conf.gheat.get('color_scheme', 'classic')
if os.sep in COLORS_NAME:
    COLORS_PATH = COLORS_NAME
else:
    COLORS_PATH = os.path.join(COLORS_DIR, COLORS_NAME+'.png')
if not os.path.isfile(COLORS_PATH):
    a = os.listdir(COLORS_DIR)
    v = [os.path.splitext(n)[0] for n in a if n.endswith('.png')]
    raise ConfigurationError( "Invalid color scheme: %s. " % COLORS_NAME
                            + "(Valid values are: %s)" % ', '.join(v)
                             )
restarter.track(COLORS_PATH)
ALWAYS_BUILD = ('true', 'yes', '1')
ALWAYS_BUILD = aspen.conf.gheat.get('always_build','').lower() in ALWAYS_BUILD
MAX_ZOOM = 31


# Database
# ========

def cursor():
    """Return a database cursor.
    """
    db = sqlite3.connect(os.path.join(aspen.paths.__, 'var', 'points.db'))
    db.row_factory = sqlite3.Row
    return db.cursor()


# Try to find an image library.
# =============================

if __name__ == '__main__':
    root = aspen.find_root()
    aspen.configure(['--root', root])

IMG_LIB = None 
IMG_LIB_PIL = False 
IMG_LIB_PYGAME = False

_want = aspen.conf.gheat.get('image_library', '').lower()
if _want not in ('pil', 'pygame', ''):
    raise ConfigurationError( "The %s image library is not supported, only PIL "
                            + "and Pygame (assuming they are installed)."
                             )

if _want:
    if _want == 'pygame':
        from gheat._pygame import Tile, Dot, colors
    elif _want == 'pil':
        from gheat._pil import Tile, Dot, colors
    IMG_LIB = _want
else:
    try:
        from gheat._pygame import Tile, Dot, colors
        IMG_LIB = 'pygame'
    except ImportError:
        try:
            from gheat._pil import Tile, Dot, colors
            IMG_LIB = 'pil'
        except ImportError:
            pass
    
    if IMG_LIB is None:
        raise ImportError("Neither Pygame nor PIL could be imported.")

IMG_LIB_PYGAME = IMG_LIB == 'pygame'
IMG_LIB_PIL = IMG_LIB == 'pil'

log.info("Using the %s library" % IMG_LIB)


# Set up dots.
# ============
# This will get lazily imported by backends.

dots = dict()
for zoom in range(MAX_ZOOM):
    dots[zoom] = Dot(zoom)


# Main WSGI callable 
# ==================

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
            start_response('400 Bad Request', [('CONTENT-TYPE','text/plain')])
            return ['Bad request.']


        # Build and save the file.
        # ========================
        # The tile that is built here will be served by the static handler.

        tile = Tile(x, y, zoom, fspath)
        if tile.isstale() or ALWAYS_BUILD:
            log.info('rebuilding %s' % path)
            tile.rebuild()


    environ['PATH_TRANSLATED'] = fspath
    return static_handler(environ, start_response)


import logging
import os
import sqlite3
import stat

import aspen
from aspen import ConfigurationError, restarter
from aspen.handlers.static import wsgi as static_handler
from aspen.utils import translate


# Logging config
# ==============

if aspen.mode.DEVDEB:
    level = logging.INFO
else:
    level = logging.WARNING
logging.basicConfig(level=level) # Ack! This should be in Aspen. :^(
log = logging.getLogger('gheat')


# Configuration
# =============
# Set some things that backends will need.

conf = aspen.conf.gheat

ALWAYS_BUILD = ('true', 'yes', '1')
ALWAYS_BUILD = conf.get('always_build', '').lower() in ALWAYS_BUILD

BUILD_EMPTIES = ('true', 'yes', '1')
BUILD_EMPTIES = conf.get('build_empties', 'true').lower() in BUILD_EMPTIES

DIRMODE = conf.get('dirmode', '0755')
try:
    DIRMODE = int(eval(DIRMODE))
except (NameError, SyntaxError, ValueError):
    raise ConfigurationError("dirmode (%s) must be an integer." % dirmode)

SIZE = 256 # size of (square) tile; NB: changing this will break gmerc calls!
MAX_ZOOM = 31 # this depends on Google API; 0 is furthest out as of recent ver.


# Opacity
# -------

OPAQUE = 255
TRANSPARENT = 0

zoom_opaque = conf.get('zoom_opaque', '-15')
try:
    zoom_opaque = int(zoom_opaque)
except ValueError:
    raise ConfigurationError("zoom_opaque must be an integer.")

zoom_transparent = conf.get('zoom_transparent', '15')
try:
    zoom_transparent = int(zoom_transparent)
except ValueError:
    raise ConfigurationError("zoom_transparent must be an integer.")

num_opacity_steps = zoom_transparent - zoom_opaque
zoom_to_opacity = dict()
if num_opacity_steps < 1:               # don't want general fade
    for zoom in range(0, MAX_ZOOM + 1):
        zoom_to_opacity[zoom] = None 
else:                                   # want general fade
    opacity_step = OPAQUE / float(num_opacity_steps) # chunk of opacity
    for zoom in range(0, MAX_ZOOM + 1):
        if zoom < zoom_opaque:
            opacity = OPAQUE 
        elif zoom > zoom_transparent:
            opacity = TRANSPARENT
        else:
            opacity = OPAQUE - (zoom * opacity_step)
        zoom_to_opacity[zoom] = int(opacity)

print zoom_to_opacity


# Database
# ========

def get_cursor():
    """Return a database cursor.
    """
    db = sqlite3.connect(os.path.join(aspen.paths.__, 'var', 'points.db'))
    db.row_factory = sqlite3.Row
    return db.cursor()


# Try to find an image library.
# =============================

IMG_LIB = None 
IMG_LIB_PIL = False 
IMG_LIB_PYGAME = False

_want = conf.get('image_library', '').lower()
if _want not in ('pil', 'pygame', ''):
    raise ConfigurationError( "The %s image library is not supported, only PIL "
                            + "and Pygame (assuming they are installed)."
                             )

if _want:
    if _want == 'pygame':
        from gheat import pygame_ as backend
    elif _want == 'pil':
        from gheat import pil_ as backend
    IMG_LIB = _want
else:
    try:
        from gheat import pygame_ as backend
        IMG_LIB = 'pygame'
    except ImportError:
        try:
            from gheat import pil_ as backend
            IMG_LIB = 'pil'
        except ImportError:
            pass
    
    if IMG_LIB is None:
        raise ImportError("Neither Pygame nor PIL could be imported.")

IMG_LIB_PYGAME = IMG_LIB == 'pygame'
IMG_LIB_PIL = IMG_LIB == 'pil'

log.info("Using the %s library" % IMG_LIB)


# Set up color schemes and dots.
# ==============================

color_schemes = dict()          # this is used below
_color_schemes_dir = os.path.join(aspen.paths.__, 'etc', 'color_schemes')
for fname in os.listdir(_color_schemes_dir):
    if not fname.endswith('.png'):
        continue
    name = os.path.splitext(fname)[0]
    fspath = os.path.join(_color_schemes_dir, fname)
    color_schemes[name] = backend.ColorScheme(name, fspath)

dots = dict()                   # this will get lazily imported by backends
for zoom in range(MAX_ZOOM):
    dots[zoom] = backend.Dot(zoom)


# Main WSGI callable 
# ==================

ROOT = aspen.paths.root

def wsgi(environ, start_response):
    path = environ['PATH_INFO']
    fspath = translate(ROOT, path)

    if path.endswith('.png'):

        # Parse and validate input.
        # =========================
        # URL paths are of the form:
        #
        #   /<color_scheme>/<zoom>/<x>,<y>.png
        #
        # E.g.:
        #
        #   /classic/3/0,1.png

        raw = path[:-4] # strip extension
        try:
            assert raw.count('/') == 3, "%d /'s" % raw.count('/')
            foo, color_scheme, zoom, xy = raw.split('/')
            assert color_scheme in color_schemes, ( "bad color_scheme: "
                                                  + color_scheme
                                                   )
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

        color_scheme = color_schemes[color_scheme]
        tile = backend.Tile(color_scheme, zoom, x, y, fspath)
        if tile.is_empty():
            log.info('serving empty tile %s' % path)
            fspath = color_scheme.get_empty_fspath(zoom)
        elif tile.is_stale() or ALWAYS_BUILD:
            log.info('rebuilding %s' % path)
            tile.rebuild()


    environ['PATH_TRANSLATED'] = fspath
    return static_handler(environ, start_response)


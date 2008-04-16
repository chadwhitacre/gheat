import logging
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

import gmerc
from aspen.handlers.static import wsgi as static_handler
from aspen.utils import translate


# Logging config
# ==============

logging.basicConfig(level=logging.INFO) # Ack! This should be in Aspen. :^(
log = logging.getLogger('gheat')


# Config
# ======
# Other config is later, after backend things are defined (should prolly move 
# to separate modules.)

SIZE = 256 # tile size, square assumed
SIZE = 32 


# Try to find an image library.
# =============================

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
        import pygame.surface
    elif _want == 'pil':
        from PIL import Image, ImageChops
    IMG_LIB = _want
else:
    try:
        import pygame.surface 
        IMG_LIB = 'pygame'
    except ImportError:
        try:
            from PIL import Image, ImageChops
            IMG_LIB = 'pil'
        except ImportError:
            pass
    
    if IMG_LIB is None:
        raise ImportError("Neither Pygame nor PIL could be imported.")

IMG_LIB_PYGAME = IMG_LIB == 'pygame'
IMG_LIB_PIL = IMG_LIB == 'pil'

log.info("Using the %s library" % IMG_LIB)


# Dots
# ====

class BaseDot(object):

    def __init__(self, zoom):
        """Takes a zoom level.
        """
        dotpath = join(aspen.paths.__, 'etc', 'dots', 'dot%d.png' % zoom)
        self.dot, self.white, self.half_size = self.variants(dotpath)


    def variants(self, dotpath):
        """Given a dotpath, return three items.
        """
        raise NotImplementedError


class PygameDot(BaseDot):
    def variants(self, dotpath):
        dot = pygame.image.load(dotpath)
        white = pygame.Surface(dot.get_size()).fill(WHITE)
        half_size = dot.get_size()[0] / 2
        return dot, white, half_size


class PILDot(BaseDot):
    def variants(self, dotpath):
        dot = Image.open(dotpath)
        white = Image.new(dot.mode, dot.size, 'white')
        half_size = dot.size[0] / 2
        return dot, white, half_size



# Tile classes
# ============

class BaseTile(object):
    """Base class for tile representations.
    """

    def __init__(self, x, y, zoom, fspath):
        """x and y are tile coords per Google Maps.
        """

        # Calculate some things.
        # ======================

        DOT = DOTS[zoom]
    
    
        # Translate tile to pixel coords.
        # -------------------------------

        x1 = x * SIZE
        x2 = x1 + 255
        y1 = y * SIZE
        y2 = y1 + 255
    
    
        # Expand bounds by one-half dot width.
        # ------------------------------------
    
        x1 = x1 - DOT.half_size
        x2 = x2 + DOT.half_size
        y1 = y1 - DOT.half_size
        y2 = y2 + DOT.half_size
        expanded_size = (x2-x1, y2-y1)
    
    
        # Translate new pixel bounds to lat/lng.
        # --------------------------------------
    
        n, w = gmerc.px2ll(x1, y1, zoom)
        s, e = gmerc.px2ll(x2, y2, zoom)


        # Save
        # ====

        self.DOT = DOT

        self.x = x
        self.y = y

        self.x1 = x1
        self.y1 = y1

        self.x2 = x2
        self.y2 = y2

        self.expanded_size = expanded_size
        self.llbound = (n,s,e,w)
        self.zoom = zoom
        self.fspath = fspath
  

    def isstale(self):
        """With attributes set on self, return a boolean.

        Calc lat/lng bounds of this tile (include half-dot-width of padding)
        SELECT count(uid) FROM points WHERE modtime < modtime_tile

        """
        if not isfile(self.fspath):
            return True
    
        modtime = datetime.fromtimestamp(os.stat(self.fspath)[stat.ST_MTIME])
    
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
    
            """, self.llbound + (modtime,))
    
        numpoints = points.fetchone()[0] # this is guaranteed to exist, right?
        return numpoints > 0


    def rebuild(self):
        """Calculate a couple common things and then handoff to a backend.
        """
        db = sqlite3.connect(join(aspen.paths.__, 'var', 'points.db'))
        db.row_factory = sqlite3.Row
        _points = db.cursor()
        _points.execute("""

            SELECT *
              FROM points
             WHERE lat <= ?
               AND lat >= ?
               AND lng <= ?
               AND lng >= ?

        """, self.llbound)

        opacity = SIZE - ((SIZE / ZOOM_FADED) * (self.zoom + 1))
   
        def points():
            """Yield x,y points within this tile.
            """
            for point in _points:
                x, y = gmerc.ll2px(point['lat'], point['lng'], self.zoom)
                x = x - self.x1 # account for tile offset relative to 
                y = y - self.y1 #  overall map
                yield x,y

        self.hook_rebuild(points(), opacity)


    def hook_rebuild(self, points, opacity):
        """Rebuild and save the file using the current library.
        """
        raise NotImplementedError


class PygameTile(BaseTile):

    def hook_rebuild(self, points, opacity):
        """Given a list of points and an opacity, save a tile.
    
        This uses the Pygame backend.
   
        Good surfarray tutorial (old but still applies):

            http://www.pygame.org/docs/tut/surfarray/SurfarrayIntro.html


        """
        
        PAD = self.DOT.half_size

        tile = pygame.Surface(self.expanded_size)#, pygame.SRCALPHA)
        tile.fill(WHITE)


        # Do heatmap thing.
        # =================
        # multiply dots, invert/colorize, transparency
    
        for x,y in points:
            dest = (x+PAD, y+PAD)
            tile.blit(self.DOT.dot, dest, None, pygame.BLEND_MULT)

   
        # Trim back to SIZE x SIZE.
        # =======================
        # Do this before performing the remaining image manipulations so we
        # don't waste time: the extra space was only for multiplying.

        tile = tile.subsurface(PAD, PAD, SIZE, SIZE).copy()
        # @@: pygame.transform.chop says this or blit; blit is prolly faster?


        # Invert and colorize.
        # ====================
        # The 'colors' image is a 1px by SIZEpx rainbow that is already inverted.

        import pdb; pdb.set_trace()
        pix = pygame.surfarray.pixels3d(tile)
#        for x in range(SIZE):
#            for y in range(SIZE):
#                val = pix[x,y,0] # grayscale, so [0] == [1] == [2]
#                val = colors[0, val]
#                pix[x,y] = [255,128,0] 
    
    
        # Make it transparent.
        # ====================
        # Create an empty image and then paste the overlay on it with a
        # mask.
    
#        tile = Image.new('RGBA', (SIZE, SIZE), (0,0,0,0))
#        mask = Image.new('RGBA', (SIZE, SIZE), (255, 255, 255, opacity))
#        tile.paste(overlay, None, mask)
    
  
        # Save.
        # =====

        dirpath = dirname(self.fspath)
        if not isdir(dirpath):
            os.mkdir(dirpath, 0755)
        pygame.image.save(tile, self.fspath)
        
 
class PILTile(BaseTile):
    """Represent a tile; use the PIL backend.
    """

    def hook_rebuild(self, points, opacity):
        """Given a list of points and an opacity, save a tile.
    
        This uses the PIL backend.
    
        """
        
        PAD = self.DOT.half_size


        # Do heatmap thing.
        # =====================
        # multiply dots, invert, colorize, transparency
    
        dots = Image.new('RGB', self.expanded_size, 'white')
        for x,y in points:
            dot_placed = Image.new('RGB', self.expanded_size, 'white')
            dot_placed.paste(self.DOT.dot, (x-PAD, y-PAD))
            dots = ImageChops.multiply(dots, dot_placed)
    
    
        # Trim back to SIZE x SIZE.
        # =======================
        # Do this before performing the remaining image manipulations so we
        # don't waste time: the extra space was only for multiplying.
    
        overlay = dots.crop((PAD, PAD, SIZE+PAD, SIZE+PAD))
        overlay = ImageChops.duplicate(overlay) # converts ImageCrop => Image


        # Colorize.
        # =========
        # The 'colors' image is a 1px by SIZEpx rainbow. Inversion is taken 
        # care of in this process, as the rainbow image is the opposite 
        # of what we really want.
    
        pix = overlay.load() # Image => PixelAccess
        for x in range(SIZE):
            for y in range(SIZE):
                pix[x,y] = colors[0, pix[x,y][0]]
    
    
        # Make it transparent.
        # ====================
        # Create an empty image and then paste the overlay on it with a
        # mask.
    
        tile = Image.new('RGBA', (SIZE, SIZE), (0,0,0,0))
        mask = Image.new('RGBA', (SIZE, SIZE), (255, 255, 255, opacity))
        tile.paste(overlay, None, mask)
    
  
        # Save.
        # =====

        dirpath = dirname(self.fspath)
        if not isdir(dirpath):
            os.mkdir(dirpath)
        tile.save(self.fspath, 'PNG')


# Configuration
# =============
# This includes some library-dependent config.
    
ZOOM_FADED = 15 # zoom level at which the map should be totally faded
COLORS_PATH = join(aspen.paths.__, 'etc', 'colors.png')
ALWAYS_BUILD = ('true', 'yes', '1')
ALWAYS_BUILD = aspen.conf.gheat.get('always_build','').lower() in ALWAYS_BUILD

if IMG_LIB_PYGAME:
    colors = pygame.surfarray.pixels3d(pygame.image.load(COLORS_PATH))
    WHITE = (255, 255, 255)
    Dot = PygameDot
    Tile = PygameTile
elif IMG_LIB_PIL:
    colors = Image.open(COLORS_PATH).load() # @@: why not gen?
    Dot = PILDot
    Tile = PILTile
else:
    raise heck # sanity check

DOTS = dict()
for zoom in range(31):
    DOTS[zoom] = Dot(zoom)


# More functions
# ==============

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


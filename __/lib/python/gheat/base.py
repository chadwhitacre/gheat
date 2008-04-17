import datetime
import os
import stat

import aspen
import gheat
import gmerc
from gheat import SIZE, ZOOM_FADED


class Dot(object):
    """Base class for dot representations.
    """

    def __init__(self, zoom):
        """Takes a zoom level.
        """
        dotname = 'dot%d.png' % zoom
        dotpath = os.path.join(aspen.paths.__, 'etc', 'dots', dotname)
        self.img, self.half_size = self.variants(dotpath)
        
    def variants(self, dotpath):
        """Given a dotpath, return three items.
        """
        raise NotImplementedError


class Tile(object):
    """Base class for tile representations.
    """

    def __init__(self, x, y, zoom, fspath):
        """x and y are tile coords per Google Maps.
        """

        # Calculate some things.
        # ======================

        from gheat import dots # lazy import to avoid circulation
        dot = dots[zoom]
    
    
        # Translate tile to pixel coords.
        # -------------------------------

        x1 = x * SIZE
        x2 = x1 + 255
        y1 = y * SIZE
        y2 = y1 + 255
    
    
        # Expand bounds by one-half dot width.
        # ------------------------------------
    
        x1 = x1 - dot.half_size
        x2 = x2 + dot.half_size
        y1 = y1 - dot.half_size
        y2 = y2 + dot.half_size
        expanded_size = (x2-x1, y2-y1)
    
    
        # Translate new pixel bounds to lat/lng.
        # --------------------------------------
    
        n, w = gmerc.px2ll(x1, y1, zoom)
        s, e = gmerc.px2ll(x2, y2, zoom)


        # Save
        # ====

        self.dot = dot.img
        self.pad = dot.half_size

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
        if not os.path.isfile(self.fspath):
            return True
   
        timestamp = os.stat(self.fspath)[stat.ST_MTIME]
        modtime = datetime.datetime.fromtimestamp(timestamp)
    
        points = gheat.cursor() 
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

        # Calculate points.
        # =================
        # Build a closure that gives us the x,y pixel coords of the points
        # to be included on this tile, relative to the top-left of the tile.

        _points = gheat.cursor()
        _points.execute("""

            SELECT *
              FROM points
             WHERE lat <= ?
               AND lat >= ?
               AND lng <= ?
               AND lng >= ?

        """, self.llbound)
   
        def points():
            """Yield x,y pixel coords within this tile.
            """
            for point in _points:
                x, y = gmerc.ll2px(point['lat'], point['lng'], self.zoom)
                x = x - self.x1 # account for tile offset relative to 
                y = y - self.y1 #  overall map
                yield x,y


        # Calculate the opacity.
        # ======================

        opacity = SIZE - ((SIZE / ZOOM_FADED) * (self.zoom + 1))


        # Main logic
        # ==========
        # Hand off to the subclass to actually build the image, then come back 
        # here to maybe create a directory before handing back to the backend
        # to actually write to disk.

        tile = self.hook_rebuild(points(), opacity)

        dirpath = os.path.dirname(self.fspath)
        if not os.path.isdir(dirpath):
            os.mkdir(dirpath, 0755)

        self.hook_save(tile)


    def hook_rebuild(self, points, opacity):
        """Rebuild and save the file using the current library.

        The algorithm runs something like this:

            o start a tile canvas/image that is a dots-worth oversized
            o loop through points and multiply dots on the tile
            o trim back down to straight tile size
            o invert/colorize the image
            o make it transparent

        Return the img object; it will be sent back to hook_save after a
        directory is made if needed.

        Trim after looping because we multiply is the only step that needs the
        extra information.

        The coloring and inverting can happen in the same pixel manipulation 
        because you can invert colors.png. That is a 1px by 256px PNG that maps
        grayscale values to color values. You can customize that file to change
        the coloration.

        """
        raise NotImplementedError


    def hook_save(self, tile):
        """Given your tile object again, write it to disk.
        """
        raise NotImplementedError



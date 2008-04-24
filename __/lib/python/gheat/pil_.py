import os

from PIL import Image, ImageChops
from gheat import SIZE, base


class ColorScheme(base.ColorScheme):
    def hook_set(self, fspath):
        self.colors = Image.open(fspath).load()


class Dot(base.Dot):
    def hook_get(self, fspath):
        img = Image.open(fspath)
        half_size = img.size[0] / 2
        return img, half_size 


class Tile(base.Tile):
    """Represent a tile; use the PIL backend.
    """

    def hook_rebuild(self, points):
        """Given a list of points and an opacity, save a tile.
    
        This uses the PIL backend.
    
        """
        tile = self._start()
        tile = self._add_points(tile, points)
        tile = self._trim(tile)
        foo  = self._colorize(tile)
        tile = self._transparentate(tile)
        return tile


    def _start(self):
        return Image.new('RGB', self.expanded_size, 'white')


    def _add_points(self, tile, points):
        for x,y in points:
            dot_placed = Image.new('RGB', self.expanded_size, 'white')
            dot_placed.paste(self.dot, (x-self.pad, y-self.pad))
            tile = ImageChops.multiply(tile, dot_placed)
        return tile
  

    def _trim(self, tile):
        tile = tile.crop((self.pad, self.pad, SIZE+self.pad, SIZE+self.pad))
        tile = ImageChops.duplicate(tile) # converts ImageCrop => Image
        return tile


    def _colorize(self, tile):
        pix = tile.load() # Image => PixelAccess
        for x in range(SIZE):
            for y in range(SIZE):
                pix[x,y] = self.color_scheme.colors[0, pix[x,y][0]]

    
    def _transparentate(self, tile):
        # Create an empty image and then paste the overlay on it with a mask.
        overlay = Image.new('RGBA', (SIZE, SIZE), (0,0,0,0))
        mask = Image.new('RGBA', (SIZE, SIZE), (255, 255, 255, self.opacity))
        tile.paste(overlay, None, mask)
        return tile


    def save(self):
        self.img.save(self.fspath, 'PNG')



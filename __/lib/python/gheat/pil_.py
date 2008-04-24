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

    def hook_rebuild(self, points, opacity):
        """Given a list of points and an opacity, save a tile.
    
        This uses the PIL backend.
    
        """
        
        # Add points 
        # ==========
   
        dots = Image.new('RGB', self.expanded_size, 'white')
        for x,y in points:
            dot_placed = Image.new('RGB', self.expanded_size, 'white')
            dot_placed.paste(self.dot, (x-self.pad, y-self.pad))
            dots = ImageChops.multiply(dots, dot_placed)
    
    
        # Trim
        # ====
    
        overlay = dots.crop((self.pad, self.pad, SIZE+self.pad, SIZE+self.pad))
        overlay = ImageChops.duplicate(overlay) # converts ImageCrop => Image


        # Invert/colorize
        # ===============
    
        pix = overlay.load() # Image => PixelAccess
        for x in range(SIZE):
            for y in range(SIZE):
                pix[x,y] = colors[0, pix[x,y][0]]
    
    
        # Transparentate
        # ==============
        # Create an empty image and then paste the overlay on it with a mask.
    
        tile = Image.new('RGBA', (SIZE, SIZE), (0,0,0,0))
        mask = Image.new('RGBA', (SIZE, SIZE), (255, 255, 255, opacity))
        tile.paste(overlay, None, mask)
    

        # Return
        # ======

        return tile


    def hook_save(self):
        self.img.save(self.fspath, 'PNG')



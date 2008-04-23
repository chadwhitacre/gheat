import os

import numpy
import pygame
from gheat import SIZE, base


WHITE = (255, 255, 255)


# Needed for colors
# =================
# 
#   http://www.pygame.org/wiki/HeadlessNoWindowsNeeded 
# 
# Beyond that, also set the color depth to 32 bits.

os.environ['SDL_VIDEODRIVER'] = 'dummy'
pygame.display.init()
pygame.display.set_mode((1,1), 0, 32)


class ColorScheme(base.ColorScheme):

    def hook_set(self, fspath):
        colors = pygame.image.load(fspath)
        self.colors = colors = colors.convert_alpha()
        self.color_map = pygame.surfarray.pixels3d(colors)[0] 
        self.alpha_map = pygame.surfarray.pixels_alpha(colors)[0]

    def hook_build_empty(self, opacity, fspath):
        tile = pygame.Surface((SIZE,SIZE), pygame.SRCALPHA, 32)
        tile.fill(self.color_map[255])
        tile.convert_alpha()
        opacity = base.compute_opacity(opacity, self.alpha_map[255])
        pygame.surfarray.pixels_alpha(tile)[:,:] = opacity 
        pygame.image.save(tile, fspath)


class Dot(base.Dot):
    def hook_get(self, fspath):
        img = pygame.image.load(fspath)
        half_size = img.get_size()[0] / 2
        return img, half_size


class Tile(base.Tile):

    def hook_rebuild(self, points):
        """Given a list of points, save a tile.
    
        This uses the Pygame backend.
   
        Good surfarray tutorial (old but still applies):

            http://www.pygame.org/docs/tut/surfarray/SurfarrayIntro.html


        """

        # Start a tile
        # ============

        tile = pygame.Surface(self.expanded_size, 0, 32)
        tile.fill(WHITE)
        #@ why do we get green after this step?
   
        
        # Add points
        # ==========

        for dest in points:
            tile.blit(self.dot, dest, None, pygame.BLEND_MULT)


        # Trim
        # ====

        tile = tile.convert_alpha(self.color_scheme.colors)
        tile = tile.subsurface(self.pad, self.pad, SIZE, SIZE).copy()
        #@ pygame.transform.chop says this or blit; blit is prolly faster?


        # Invert/colorize
        # ===============
        # The way this works is that we loop through all pixels in the image,
        # and set their color and their transparency based on an index image.
        # The index image can be as wide as we want; we only look at the first
        # column of pixels. This first column is considered a mapping of 256
        # gray-scale intensity values to color/alpha.

        tile.lock()
        #@ ... although this is the really expensive part
        pix = pygame.surfarray.pixels3d(tile)
        alp = pygame.surfarray.pixels_alpha(tile)
        for x in range(SIZE):
            for y in range(SIZE):
                key = pix[x,y,0]
                pix_alpha = self.color_scheme.alpha_map[key]
                alp[x,y] = base.compute_opacity(self.opacity, pix_alpha)
                pix[x,y] = self.color_scheme.color_map[key]
        tile.unlock()
    

        # Return
        # ======

        return tile


    def hook_save(self, tile):
        pygame.image.save(tile, self.fspath)



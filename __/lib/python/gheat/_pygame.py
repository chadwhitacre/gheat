import os

import numpy
import pygame.surface
from gheat import base, COLORS_PATH, SIZE


WHITE = (255, 255, 255)


colors = pygame.surfarray.pixels3d(pygame.image.load(COLORS_PATH))


class Dot(base.Dot):
    def variants(self, dotpath):
        img = pygame.image.load(dotpath)
        half_size = img.get_size()[0] / 2
        return img, half_size


class Tile(base.Tile):

    def hook_rebuild(self, points, opacity):
        """Given a list of points and an opacity, save a tile.
    
        This uses the Pygame backend.
   
        Good surfarray tutorial (old but still applies):

            http://www.pygame.org/docs/tut/surfarray/SurfarrayIntro.html


        """

        # Start a tile
        # ============

        tile = pygame.Surface(self.expanded_size)
        tile.fill(WHITE)
   

        # Add points
        # ==========

        for x,y in points:
            dest = (x-self.pad, y-self.pad)
            tile.blit(self.dot, dest, None, pygame.BLEND_MULT)


        # Trim
        # ====

        tile = tile.subsurface(self.pad, self.pad, SIZE, SIZE).copy()
        # @@: pygame.transform.chop says this or blit; blit is prolly faster?


        # Invert/colorize
        # ===============

        tile.lock()
        # @@: this is the expensive part, though
        pix = pygame.surfarray.pixels3d(tile)
        for x in range(SIZE):
            for y in range(SIZE):
                pix[x,y] = colors[0, pix[x,y,0]]
        tile.unlock()
    
    
        # Transparentate
        # ==============

        tile.set_alpha(opacity)
    

        # Return
        # ======

        return tile


    def hook_save(self, tile):
        pygame.image.save(tile, self.fspath)



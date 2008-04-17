#!/usr/bin/env python
"""Generate dot images.
"""
import pygame.transform

master = pygame.image.load('../etc/dots/dot30.png')
for i in range(1, 31):
    SIZE = i * 3
    scaled = pygame.transform.smoothscale(master, (SIZE, SIZE))
    pygame.image.save(scaled, "../etc/dots/dot%d.png" % (i-1,))


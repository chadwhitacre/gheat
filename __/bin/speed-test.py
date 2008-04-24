#!/usr/bin/env python
import os
import sys

import aspen; aspen.configure()
import gheat


image_library = sys.argv[1]
assert image_library in ('pygame', 'pil'), "bad image library"
if image_library == 'pygame':
    from gheat import pygame_ as backend
elif image_library == 'pil':
    from gheat import pil_ as backend

color_path = os.path.join(aspen.paths.__, 'etc', 'color_schemes', 'classic.png')
color_scheme = backend.ColorScheme('classic', color_path)
dots = gheat.load_dots(backend)
tile = backend.Tile(color_scheme, dots, 4, 4, 6, 'foo.png')
tile.rebuild()


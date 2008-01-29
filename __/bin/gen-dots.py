#!/usr/bin/env python
"""Generate dot images.
"""
from PIL import Image, ImageDraw

for i in range(1, 32):
    SIZE = i * 3
    dot = Image.new('RGBA', (SIZE, SIZE), 'white')
    draw = ImageDraw.Draw(dot)
    unit = 255 / (SIZE-1.0)
    for j in range(dot.size[0], 0, -1):
        g = gray = int(unit * (j-1))
        draw.ellipse((SIZE-j,SIZE-j,j,j), fill=(g,g,g))
    dot.save("../etc/dots/dot%d.png" % (i-1,))

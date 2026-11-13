#!/usr/bin/env python3
"""Render-time changes to project_topo.mml, measured on tiles04.

Run after restore_layers.py, since what it tunes is a restored layer.
Idempotent, as the other scripts here are.

  tune_mml.py <project_topo.mml>
"""
import re
import sys

p = sys.argv[1] if len(sys.argv) > 1 else 'topo/project_topo.mml'
s = open(p).read()

# ---- landcover-low-zoom: nothing under a tenth of a pixel -----------------
# osm-carto draws every landcover polygon over 0.01 px. On a z5 metatile that is
# 210,000 polygons, 140,000 of them between 0.01 and 0.1 px, and the layer is
# over two thirds of the render. At 0.1 px it halves (z5 11.5 s -> 5 s, z7
# 4.8 s -> 2.4 s) and 13,659 of 4.2M pixels change, one of them by more than 8
# levels. Simplifying the geometry in SQL instead was slower: the cost is the
# polygon count, not the vertices.
s, n_lc = re.subn(r'(- id: landcover-low-zoom\n(?:(?!\n  - id: ).)*?way_area > )0\.01(\*!pixel_width!)',
                  r'\g<1>0.1\2', s, flags=re.S)

open(p, 'w').write(s)
print('  landcover-low-zoom threshold 0.01 -> 0.1 px: %d' % n_lc)

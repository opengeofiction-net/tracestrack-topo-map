#!/usr/bin/env python3
"""Add the historic scripts to fonts.mss.

Upstream leaves them out because OSM does not use them in name tags. OGF does:
its conlangs are written in them, and without these faces those names render as
empty boxes. Same list the OGF CyclOSM patch adds, for the same reason.

Appended to @book-fonts, which every other list falls back to, immediately
before the Tibetan entries that close it.
"""
import sys

p = sys.argv[1] if len(sys.argv) > 1 else 'style/fonts.mss'
faces = [l.strip() for l in open(sys.argv[2]).read().splitlines() if l.strip()]
s = open(p).read()

anchor = '                "Noto Serif Tibetan Regular", "Noto Sans Tibetan Regular";'
if anchor not in s:
    print('  anchor not found - fonts.mss has changed shape'); sys.exit(1)
if faces[0].strip('"') in s:
    print('  historic scripts already present'); sys.exit(0)

block = '\n'.join('                %s,' % f for f in faces)
s = s.replace(anchor, block + '\n\n' + anchor)
open(p, 'w').write(s)
print('  fonts.mss: %d historic script faces added to @book-fonts' % len(faces))

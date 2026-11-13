#!/usr/bin/env python3
"""Make fonts.mss name faces Debian has, and add the historic scripts.

  fix_fonts_mss.py <fonts.mss> <historic-faces.txt>

Idempotent: each part checks whether it has already been done.

Faces Debian has. Upstream names Adobe's own builds, Source Sans Pro and Source
Han Sans SC, and Debian packages neither under those names. With both missing,
mapnik fell through to the third face in the list, Noto Sans Mono CJK SC: every
regular and italic label came out monospaced, and any Latin letter that font
lacks - s with comma below, esh - came out as a box, because nothing later in
the list carries Latin. So:

  * Source Sans Pro becomes Source Sans 3, its successor under a new name, from
    fonts-adobe-sourcesans3.
  * Source Han Sans SC becomes Noto Sans CJK SC, the same font under Google's
    name, from fonts-noto-cjk.
  * Noto Sans goes straight after Source Sans 3, so a letter Source Sans 3 lacks
    falls to a full Latin, Greek and Cyrillic face, not to the CJK fonts. In the
    bold list that means moving upstream's own Noto Sans Bold up one.

The historic scripts. Upstream leaves them out because OSM does not use them in
name tags. OGF does: its conlangs are written in them, and without these faces
those names render as empty boxes. Same list the OGF CyclOSM patch adds, for the
same reason. Appended to @book-fonts, which every other list falls back to,
immediately before the Tibetan entries that close it.
"""
import sys

p = sys.argv[1] if len(sys.argv) > 1 else 'style/fonts.mss'
faces = [l.strip() for l in open(sys.argv[2]).read().splitlines() if l.strip()]
s = open(p).read()

# ---- faces Debian has -----------------------------------------------------
I = '\n                '
RENAME = [
    ('"Source Sans Pro Regular",' + I + '"Source Han Sans SC Regular",',
     '"Source Sans 3 Regular",' + I + '"Noto Sans Regular",' + I + '"Noto Sans CJK SC Regular",'),
    ('"Source Sans Pro SemiBold",',
     '"Source Sans 3 Semibold",'),
    ('"Source Sans Pro Bold",' + I + '"Source Han Sans SC Bold", ' + I + '"Noto Sans Bold",',
     '"Source Sans 3 Bold",' + I + '"Noto Sans Bold",' + I + '"Noto Sans CJK SC Bold",'),
    ('"Source Sans Pro Light",',
     '"Source Sans 3 Light",'),
    ('"Source Sans Pro Italic",',
     '"Source Sans 3 Italic", "Noto Sans Italic",'),
]
n_faces = 0
for old, new in RENAME:
    if old in s:
        s = s.replace(old, new)
        n_faces += 1
print('  fonts.mss: %d face lists changed to faces Debian has' % n_faces)

# ---- historic scripts -----------------------------------------------------
anchor = '                "Noto Serif Tibetan Regular", "Noto Sans Tibetan Regular";'
if anchor not in s:
    print('  anchor not found - fonts.mss has changed shape'); sys.exit(1)
if faces[0].strip('"') in s:
    print('  historic scripts already present')
else:
    block = '\n'.join('                %s,' % f for f in faces)
    s = s.replace(anchor, block + '\n\n' + anchor)
    print('  fonts.mss: %d historic script faces added to @book-fonts' % len(faces))

open(p, 'w').write(s)

#!/usr/bin/env python3
"""Composite the hillshade for the rasters OGF actually has.

Upstream styles the three hillshade bands with grain-merge, which wants a
neutral grey raster - flat ground at 128, neither lightening nor darkening.
OGF's come from gdaldem, where flat ground is a valid mid value around 180, so
grain-merge lightens the whole of a zone's rectangle, sea included, and every
DEM footprint shows as a box on the map.

ogf/fetch-relief.sh puts them through the style's own shade.ramp first, which
makes flat ground transparent and shades only slopes. That is RGBA, and multiply
is what it wants - the same treatment CyclOSM gives the same data.

Edited in place rather than overridden from a later stylesheet: carto keeps the
first rule it sees for a selector, so a second block saying multiply is read,
parsed and ignored, whether it sits in another sheet or at the foot of this one.

The coarse bands are eased to 0.45 where they overlap the relief at z5-8;
multiplying both at 0.7 leaves the ground darker than either intends. The fine
band tapers from z12, because contours are drawn with multiply as well and a
heavy shade buries them - the same taper CyclOSM applies to this raster.
"""
import re
import sys

p = sys.argv[1] if len(sys.argv) > 1 else 'style/contours.mss'
s = open(p).read()

old = """#hillshade-5000,
#hillshade-500,
#hillshade-90 {
    raster-comp-op: grain-merge;
    raster-scaling: lanczos;
    raster-opacity: 0.7;
}"""

new = """#hillshade-5000,
#hillshade-500,
#hillshade-90 {
    raster-comp-op: multiply;
    raster-scaling: lanczos;
    raster-opacity: 0.7;
    /* Eased off as the ground fills with detail it would otherwise swamp -
     * the contours are drawn multiply too, and a heavy shade buries them.
     * Same taper CyclOSM gives this raster. */
    [zoom >= 12] { raster-opacity: 0.5; }
    [zoom >= 14] { raster-opacity: 0.4; }
    [zoom >= 16] { raster-opacity: 0.3; }
}

#hillshade-5000,
#hillshade-500 {
    raster-opacity: 0.45;
}"""

if old not in s:
    print('  the upstream hillshade block was not found - already patched?')
    sys.exit(0)

# the second block only works because carto keeps the FIRST rule per selector,
# and these two selectors are different sets - so this one is not a duplicate
s = s.replace(old, new)
open(p, 'w').write(s)
print('  contours.mss: hillshade composites with multiply, coarse bands at 0.45')

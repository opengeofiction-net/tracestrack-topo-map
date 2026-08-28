#!/usr/bin/env python3
"""Adapt Tracestrack's project_topo.mml for the OGF trial on tiles07.

Connection, and two gaps in the published snapshot which show the moment you
browse it. Everything here is ours; upstream is left alone otherwise.
"""
import re
import sys

p = sys.argv[1] if len(sys.argv) > 1 else 'topo/project_topo.mml'
VRT = '/opt/opengeofiction/dem/hillshade.vrt'
s = open(p).read()

# ---- connection -----------------------------------------------------------
# dbname, and drop the placeholder credentials. host and port go too: left in,
# host: "localhost" forces TCP and renderd fails every layer with
# "fe_sendauth: no password supplied". osm-carto and CyclOSM both omit them so
# mapnik connects over the local socket. "ser:" is a typo for "user:" upstream.
n_db = s.count('dbname: "gis"')
s = s.replace('dbname: "gis"', 'dbname: "ttopo"')
before = len(s.splitlines())
s = re.sub(r'^[ \t]*(?:user|ser|password): "YOUR(?:USERNAME|PASSWORD)"\n', '', s, flags=re.M)
s = re.sub(r'^[ \t]*host: "localhost"\n', '', s, flags=re.M)
s = re.sub(r'^[ \t]*port: "?5432"?\n', '', s, flags=re.M)
n_conn = before - len(s.splitlines())

# ---- the sea below z9 -----------------------------------------------------
# ocean-lz is minzoom 9 AND maxzoom 9, so it draws on exactly one zoom level and
# below z9 nothing draws the sea at all - land colour to the horizon. Opened
# down to z0. It reads simplified_water_polygons, which is what that is for.
s, n_ocean = re.subn(r'(- id: ocean-lz.*?properties:\n\s*minzoom: )9',
                     r'\g<1>0', s, flags=re.S)

# ---- landcover at z10 and z11 ---------------------------------------------
# landcover.mss selects "#landcover-low-zoom[zoom < 10], #landcover[zoom >= 10]",
# so with the low zoom layer restored this one wants to start at 10, not the 12
# the snapshot has - otherwise z10 and z11 fall between the two and draw nothing.
# Not lower than 10: no rule in the stylesheet fires for this layer below that,
# so the query would return 2.9 million rows for nothing.
s, n_land = re.subn(r'(- id: landcover\n.*?properties:\n\s*cache-features: true\n\s*minzoom: )12',
                    r'\g<1>10', s, flags=re.S)

# ---- hillshade ------------------------------------------------------------
# The snapshot carries a full OpenTopoMap relief and hillshade ladder, commented
# out because it ships no rasters - and contours.mss still styles every one of
# them. Uncomment the z8+ band and point it at the mosaic fetchDemData.sh
# builds - the greyscale one, not shade.vrt, because contours.mss composites these
# with grain-merge, which wants a neutral grey hillshade rather than the ramped
# RGBA CyclOSM multiplies. The lower bands want relief-500/5000 and hillshade-500/5000, which we
# publish per zone but do not currently mosaic, so they stay commented.
block = re.search(r'((?:^#  - id: hillshade-90\n)(?:^#.*\n)*)', s, flags=re.M)
n_hs = 0
if block:
    live = re.sub(r'^#', '', block.group(1), flags=re.M)
    live = live.replace('"./otm-data/hillshade-90.tif"', '"%s"' % VRT)
    live = re.sub(r'(minzoom: 8\n\s*)maxzoom: 17', r'\g<1>maxzoom: 19', live)
    s = s[:block.start(1)] + live + s[block.end(1):]
    n_hs = 1

open(p, 'w').write(s)
print('  dbname gis -> ttopo: %d anchor(s)' % n_db)
print('  connection lines removed: %d' % n_conn)
print('  ocean-lz opened to z0: %d' % n_ocean)
print('  landcover lowered to z7: %d' % n_land)
print('  hillshade-90 enabled on shade.vrt: %d' % n_hs)

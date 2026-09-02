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

# Each zoom correction below is confined to its own layer by
# "(?:(?!\n  - id: ).)*?" rather than a plain ".*?". With DOTALL a lazy .*? does
# not stop at the end of the block: run the script twice and the first pattern,
# finding its own layer already at 0, walks on to the next layer whose
# properties happen to end "minzoom: 9" and silently patches that instead. It
# reported a hit either way. Adding the label layers put a "cache-features: true
# / minzoom: 12" block after placenames-small and turned that from latent into a
# stations layer quietly moved to z10.

# ---- the sea below z9 -----------------------------------------------------
# ocean-lz is minzoom 9 AND maxzoom 9, so it draws on exactly one zoom level and
# below z9 nothing draws the sea at all - land colour to the horizon. Opened
# down to z0. It reads simplified_water_polygons, which is what that is for.
s, n_ocean = re.subn(r'(- id: ocean-lz(?:(?!\n  - id: ).)*?properties:\n\s*minzoom: )9',
                     r'\g<1>0', s, flags=re.S)

# ---- landcover at z10 and z11 ---------------------------------------------
# landcover.mss selects "#landcover-low-zoom[zoom < 10], #landcover[zoom >= 10]",
# so with the low zoom layer restored this one wants to start at 10, not the 12
# the snapshot has - otherwise z10 and z11 fall between the two and draw nothing.
# Not lower than 10: no rule in the stylesheet fires for this layer below that,
# so the query would return 2.9 million rows for nothing.
s, n_land = re.subn(r'(- id: landcover\n(?:(?!\n  - id: ).)*?properties:\n\s*cache-features: true\n\s*minzoom: )12',
                    r'\g<1>10', s, flags=re.S)

# ---- the icesheet at low zoom ---------------------------------------------
# icesheet-poly is minzoom 9, so above the poles there is nothing but sea colour
# on a world view. The layer reads the icesheet shapefile, which is generalised
# and cheap at any zoom, and shapefiles.mss styles it from z0. Opened down to 0
# for the same reason as ocean-lz.
s, n_ice = re.subn(r'(- id: icesheet-poly(?:(?!\n  - id: ).)*?properties:\n\s*minzoom: )9',
                   r'\g<1>0', s, flags=re.S)

# ---- villages and suburbs at z10 and z11 ----------------------------------
# placenames-small is minzoom 12 in the snapshot. On a topographic map z10 and
# z11 are where you are reading the shape of a region, and with nothing smaller
# than a town labelled the sheet goes quiet exactly where the terrain gets
# interesting. placenames.mss has rules for village, suburb, quarter and
# neighborhood from z11, so 12 was cutting off a zoom the stylesheet already
# draws. Lowered to 10, which is where the rules stop firing.
s, n_small = re.subn(r'(- id: placenames-small(?:(?!\n  - id: ).)*?properties:\n\s*cache-features: true\n\s*minzoom: )12',
                     r'\g<1>10', s, flags=re.S)

# ---- the label stylesheets ------------------------------------------------
# placenames.mss in the snapshot is openstreetmap-carto's file with everything
# after the variable header deleted - its first five lines are byte for byte
# osm-carto's, and the rules that followed went to labels_topo. admin.mss went
# with them entirely, which is why placenames.mss refers to
# @admin-boundaries-narrow and nothing defines it. Both files are restored from
# osm-carto v5.9.0 and declared here, admin last so boundaries draw over the
# ground.
for sheet in ('style/placenames.mss', 'style/admin.mss'):
    if sheet not in s:
        s = s.replace('  - style/contours.mss\n',
                      '  - %s\n  - style/contours.mss\n' % sheet)

# ---- relief and hillshade ------------------------------------------------
# The snapshot carries OpenTopoMap's full ladder - a different raster per zoom
# band - commented out because it ships no rasters, and contours.mss still
# styles every one of them. OGF publishes exactly that ladder per zone, so all
# five are uncommented and pointed at the mosaics ogf/fetch-relief.sh builds.
#
# The mapping is not quite name for name: their hillshade-500 covers z5-7, which
# is our hillshade-1000; their hillshade-90 is the fine band, which is the 1
# arcsecond mosaic. Greyscale rather than the ramped RGBA CyclOSM uses, because
# contours.mss composites hillshade with grain-merge, which wants neutral grey.
DEM = '/opt/opengeofiction/dem'
LADDER = {
    'relief-5000':    DEM + '/relief-5000.vrt',
    'relief-500':     DEM + '/relief-500.vrt',
    'hillshade-5000': DEM + '/hillshade-5000.vrt',
    'hillshade-500':  DEM + '/hillshade-1000.vrt',
    'hillshade-90':   DEM + '/shade.vrt',
}
n_dem = 0
for layer, path in LADDER.items():
    blk = re.search(r'((?:^#  - id: %s\n)(?:^#.*\n)*)' % re.escape(layer), s, flags=re.M)
    if not blk:
        continue
    live = re.sub(r'^#', '', blk.group(1), flags=re.M)
    live = re.sub(r'file: "[^"]*"', 'file: "%s"' % path, live)
    if layer == 'hillshade-90':
        live = re.sub(r'(minzoom: 8\n\s*)maxzoom: 17', r'\g<1>maxzoom: 19', live)
    s = s[:blk.start(1)] + live + s[blk.end(1):]
    n_dem += 1

open(p, 'w').write(s)
print('  dbname gis -> ttopo: %d anchor(s)' % n_db)
print('  connection lines removed: %d' % n_conn)
print('  ocean-lz opened to z0: %d' % n_ocean)
print('  landcover lowered to z7: %d' % n_land)
print('  icesheet-poly opened to z0: %d' % n_ice)
print('  placenames-small lowered to z10: %d' % n_small)
print('  relief and hillshade layers enabled: %d' % n_dem)

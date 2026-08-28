#!/usr/bin/env python3
"""Put back the layers Tracestrack's stylesheets style but its published
project file never defined.

The snapshot in the upstream repository is one project of at least two -
"topo_base", with "labels_topo" unpublished - and even topo_base is short of
its own stylesheets: 19 layer ids appear in style/*.mss with no Layer to match.
That is why there is no landcover below z10 (landcover.mss opens
"#landcover-low-zoom[zoom < 10], #landcover[zoom >= 10]" and only the second
layer exists), no country boundaries, no ferries, and no power lines.

Twelve of them are stock openstreetmap-carto layers, which is unsurprising
since this style is derived from it, so they are taken from osm-carto v5.9.0 -
the last release on the pgsql output this project uses - and rewritten to use
this project's own anchors. Three are not: landcover-1000 and landcover-200 are
raster layers Tracestrack renders generalised landcover into, and "natural" is
theirs; none of the three can be reconstructed from osm-carto and they are left
alone.

  restore_layers.py <project_topo.mml> <osm-carto-project.mml>
"""
import re
import sys

import yaml

# layer -> the layer it should follow in this project, or None for the head of
# the list. Taken from osm-carto's own draw order, mapped through the 33 layers
# the two projects share.
AFTER = [
    ('landcover-low-zoom',    None),
    ('landcover-line',        'landcover'),
    ('water-barriers-point',  'piers-line'),
    ('ferry-routes',          'cliffs'),
    ('turning-circle-casing', 'cliffs'),
    ('turning-circle-fill',   'roads-fill'),
    ('necountries',           'aeroways'),
    ('power-line',            'aeroways'),
    ('power-minorline',       'aeroways'),
    ('power-towers',          'amenity-line'),
    ('text-line',             'amenity-line'),
    ('text-point',            'amenity-line'),
]

# Boundaries and labels, appended in osm-carto's own relative order rather than
# slotted in. The nearest-shared-predecessor rule used above puts them far too
# early - the layers these two projects have in common are mostly the ground
# ones, so a label would end up under everything drawn after it. Labels go last.
APPEND = [
    'protected-areas',
    'admin-low-zoom', 'admin-mid-zoom', 'admin-high-zoom',
    'country-names', 'state-names', 'county-names', 'capital-names',
    'placenames-medium', 'placenames-small',
    'admin-text', 'protected-areas-text',
]


def block(layer):
    """One layer, in this project's own style: anchors rather than repeated
    connection settings, and the table as a literal block."""
    ds = layer['Datasource']
    out = ['  - id: %s' % layer['id']]
    if layer.get('geometry'):
        out.append('    geometry: %s' % layer['geometry'])
    out.append('    <<: *extents')
    out.append('    Datasource:')
    out.append('      <<: *osm2pgsql')
    table = str(ds['table']).strip()
    out.append('      table: |-')
    for line in table.splitlines():
        out.append('        %s' % line.rstrip())
    props = layer.get('properties') or {}
    if props:
        out.append('    properties:')
        for k in ('cache-features', 'minzoom', 'maxzoom'):
            if k in props:
                v = props[k]
                out.append('      %s: %s' % (k, str(v).lower() if isinstance(v, bool) else v))
    return '\n'.join(out) + '\n'


def main():
    mml_path, oc_path = sys.argv[1], sys.argv[2]
    oc = yaml.safe_load(open(oc_path))
    src = {l['id']: l for l in oc['Layer']}
    text = open(mml_path).read()

    added, skipped = [], []
    for name, after in AFTER:
        if re.search(r'^  - id: %s$' % re.escape(name), text, flags=re.M):
            skipped.append(name)
            continue
        if name not in src:
            skipped.append(name)
            continue
        new = block(src[name])
        if after is None:
            m = re.search(r'^Layer:\n', text, flags=re.M)
            text = text[:m.end()] + new + text[m.end():]
        else:
            # insert after the whole of the named layer, i.e. before the next
            # "  - id:" at the same indent
            m = re.search(r'^  - id: %s$' % re.escape(after), text, flags=re.M)
            if not m:
                skipped.append(name)
                continue
            nxt = re.search(r'^  - id: ', text[m.end():], flags=re.M)
            at = m.end() + (nxt.start() if nxt else len(text) - m.end())
            text = text[:at] + new + text[at:]
        added.append(name)

    for name in APPEND:
        if re.search(r'^  - id: %s$' % re.escape(name), text, flags=re.M):
            skipped.append(name)
            continue
        if name not in src:
            skipped.append(name)
            continue
        text = text.rstrip('\n') + '\n' + block(src[name])
        added.append(name)

    open(mml_path, 'w').write(text)
    print('  restored %d: %s' % (len(added), ', '.join(added)))
    if skipped:
        print('  skipped %d: %s' % (len(skipped), ', '.join(skipped)))


if __name__ == '__main__':
    main()

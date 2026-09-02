#!/usr/bin/env python3
"""Put back the road, water, POI and address labels.

topo_base is the half of Tracestrack's map that draws the ground. Every label
rule went to labels_topo, which is not published, and the cut is clean enough to
see: stations.mss is osm-carto's variable header with all 120 lines of rules
removed, ferry-routes.mss is osm-carto's file minus its one #ferry-routes-text
block, and water-features.mss keeps its label rules but with text-name set to ""
so they draw nothing. Eighteen more layers are simply absent from the project.

So this is the same graft placenames and admin already are - osm-carto v5.9.0's
label cartography on a Tracestrack base - and it is worth being plain that it is
not a recovery of what Tracestrack draws. Nobody outside Tracestrack has seen
labels_topo.

What makes it a graft and not a merge: the rules are appended, and the variables
they read are already here. topo_base keeps osm-carto's whole variable header in
each file, including the sizes Tracestrack scaled for a topographic sheet -
@standard-font-size is 10*1.4 here against osm-carto's 10, @landcover-wrap-width
30*2.5 against 30 - so the restored rules pick up this project's typography
rather than osm-carto's. Of the 131 variables they reference exactly one,
@private-opacity, is missing, and @address-color arrives with addressing.mss.

  restore_labels.py <project_topo.mml> <osm-carto checkout>

Idempotent: a layer already in the project, or a rule whose selector is already
in the target stylesheet, is skipped.
"""
import os
import re
import shutil
import sys

import yaml

from restore_layers import block

# Appended in osm-carto's own relative order, after the label block already
# restored. Order is priority: mapnik gives the space to whichever label is
# drawn first, so placenames and admin - already at the end of the project -
# keep winning against a street name, which is the way round it should be.
LAYERS = [
    'stations', 'bridge-text', 'amenity-points',
    'roads-text-ref-low-zoom', 'roads-text-ref', 'roads-area-text-name',
    'roads-text-name', 'paths-text-name', 'railways-text-name',
    'roads-text-ref-minor', 'text-poly-low-zoom',
    'building-text', 'interpolation', 'addresses',
    'water-lines-text', 'ferry-routes-text',
    'amenity-low-priority', 'text-low-priority',
]

# target stylesheet <- the layer ids whose rules to take from osm-carto's file of
# the same name. junctions adds no layer: the project already has one, and it is
# the motorway junction ref, so it was the third thing carto was reporting as a
# layer with no styles associated with it. text-poly-low-zoom is in two of them, sharing a selector with
# text-point: water.mss names lakes, reservoirs, basins and docks, and
# amenity-points.mss names islands. osm-carto carries both and so does this.
GRAFT = [
    ('roads.mss', ['bridge-text', 'roads-text-ref-low-zoom', 'roads-text-ref',
                   'roads-area-text-name', 'roads-text-name', 'paths-text-name',
                   'railways-text-name', 'roads-text-ref-minor', 'junctions']),
    ('water.mss', ['water-lines-text', 'text-poly-low-zoom']),
    ('stations.mss', ['stations']),
    ('amenity-points.mss', ['amenity-points', 'amenity-low-priority',
                            'text-low-priority', 'text-poly-low-zoom']),
    ('ferry-routes.mss', ['ferry-routes-text']),
]

# Whole files this project does not have. addressing.mss is house numbers and
# building names, and brings @address-color with it.
COPY = ['addressing.mss']

# Stylesheets to declare, and what each must follow. power.mss is not a label
# and is here because it is the same omission: the three power layers were
# restored, power.mss styles them, and it was never added to the list - so carto
# has been reporting "Layer power-line has no styles associated with it" and
# drawing no power at all. Both positions are osm-carto's own.
SHEETS = [('style/power.mss', 'style/roads.mss'),
          ('style/addressing.mss', 'style/admin.mss')]

# The label rules topo_base kept but silenced.
UNBLANK = ('water-features.mss', 'text-name: "";', 'text-name: "[name]";')

# Used by the grafted rules and defined in no file here.
VARS = [('amenity-points.mss', '@private-opacity: 0.33;')]

# Layers that have to move. text-line and text-point were slotted in early by
# restore_layers.py, which places a restored layer after the nearest layer the
# two projects share - and the nearest one to them is amenity-line, at 48, four
# before buildings. That was harmless while they carried only topo_base's dam,
# weir and pier labels, which were silenced anyway. It stops being harmless
# here: osm-carto's text-point is where **area** POIs get their name, so
# grafting those rules onto a layer drawn before buildings means every
# restaurant, shop and school mapped as a building is labelled and then painted
# over by the building at its 0.7 opacity. osm-carto draws all three after the
# road text and before building-text, and so should this.
MOVE = [('text-line', 'building-text'), ('text-point', 'building-text')]

# Layers whose entry zoom this map wants somewhere other than osm-carto's.
# junctions is osm-carto's from z11, which suits a road map: on a topographic
# sheet the motorway junction refs arrive long before anything they could be
# read against, and at z12 to z15 they are the loudest thing on the map. From
# z16 they land with the roads they belong to. The rules below z16 inside
# roads.mss are left as osm-carto wrote them - the layer simply does not run.
MINZOOM = [('junctions', 16)]


def rules(text):
    """Yield (selector, source text) for each top-level rule in a stylesheet.

    Selectors run over several lines - "#amenity-points,\\n#amenity-low-priority
    {" - so this walks the file at brace depth rather than matching line by
    line, skipping comments and strings so a brace inside either does not shift
    the depth.
    """
    i, n = 0, len(text)
    while i < n:
        while i < n:                                    # between rules
            if text[i] in ' \t\r\n':
                i += 1
            elif text.startswith('//', i):
                i = text.find('\n', i) + 1 or n
            elif text.startswith('/*', i):
                i = text.find('*/', i) + 2
            else:
                break
        if i >= n:
            return
        if text[i] == '@':                              # a variable, not a rule
            i = text.find(';', i) + 1 or n
            continue
        start = i
        b = text.find('{', i)
        if b < 0:
            return
        sel, depth, j = text[i:b].strip(), 0, b
        while j < n:
            if text.startswith('//', j):
                j = text.find('\n', j) + 1 or n
                continue
            if text.startswith('/*', j):
                j = text.find('*/', j) + 2
                continue
            c = text[j]
            if c in '"\'':
                j += 1
                while j < n and text[j] != c:
                    j += 2 if text[j] == '\\' else 1
                j += 1
                continue
            if c == '{':
                depth += 1
            elif c == '}':
                depth -= 1
                if depth == 0:
                    j += 1
                    break
            j += 1
        yield sel, text[start:j]
        i = j


def resolve_icons(paths, symbols, oc_symbols):
    """Point every icon reference in the grafted rules at a file that exists.

    This project keeps the same 974 symbols as osm-carto but not always under
    the same name. Some carry the intended pixel size - entrance.10.svg,
    aerodrome.12.svg, traffic_light.13.svg - and some were flattened out of
    their category directory to the top of symbols/. Mapnik does not warn about
    a missing marker file: it fails the whole layer, and renderd then fails the
    map, so every one of these has to resolve.

    A reference is matched by basename, allowing this project's size suffix. If
    nothing matches, the symbol is one osm-carto added after this snapshot was
    taken and is copied in.
    """
    have = {}
    for root, _, files in os.walk(symbols):
        for f in files:
            rel = os.path.relpath(os.path.join(root, f), symbols)
            stem = re.sub(r'\.[0-9]+(?=\.[a-z]+$)', '', f)      # entrance.10.svg -> entrance.svg
            have.setdefault(stem, os.path.join('symbols', rel))
    moved = copied = 0
    for path in paths:
        s = open(path).read()
        out = s
        for ref in sorted(set(re.findall(r"symbols/[A-Za-z0-9_./@-]+\.(?:svg|png)", s))):
            if os.path.exists(os.path.join(os.path.dirname(symbols), ref)):
                continue
            base = os.path.basename(ref)
            if base in have:
                out = out.replace(ref, have[base])
                moved += 1
            else:
                src = os.path.join(oc_symbols, ref[len('symbols/'):])
                dst = os.path.join(symbols, ref[len('symbols/'):])
                os.makedirs(os.path.dirname(dst), exist_ok=True)
                shutil.copyfile(src, dst)
                copied += 1
        if out != s:
            open(path, 'w').write(out)
    if moved or copied:
        print('  icons: %d reference(s) repointed, %d symbol(s) copied in' % (moved, copied))


def graft(dst, src, ids):
    """Append every rule in src whose selector names one of ids, unless dst has
    a rule with that selector already."""
    have = {sel for sel, _ in rules(open(dst).read())}
    take = [(sel, body) for sel, body in rules(open(src).read())
            if set(re.findall(r'#([a-z0-9_-]+)', sel)) & set(ids) and sel not in have]
    if not take:
        return 0
    with open(dst, 'a') as f:
        f.write('\n\n' + '\n\n'.join(body for _, body in take) + '\n')
    return len(take)


def main():
    mml_path, oc_root = sys.argv[1], sys.argv[2]
    style = os.path.join(os.path.dirname(os.path.abspath(mml_path)), 'style')
    oc_style = os.path.join(oc_root, 'style')

    for name in COPY:
        dst = os.path.join(style, name)
        if os.path.exists(dst):
            print('  %s already here' % name)
        else:
            shutil.copyfile(os.path.join(oc_style, name), dst)
            print('  %s copied' % name)

    for name, ids in GRAFT:
        n = graft(os.path.join(style, name), os.path.join(oc_style, name), ids)
        print('  %-22s %s' % (name, '%d rules grafted' % n if n else 'already grafted'))

    resolve_icons([os.path.join(style, n) for n, _ in GRAFT] +
                  [os.path.join(style, n) for n in COPY],
                  os.path.join(os.path.dirname(style), 'symbols'),
                  os.path.join(oc_root, 'symbols'))

    for name, decl in VARS:
        p = os.path.join(style, name)
        s = open(p).read()
        if decl.split(':')[0] + ':' not in s:
            open(p, 'w').write(decl + '\n' + s)
            print('  %-22s %s added' % (name, decl.split(':')[0]))

    name, old, new = UNBLANK
    p = os.path.join(style, name)
    s = open(p).read()
    if old in s:
        open(p, 'w').write(s.replace(old, new))
        print('  %-22s %d label(s) unsilenced' % (name, s.count(old)))

    oc = {l['id']: l for l in
          yaml.safe_load(open(os.path.join(oc_root, 'project.mml')))['Layer']}
    text = open(mml_path).read()

    def layer_block(text, name):
        m = re.search(r'^  - id: %s$' % re.escape(name), text, flags=re.M)
        if not m:
            return None, None, None
        nxt = re.search(r'^  - id: ', text[m.end():], flags=re.M)
        end = m.end() + (nxt.start() if nxt else len(text) - m.end())
        return m.start(), end, text[m.start():end]

    for name, before in MOVE:
        start, end, blk = layer_block(text, name)
        at, _, _ = layer_block(text, before)
        anchor, _, _ = layer_block(text, 'buildings')
        if blk is None or at is None or anchor is None or start > anchor:
            continue        # already out of the early slot
        text = text[:start] + text[end:]
        at, _, _ = layer_block(text, before)
        text = text[:at] + blk + text[at:]
        print('  %-22s moved to just before %s' % (name, before))

    for name, z in MINZOOM:
        m = re.search(r'^  - id: %s$.*?^      minzoom: (\d+)$' % re.escape(name),
                      text, flags=re.M | re.S)
        if m and int(m.group(1)) != z:
            text = text[:m.start(1)] + str(z) + text[m.end(1):]
            print('  %-22s minzoom %s -> %d' % (name, m.group(1), z))

    for sheet, after in SHEETS:
        if '  - %s\n' % sheet not in text:
            text = text.replace('  - %s\n' % after, '  - %s\n  - %s\n' % (after, sheet), 1)
            print('  %-22s declared after %s' % (sheet.split('/')[-1], after.split('/')[-1]))

    added, skipped = [], []
    for name in LAYERS:
        if re.search(r'^  - id: %s$' % re.escape(name), text, flags=re.M) or name not in oc:
            skipped.append(name)
            continue
        text = text.rstrip('\n') + '\n' + block(oc[name])
        added.append(name)
    open(mml_path, 'w').write(text)

    print('  restored %d layer(s): %s' % (len(added), ', '.join(added) or 'none'))
    if skipped:
        print('  skipped %d: %s' % (len(skipped), ', '.join(skipped)))


if __name__ == '__main__':
    main()

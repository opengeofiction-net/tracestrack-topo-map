# OpenGeofiction fork

Tracestrack Topo, running on OpenGeofiction's fictional planet at
[tiles07.opengeofiction.net](https://tiles07.opengeofiction.net). Upstream is
`tracestrack/tracestrack-topo-map`, kept as the `upstream` remote.

## What upstream publishes, and what it does not

The upstream README is explicit that the repository is "a detached early state
… not actively updated and may not work out of the box". It builds and renders
fine. What it is missing is layers:

* The project is **`topo_base`**, one of at least two — a commit message names
  "topo_base + labels_topo" and `taginfo/taglist.txt` declares the tags for both
  together. `labels_topo` is not published, which is why nothing labels a place
  and why `admin_level` and `boundary=administrative` appear in the taginfo
  manifest but in no layer.
* Even `topo_base` is short of its own stylesheets. **19 layer ids are styled in
  `topo/style/*.mss` with no `Layer` to match.** `landcover.mss` opens
  `#landcover-low-zoom[zoom < 10], #landcover[zoom >= 10]` and only the second
  layer exists, so there is no landcover at all below z10. `power.mss` and
  `ferry-routes.mss` style nothing whatever.

## What this fork changes

`ogf/restore_layers.py` puts back twelve of those layers, taken from
openstreetmap-carto v5.9.0 — the last release on the `pgsql` output this project
uses, and the style this one derives from — and rewritten to use this project's
own YAML anchors. Their positions come from osm-carto's own draw order, mapped
through the 33 layers the two projects share:

| restored | brings back |
| --- | --- |
| `landcover-low-zoom`, `landcover-line` | landcover below z10 |
| `necountries` | country boundaries at low zoom |
| `text-line`, `text-point`, `water-barriers-point` | water labels and barriers |
| `power-line`, `power-minorline`, `power-towers` | power infrastructure |
| `ferry-routes` | ferries |
| `turning-circle-casing`, `turning-circle-fill` | road ends |

Three of the nineteen are not reconstructable and are left alone:
`landcover-1000` and `landcover-200` are raster layers Tracestrack renders
generalised landcover into, and `natural` is theirs; none exists in osm-carto.

`ogf/patch_mml.py` makes the rest of the changes at deploy time:

* **`ocean-lz` was `minzoom: 9` and `maxzoom: 9`**, so it drew on exactly one
  zoom level and below z9 nothing drew the sea at all. Opened to z0.
* **`landcover` starts at z10**, not the 12 upstream has, matching the
  stylesheet's own `#landcover[zoom >= 10]`. Below 10 the restored low-zoom
  layer covers it.
* **The hillshade is uncommented.** The snapshot carries a full OpenTopoMap
  relief ladder — `relief-5000`, `relief-500`, `hillshade-5000`, `hillshade-500`,
  `hillshade-90` — commented out because it ships no rasters, and `contours.mss`
  still styles every one of them. The z8+ band is pointed at our own DEM.
* Database name, and the `YOURUSERNAME`/`YOURPASSWORD` placeholders. `host` and
  `port` go too: left in, `host: "localhost"` forces a TCP connection and renderd
  fails every layer with `fe_sendauth: no password supplied`.

## Notes for running it

The import is openstreetmap-carto's, not CyclOSM's, and the difference matters.
osm-carto's `openstreetmap-carto.style` promotes fewer tags to columns, so
`wetland`, `embankment`, `intermittent`, `leaf_type`, `basin`, `location`,
`parking` and `seasonal` stay in the hstore, which is where this style reads
them. Imported with CyclOSM's style those eight are columns, absent from the
hstore, and the queries silently return nothing for tens of thousands of
features.

    osm2pgsql --database ttopo --create --slim --multi-geometry --hstore \
      --tag-transform-script openstreetmap-carto.lua \
      --style openstreetmap-carto.style \
      --cache 2500 --number-processes 4 ogf-planet.osm.pbf

`ogf/external-data.yml` loads water polygons, the antarctica icesheet and the
Natural Earth boundary lines `necountries` needs — all published by the OGF
coastline process. `ogf/icesheet-column.sql` adds the `ice_edge` column: OGF's
icesheet shapefiles are valid, projected and empty, carrying only a geometry
where the real osmdata ones also carry that attribute, and the layer will not
parse without it.

`ogf/contours-view.sql` maps the OGF contours - `geometry`, `height` - onto the
`geom`, `ele` this style selects. Its own SQL already carries `WHERE ele <> 0`,
which is the same exclusion the CyclOGF style needed by patch: a contour at sea
level is the coastline, and drawing it as an index contour rings every island.

See *Admin:Elevation process* in the OGF admin wiki for where the DEM, the
contours and the shapefiles come from.

## The relief ladder

The snapshot carries OpenTopoMap's raster ladder — a different raster per zoom
band — commented out, and `contours.mss` styles every one of them:

| layer | zooms | OGF raster |
| --- | --- | --- |
| `relief-5000` | 1–4 | `relief-5000.tif` |
| `relief-500` | 5–8 | `relief-500.tif` |
| `hillshade-5000` | 1–4 | `hillshade-5000.tif` |
| `hillshade-500` | 5–7 | `hillshade-1000.tif` |
| `hillshade-90` | 8–19 | the 1 arcsecond `shade.vrt` |

`ogf/fetch-relief.sh` fetches those per zone and mosaics each band.
`fetchDemData.sh` does not - it pulls only the single 1 arcsecond mosaic CyclOSM
wants - so this runs alongside it.

Two things about compositing them, both learned the hard way:

**The hillshades need the ramp.** `gdaldem` gives flat ground a valid mid value,
around 180 rather than a neutral 128, so `grain-merge` lightens the whole of a
zone's rectangle, sea included, and every DEM footprint shows as a box on the
map. The fetch script puts them through the style's own `shade.ramp` first,
which makes flat ground transparent and shades only slopes, and `contours.mss`
is edited to composite with `multiply`. That is what CyclOSM does with the same
data. The relief rasters are already RGBA and are left alone.

**Edit the rule, do not override it.** carto keeps the *first* rule it sees for
a selector, so a later block saying `multiply` is read, parsed and silently
ignored - whether it sits in another stylesheet loaded afterwards or at the foot
of the same file. `ogf/fix_contours_mss.py` therefore edits the declaration in
place. A second block is only effective when its selector *set* differs from the
first, which is how the coarse-band opacity below works.

Opacities: the coarse bands drop to 0.45 where they overlap the relief at z5-8,
since multiplying both at 0.7 leaves the ground darker than either intends; and
the fine band tapers from z12 down to 0.3 by z16, because contours are drawn
with `multiply` too and a heavy shade buries them.

## Still missing

Labels and administrative boundaries. They live in `labels_topo`, which is not
published - `tracestrack/OpenLayers-Cartographic-Label-Style` is a client-side
OpenLayers overlay for the Carto product line, not that project. None of the 24
label and boundary layers osm-carto offers has any styling in these stylesheets,
so restoring them means importing osm-carto's label cartography as well: labels
would appear, but they would be osm-carto's labels on a Tracestrack base rather
than a recovery of what is missing.

`necountries` gives country outlines at z1-3, which is the one piece of the
boundary story the base project can carry.

## Labels and boundaries

`placenames.mss` in the snapshot is openstreetmap-carto's file with everything
after the variable header deleted — its first five lines are byte for byte
osm-carto's, and the rules that followed went to `labels_topo` with `admin.mss`
entirely. That is why the stub refers to `@admin-boundaries-narrow` and nothing
in the project defines it.

Both files are restored from osm-carto v5.9.0, along with the twelve layers they
style: `admin-low-zoom`, `admin-mid-zoom`, `admin-high-zoom`, `admin-text`,
`protected-areas`, `protected-areas-text`, `country-names`, `state-names`,
`county-names`, `capital-names`, `placenames-medium` and `placenames-small`.

They are **appended** to the layer list rather than slotted into it. The
nearest-shared-predecessor rule that places the other restored layers puts these
far too early — the layers the two projects have in common are mostly ground
ones — and a label drawn early ends up under everything after it.

This is a graft, and worth being honest about: the label cartography is
osm-carto's, on a Tracestrack base. It is not a recovery of what Tracestrack
draws. It is closer than it sounds, though, since their file was osm-carto's
until the rules were cut out of it.

`fonts.mss` gains the historic scripts, as the OGF CyclOSM patch adds them for
the same reason: upstream leaves them out because OSM does not use them in name
tags, and OGF's conlangs are written in them.

Note — `scripts/get-fonts.py` is needed here. The style asks for the Noto "UI"
variants, which Debian does not package, so Arabic and a dozen other scripts
render as empty boxes without it. v5.9.0 ships `get-fonts.sh`; take the `.py`
from v6.0.0, which is what the OGF CyclOSM servers use. Then symlink the fonts
into renderd's `font_dir`, since this style declares no `font-directory` of its
own and mapnik would otherwise never look there.

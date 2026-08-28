# OpenGeofiction fork

Tracestrack Topo, rendering OpenGeofiction's fictional planet at
[tiles07.opengeofiction.net](https://tiles07.opengeofiction.net). Upstream is
`tracestrack/tracestrack-topo-map`, kept as the `upstream` remote; everything
here is on the `ogf` branch, with `main` left as upstream's snapshot.

## What upstream publishes, and what it does not

The upstream README says the repository is "a detached early state … not
actively updated and may not work out of the box". It builds and renders
perfectly well. What it is missing is **layers**.

* The project is **`topo_base`**, one of at least two. A commit message names
  "topo_base + labels_topo" and `taginfo/taglist.txt` declares the tags for both
  together — including `admin_level` and `boundary=administrative`, which appear
  in no layer here. **`labels_topo` is not published.**
* Even `topo_base` is short of its own stylesheets. **Nineteen layer ids are
  styled in `topo/style/*.mss` with no `Layer` to match**, so the stylesheets
  describe a map the project file cannot draw. `landcover.mss` opens
  `#landcover-low-zoom[zoom < 10], #landcover[zoom >= 10]` and only the second
  layer exists, so there is no landcover below z10 at all. `power.mss` and
  `ferry-routes.mss` style nothing whatever.
* `placenames.mss` is openstreetmap-carto's file **with everything after the
  variable header deleted** — its first five lines are byte for byte osm-carto's.
  `admin.mss` went entirely. That is why the stub refers to
  `@admin-boundaries-narrow` and nothing defines it.

`tracestrack/OpenLayers-Cartographic-Label-Style` is **not** `labels_topo`: it is
a client-side OpenLayers vector overlay for the Carto product line, needing
vector tiles and an API key.

## What this fork changes

**Twenty-four layers restored**, all from openstreetmap-carto v5.9.0 — the last
release on the `pgsql` output this project uses, and the style this one derives
from — rewritten to use this project's own YAML anchors.

| restored | brings back |
| --- | --- |
| `landcover-low-zoom`, `landcover-line` | landcover below z10 |
| `necountries` | country outlines at z1–3 |
| `text-line`, `text-point`, `water-barriers-point` | water labels and barriers |
| `power-line`, `power-minorline`, `power-towers` | power infrastructure |
| `ferry-routes` | ferries |
| `turning-circle-casing`, `turning-circle-fill` | road ends |
| `admin-low-zoom`, `-mid-zoom`, `-high-zoom`, `admin-text` | administrative boundaries |
| `protected-areas`, `protected-areas-text` | protected areas |
| `country-names`, `state-names`, `county-names`, `capital-names` | |
| `placenames-medium`, `placenames-small` | place labels |

The first twelve are placed by osm-carto's own draw order, mapped through the 33
layers the two projects share. The twelve label and boundary layers are
**appended** instead: that predecessor rule puts them far too early, because the
shared layers are mostly ground ones, and a label drawn early ends up under
everything after it.

**`placenames.mss` and `admin.mss`** are restored from the same release. This is
a graft and worth saying so — the label cartography is osm-carto's on a
Tracestrack base, not a recovery of what Tracestrack draws. It is closer than it
sounds, their file having been osm-carto's until the rules were cut out.

**The relief ladder is enabled.** The snapshot carries OpenTopoMap's raster
ladder commented out, and `contours.mss` styles every layer in it. OGF publishes
exactly that ladder per zone:

| layer | zooms | OGF raster |
| --- | --- | --- |
| `relief-5000` | 1–4 | `relief-5000.tif` |
| `relief-500` | 5–8 | `relief-500.tif` |
| `hillshade-5000` | 1–4 | `hillshade-5000.tif` |
| `hillshade-500` | 5–7 | `hillshade-1000.tif` |
| `hillshade-90` | 8–19 | the 1 arcsecond `shade.vrt` |

**Three zoom-range corrections.** `ocean-lz` was `minzoom: 9` *and*
`maxzoom: 9`, drawing on exactly one zoom level with nothing drawing the sea
below z9. `landcover` starts at z10 rather than z12, matching its own selector,
with the restored low-zoom layer below that.

**`fonts.mss` gains the historic scripts**, as the OGF CyclOSM patch adds them:
upstream leaves them out because OSM does not use them in name tags, and OGF's
conlangs are written in them.

**Connection details**: database name, and the `YOURUSERNAME`/`YOURPASSWORD`
placeholders. `host` and `port` go too — left in, `host: "localhost"` forces a
TCP connection and renderd fails every layer with
`fe_sendauth: no password supplied`.

## Running it

The import is openstreetmap-carto's, **not CyclOSM's**, and the difference
matters. osm-carto's `.style` promotes fewer tags to columns, so `wetland`,
`embankment`, `intermittent`, `leaf_type`, `basin`, `location`, `parking` and
`seasonal` stay in the hstore, which is where this style reads them. Imported
with CyclOSM's style those eight are columns, absent from the hstore, and the
queries silently return nothing for tens of thousands of features.

    osm2pgsql --database ttopo --create --slim --multi-geometry --hstore \
      --tag-transform-script openstreetmap-carto.lua \
      --style openstreetmap-carto.style \
      --cache 2500 --number-processes 4 ogf-planet.osm.pbf

Then, in order:

| | |
| --- | --- |
| `ogf/patch_mml.py topo/project_topo.mml` | connection, zoom ranges, relief ladder, stylesheet list |
| `ogf/restore_layers.py topo/project_topo.mml <osm-carto project.mml>` | the 24 layers |
| `ogf/fix_contours_mss.py topo/style/contours.mss` | hillshade compositing |
| `ogf/fix_fonts_mss.py topo/style/fonts.mss ogf/historic-faces.txt` | historic scripts |
| `scripts/get-external-data.py` with `ogf/external-data.yml` | water polygons, icesheet, Natural Earth boundaries |
| `ogf/fetch-relief.sh` | the coarse relief and hillshade mosaics |
| `psql -d contours -f ogf/contours-view.sql` | maps OGF contours onto what the style selects |
| `psql -d ttopo -f ogf/icesheet-column.sql` | adds `ice_edge` to the empty icesheet table |

**Fonts are not optional.** The style asks for the Noto "UI" variants, which
Debian does not package, so Arabic and a dozen other scripts render as empty
boxes. v5.9.0 ships `scripts/get-fonts.sh`; take the `.py` from v6.0.0, which is
what the OGF CyclOSM servers use. Then symlink the result into renderd's
`font_dir` — this style declares no `font-directory`, so mapnik will not find
them otherwise.

## Things that cost time to find

**carto keeps the *first* rule it sees for a selector.** A later block saying
something different is read, parsed, compiled without complaint and silently
ignored — whether it sits in another stylesheet loaded afterwards or at the foot
of the same file. An override sheet was written, looked correct and did nothing
whatever. `ogf/fix_contours_mss.py` edits the declaration in place instead. A
second block only takes effect when its selector *set* differs from the first.

**The hillshades need the ramp.** `gdaldem` gives flat ground a valid mid value,
around 180 rather than a neutral 128, so `grain-merge` lightens the whole of a
zone's rectangle, sea included, and every DEM footprint shows as a box on the
map. `ogf/fetch-relief.sh` puts them through `shade.ramp` first, which makes
flat ground transparent and shades only slopes, and they composite with
`multiply` — what CyclOSM does with the same rasters. The relief rasters are
already RGBA and are left alone.

**Rendering through mapnik directly is not rendering through renderd.** renderd
registers fonts from `font_dir`; a script calling mapnik does not, so every
label outside the default set comes out as boxes. That looks like a broken style
and is not.

## Still missing

**Road, water and POI labels.** `roads-text-name`, `roads-text-ref`,
`water-lines-text`, `bridge-text`, `railways-text-name`, `building-text` and the
amenity labels are all still absent. Unlike placenames and admin, their rules
live inside osm-carto's `roads.mss`, `water-features.mss` and
`amenity-points.mss` — files this project already has its own versions of — so
restoring them means extracting text rules from those, not copying a file.

**Tracestrack's own label design.** What is here is osm-carto's. Recovering
theirs needs `labels_topo`, which is not published anywhere.

**`landcover-1000`, `landcover-200` and `natural`.** The first two are raster
layers Tracestrack renders generalised landcover into, and `natural` is theirs;
none exists in osm-carto and none can be reconstructed from it.

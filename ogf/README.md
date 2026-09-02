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
  * The split runs through the stylesheets too, and the cut is clean enough to
    read. `stations.mss` is osm-carto's variable header with all 120 lines of
    rules removed. `ferry-routes.mss` is osm-carto's file minus its one
    `#ferry-routes-text` block. `water-features.mss` keeps its label rules but
    sets `text-name: ""`, so dams, weirs, piers and breakwaters are named by
    rules that draw nothing. **Every label rule in the map went to
    `labels_topo`**, and eighteen more layers with it.
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

**Road, water, POI and address labels restored**, by `ogf/restore_labels.py`,
from the same release. Eighteen layers — `stations`, `amenity-points`,
`bridge-text`, the seven `roads-text-*`, `railways-text-name`, `paths-text-name`,
`water-lines-text`, `ferry-routes-text`, `building-text`, `addresses`,
`interpolation`, `text-poly-low-zoom` and the two low-priority passes — appended
in osm-carto's own relative order. Order is priority: mapnik gives contested
space to whichever label is drawn first, so placenames and admin, already at the
end of the project, keep winning against a street name.

Their rules are appended to this project's own `roads.mss`, `water.mss`,
`amenity-points.mss`, `stations.mss` and `ferry-routes.mss`, and `addressing.mss`
is copied in whole. It is a graft on the same terms as placenames — the label
cartography is osm-carto's — but it lands closer than that sounds, because
`topo_base` keeps osm-carto's whole variable header in every file, **including
the sizes Tracestrack scaled for a topographic sheet**. `@standard-font-size` is
`10*1.4` here against osm-carto's `10`, `@landcover-wrap-width-size` `30*2.5`
against `30`. The restored rules read those, so they come out at this project's
typography and not osm-carto's. Of the 131 variables they reference exactly one,
`@private-opacity`, had to be added.

**`text-line` and `text-point` move.** `restore_layers.py` had placed them at 49
and 50, four before `buildings`, because it slots a restored layer after the
nearest layer the two projects share and the nearest to those is `amenity-line`.
That was harmless while they carried only `topo_base`'s dam, weir and pier
labels, which were silenced anyway. It stops being harmless here: osm-carto's
`text-point` is **where an area POI gets its name**, so grafting those rules onto
a layer drawn before `buildings` means every restaurant, shop and school mapped
as a building is labelled and then painted over by its own building at 0.7
opacity — the name half legible, in a way that reads as a font problem rather
than an ordering one. They now sit where osm-carto puts them, after the road text
and before `building-text`.

The trade that comes with it is osm-carto's: road names are drawn first and so
win the space, and an area POI whose label a road label crosses now yields
instead of overprinting. That is the upstream priority and the reason to accept
it, but it is a real change in what gets labelled.

**`junctions` starts at z16, not osm-carto's z11.** The layer is right for a road
map at z11; on a topographic sheet the motorway junction refs arrive long before
anything they can be read against, and from z12 to z15 they are the loudest thing
on the map — a scatter of bare numbers over terrain. From z16 they land with the
roads they belong to, and z12 to z15 get the motorway names instead. The rules
inside `roads.mss` are left as osm-carto wrote them; the layer simply does not
run below z16.

`#junctions` comes with them. That layer was already in the project with nothing
styling it, so carto had been reporting it, alongside the three power layers, as
a layer with no styles associated with it. It is the motorway junction ref.

**`power.mss` is declared.** The three power layers were restored and the
stylesheet that styles them was never added to the project's list, so carto
warned and the map drew no power at all. It and `addressing.mss` both go in at
osm-carto's own positions in that list.

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

**Five zoom-range corrections.** `ocean-lz` was `minzoom: 9` *and*
`maxzoom: 9`, drawing on exactly one zoom level with nothing drawing the sea
below z9. `landcover` starts at z10 rather than z12, matching its own selector,
with the restored low-zoom layer below that. `icesheet-poly` was `minzoom: 9`,
so a world view had nothing but sea colour above the poles; the shapefile is
generalised and `shapefiles.mss` styles it from z0, so it is opened down there
for the same reason as `ocean-lz`. `placenames-small` was `minzoom: 12`, but
`placenames.mss` has rules for village, suburb, quarter and neighborhood from
z11 — so 12 was cutting off a zoom the stylesheet already draws, and on a
topographic sheet z10 and z11 are exactly where the map went quiet. Lowered to
10, where the rules stop firing.

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
| `ogf/restore_labels.py topo/project_topo.mml <osm-carto checkout>` | the 18 label layers, their rules, and the icons they need |
| `psql -d ttopo -f functions.sql` | `carto_path_type`, which `paths-text-name` selects on |
| `ogf/fix_contours_mss.py topo/style/contours.mss` | hillshade compositing |
| `ogf/fix_fonts_mss.py topo/style/fonts.mss ogf/historic-faces.txt` | historic scripts |
| `scripts/get-external-data.py` with `ogf/external-data.yml` | water polygons, icesheet, Natural Earth boundaries |
| `ogf/fetch-relief.sh` | the coarse relief and hillshade mosaics |
| `cp ogf/shade.ramp ogf/zfactor dem/` | the hillshade ramp, and which strength this style wants |
| `psql -d ttopo -f ogf/icesheet-column.sql` | adds `ice_edge` to the empty icesheet table |

**Fonts are not optional.** The style asks for the Noto "UI" variants, which
Debian does not package, so Arabic and a dozen other scripts render as empty
boxes. v5.9.0 ships `scripts/get-fonts.sh`; take the `.py` from v6.0.0, which is
what the OGF CyclOSM servers use. Then symlink the result into renderd's
`font_dir` — this style declares no `font-directory`, so mapnik will not find
them otherwise.

## Things that cost time to find

**A lazy `.*?` in `patch_mml.py` does not stop at the end of a layer.** Each
zoom correction walks from `- id: <layer>` to a `properties:` block under
`re.S`. Run the script a second time and the first pattern, finding its own
layer already patched, walks straight on to the next layer whose properties
happen to end the same way and patches *that* — reporting a hit either way, so
it looks like it worked. It was latent until the label layers put a
`cache-features: true` / `minzoom: 12` block after `placenames-small`, at which
point a re-run quietly moved `stations` to z10. Every pattern is now confined to
its own block with `(?:(?!\n  - id: ).)*?`.

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

`ogf/shade.ramp` is why the 178–182 gap in it is fully transparent: that is
where flat ground lands. Below it is black at falling alpha for shadow, above it
white at rising alpha for highlight. Both `fetch-relief.sh` and OGF-terrain-tools'
`fetchDemData.sh` read it from `dem/shade.ramp`, so it has to be copied into
place — neither creates it.

**`ogf/zfactor` picks the hillshade strength.** The published DEM carries several,
and `fetchDemData.sh` fetches `hillshade-<zfactor>.tif`. cyclogf reads the soft
`z2`; this style wants `z5`, which is why the file says so. It sits beside the
ramp rather than in the systemd unit so that a hand-run and the timer agree —
disagreeing just re-fetches every zone at the other strength, which looks like a
slow morning rather than a mistake.

**The `contour` view is not this repo's to create.** The style selects `geom` and
`ele` from a relation named `contour`, where OGF's contours arrive as `way` and
`ele` on `planet_osm_line`. `fetchDemData.sh` creates both that view and cyclogf's
`contours` after every load, because `osm2pgsql --create` replaces the table under
them. Nothing here needs to run any SQL for it.

**A missing icon is fatal, and this project renamed some.** mapnik does not warn
about a marker file it cannot open: it fails the whole layer, renderd then fails
the map, and every tile comes back an error. The symbol set here is osm-carto's
974 files, but not always under osm-carto's names — some carry the intended pixel
size, `entrance.10.svg`, `aerodrome.12.svg`, `traffic_light.13.svg`, and some
were flattened out of their category directory to the top of `symbols/`. Of the
17 icons the restored rules asked for and could not find, 13 were one of those
two and four were added to osm-carto after this snapshot. `restore_labels.py`
repoints the first kind by basename, ignoring the size suffix, and copies in the
second.

**`carto_path_type` is not in the database.** `paths-text-name` selects on it, so
without it renderd fails the whole map with `function carto_path_type(text, text)
does not exist`. It is in osm-carto's `functions.sql`, which this repo did not
carry and now does — `indexes.sql` was taken at setup and its companion was not.

**Rendering through mapnik directly is not rendering through renderd.** renderd
registers fonts from `font_dir`; a script calling mapnik does not, so every
label outside the default set comes out as boxes. That looks like a broken style
and is not.

## Still missing

**Tracestrack's own label design.** What is here is osm-carto's. Recovering
theirs needs `labels_topo`, which is not published anywhere.

**Layers that are not labels.** `aerialways`, `golf-line`, `trees`, and
`roller-coaster` with its gap fill, are all in osm-carto v5.9.0 and none is
here. They need `aerialways.mss`, `golf.mss` and `tourism.mss`, which this
project does not carry at all — so unlike the labels they are three new files
rather than rules appended to existing ones, and nothing about them was cut by
the `labels_topo` split. Left alone deliberately.

**`landcover-1000`, `landcover-200` and `natural`.** The first two are raster
layers Tracestrack renders generalised landcover into, and `natural` is theirs;
none exists in osm-carto and none can be reconstructed from it.

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

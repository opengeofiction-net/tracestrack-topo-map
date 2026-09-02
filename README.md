# Tracestrack Topo Map

This repository is for the Tracestrack Topo Map, a topographical map derived
from [openstreetmap-carto/openstreetmap-carto](https://github.com/openstreetmap-carto/openstreetmap-carto).
It is available as a featured layer on
[OpenStreetMap](https://www.openstreetmap.org/#layers=P).

> **Note:** The code in this repository is a detached early state, kept here only
> for reference. It is not actively updated and may not work out of the box.
> This repo is used mainly as an issue tracker.

**OpenGeofiction fork.** This branch renders
[OpenGeofiction](https://www.opengeofiction.net/)'s fictional planet, and puts
back the layers the stylesheets style but the project file never defined —
landcover below z10, boundaries, place labels, ferries, power, and the relief
ladder. See **[ogf/README.md](ogf/README.md)** for what was missing, what was
restored and from where, and what is still absent.

## Goals

The map aims to be avant-garde and progressive, i.e. willing to change and
support new tags. That said, a few general guidelines apply:

1. Stay close to osm-carto so users can cross-reference styles without much
   context switching.
2. Keep things general and balanced for everyday use. For example, no
   street lamps or power lines, as they are less useful and clutter the map.
3. Prioritize outdoor activities, featuring relief, hill shades, and contour
   lines.

## Issue reports

You are welcome to open issues about styling and tag support for the Topo map.


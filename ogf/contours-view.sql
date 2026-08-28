-- Tracestrack's contours layer expects a table "contour" with a "geom" column
-- and a numeric "ele". fetchDemData.sh loads the OGF contours as "contours"
-- with "geometry" and "height", the shape CyclOSM wants. This view maps one to
-- the other, so the style's own SQL is left exactly as upstream wrote it.
--
-- Their query already carries WHERE ele <> 0, which is the same exclusion we
-- had to add to cyclogf by patch: a contour at sea level is the coastline, and
-- drawing it as an index contour rings every island.
CREATE OR REPLACE VIEW contour AS
  SELECT geometry AS geom, height AS ele FROM contours;

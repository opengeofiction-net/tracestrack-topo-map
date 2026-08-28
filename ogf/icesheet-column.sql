-- OGF publishes placeholder antarctica-icesheet shapefiles: valid, projected,
-- and empty, because the planet has no mapped icesheet. They carry only a
-- geometry column, where the real osmdata ones also carry ice_edge, which
-- osm-carto lineage styles select. The layer returns no rows either way; it
-- just has to be able to parse the query.
ALTER TABLE icesheet_outlines ADD COLUMN IF NOT EXISTS ice_edge text;

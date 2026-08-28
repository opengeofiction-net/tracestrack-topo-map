#!/bin/bash
#
# Fetch the coarse relief and hillshade rasters and mosaic each band.
#
# fetchDemData.sh pulls only what CyclOSM needs - one 1 arcsecond shade mosaic -
# but the Tracestrack style carries OpenTopoMap's ladder, a different raster per
# zoom band, and styles all of them. OGF publishes exactly those per zone.
#
#   relief-5000   z1-4     relief-500    z5-8
#   hillshade-5000 z1-4    hillshade-1000 z5-7    hillshade-500 z8
#
# Run as the ogf user on the tile server.
set -u
BASE=/opt/opengeofiction/dem
RAMP=${RAMP:-/opt/opengeofiction/map-styles/ttopo/dem/shade.ramp}
SRC=https://data.opengeofiction.net/dem
ZONES=$(grep -v '^#' ${BASE}/active-zones.txt)

for band in relief-5000 relief-500 hillshade-5000 hillshade-1000 hillshade-500; do
	mkdir -p ${BASE}/${band}
	n=0
	for z in ${ZONES}; do
		out=${BASE}/${band}/${z}.tif
		# -N: only fetch when the published copy is newer, as fetchDemData does
		if wget -q -N -O ${out}.new "${SRC}/${z}/${band}.tif" 2>/dev/null && [ -s ${out}.new ]; then
			mv ${out}.new ${out}; n=$((n+1))
		else
			rm -f ${out}.new
		fi
	done
	if ! ls ${BASE}/${band}/*.tif >/dev/null 2>&1; then
		echo "  ${band}: nothing fetched"
		continue
	fi

	# The hillshades are single band grey where gdaldem gives flat ground a
	# valid mid value - about 180, not the neutral 128 - so compositing one
	# lightens the whole of a zone's rectangle, sea included, and the DEM
	# footprints show as boxes. Put them through the style's own ramp, which
	# makes flat ground transparent and shades only slopes, exactly as
	# fetchDemData.sh does for the 1 arcsecond band. The relief rasters are
	# already RGBA and are left alone.
	case ${band} in
	hillshade-*)
		mkdir -p ${BASE}/${band}-ramped
		for f in ${BASE}/${band}/*.tif; do
			out=${BASE}/${band}-ramped/$(basename ${f})
			[ -f "${out}" ] && [ "${out}" -nt "${f}" ] && continue
			gdaldem color-relief -q -alpha -co COMPRESS=DEFLATE \
				"${f}" "${RAMP}" "${out}" 2>/dev/null
		done
		gdalbuildvrt -q -overwrite ${BASE}/${band}.vrt ${BASE}/${band}-ramped/*.tif
		echo "  ${band}: ${n} zones, ramped -> ${band}.vrt"
		;;
	*)
		gdalbuildvrt -q -overwrite ${BASE}/${band}.vrt ${BASE}/${band}/*.tif
		echo "  ${band}: ${n} zones -> ${band}.vrt"
		;;
	esac
done

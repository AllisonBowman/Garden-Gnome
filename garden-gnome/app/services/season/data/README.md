# Seasonal engine data

## frost_normals.json (about 1.2 MB)

**Source.** National Oceanic and Atmospheric Administration (NOAA), National
Centers for Environmental Information, U.S. Climate Normals 1991-2020,
version 1.0.1:

- annual/seasonal normals by station:
  `https://www.ncei.noaa.gov/data/normals-annualseasonal/1991-2020/archive/us-climate-normals_1991-2020_v1.0.1_annualseasonal_multivariate_by-station_c20230404.tar.gz` (54 MB)
- daily temperature normals by variable (`dly-temp-normal.csv` only):
  `https://www.ncei.noaa.gov/data/normals-daily/1991-2020/archive/us-climate-normals_1991-2020_v1.0.1_daily_temperature_by-variable_c20230403.tar.gz` (165 MB)

Product page: https://www.ncei.noaa.gov/products/land-based-station/us-climate-normals

**Licence.** A United States government work, in the public domain; no
restriction on use. Credit is given in the app as "National Oceanic and
Atmospheric Administration (NOAA) station normals 1991 to 2020" with the
station name.

**How it was built** (2026-11-15, two archive downloads, no location sent):

    tar xzf annualseasonal.tar.gz -C ann
    tar xzf dailytemp.tar.gz -C dly dly-temp-normal.csv
    python build_frost_normals.py ann dly/dly-temp-normal.csv frost_normals.json

7,117 stations publish first and last 36, 32 and 28 F dates; all are kept.
Per station: id, name, latitude, longitude, elevation, the nine fall and nine
spring probability dates (10, 50 and 90%), the share of years each threshold
occurs at all, and dates derived from the daily normals: the normal low
falling to 55 and 50 F in fall, the normal mean falling to 45 F in fall
(woody dormancy), the normal low rising to 50 F in spring (tender plants
out), and the Spring Index stand-in below.

**Semantics.** Fall percentiles mean "on or before"; spring percentiles mean
"a later one after" (NCEI documentation). So the fall 10% date is reached in
one year in ten, the fall 90% date in nine years in ten, and one year in ten
still freezes after the spring 10% date.

**Spring Index stand-in (an estimate).** The USA National Phenology Network
Spring Index layers are GeoTIFF rasters, which this build cannot read without
adding a reader. In their place: the day the station's normal daily mean,
summed above 32 F from 1 January, reaches 470 (first leaf) or 1000 (first
bloom). These two figures are engineering defaults calibrated on two places:
Spring Index first leaf 9 March at the National Arboretum (the sum is 417
there that day) and 26 January at Austin Camp Mabry (518). The stand-in gives
14 March and 24 January; first bloom gives 12 April and 17 February (the
Spring Index reads 22 February at Austin). The app labels
these dates as our estimate.

## season_rules.json

The guidance lines for seasonal tasks and their sources, and the engineering
defaults (13.5 hours, 42 days, the leaf-drop window offsets, 45 F, 50 F, the
2 F frost setting). A line is either `cited` (a named publisher and a web
address) or `general` (it begins "General advice" and names no source it
does not have, per PLAN.md P0-12). `tests/test_season_rules.py` holds both
kinds to that.

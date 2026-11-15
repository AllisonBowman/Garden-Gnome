# Hardiness grid (`phzm2023_conus.bin`)

**What it is.** The 2023 USDA Plant Hardiness Zone Map for the contiguous
United States, as a compact grid read by `../hardiness.py`. Each cell holds
the 1991 to 2020 mean annual extreme minimum temperature, from which the
hardiness zone and half zone follow (5 °F bands starting at -60 °F: 8a is
10 to 15 °F).

**Source.** United States Department of Agriculture Agricultural Research
Service and the PRISM Climate Group (Parameter-elevation Regressions on
Independent Slopes Model), Oregon State University. File
`2023ConusNAD83_Clip.tif`, 18,253,084 bytes, from the Ag Data Commons record
"2023 USDA Plant Hardiness Zone Map Mean Annual Extreme Low Temperature
Rasters" (article 25343293, https://ndownloader.figshare.com/files/44868940),
downloaded 2026-11-15. 7025 by 3105 cells of 30 arc-seconds (about 800
metres), NAD83 degrees, values in hundredths of a degree Fahrenheit,
-32768 for no data. Alaska, Hawaii and Puerto Rico are separate rasters and
are not included yet: pins there read "Not known yet".

**Licence.** The Ag Data Commons record lists Creative Commons Attribution
4.0. PRISM's terms (https://prism.oregonstate.edu/terms) allow free
reproduction and distribution with the PRISM Group's name, its address and
the access date. The map page adds that a drawn map derived from the data
must carry the USDA Agricultural Research Service and Oregon State
University logos, and altered data must say it is not the official map. The
app never draws a zone map; it shows one value with this attribution.

**Attribution wording** (next to every hardiness zone value):

> USDA Plant Hardiness Zone Map (2023), United States Department of
> Agriculture Agricultural Research Service and the PRISM Climate Group,
> Oregon State University, prism.oregonstate.edu, accessed 15 November 2026.

**How it was built.** `build_phzm2023.py` (Pillow and numpy, build time
only): each value floored to half a degree Fahrenheit and stored as a signed
byte (-128 = no data), in 256 by 256 tiles compressed with zlib. Flooring to
0.5 °F never moves a value across a zone line, because every line is a whole
multiple of 5 °F; the distance to the nearest line is computed from the
conservative edge of that half degree. 3,412,032 bytes.

**Checks** (`tests/test_site_sources.py`): the United States National
Arboretum (38.9123, -76.9681) reads 8a (10.5 to 11 °F, so within 1 °F of the
line with 7b) and Zilker Park, Austin (30.2669, -97.7729) reads 9a (22 to
22.5 °F). Both match the official map and the published ZIP Code table
(20002 is 8a, 78746 and 78704 are 9a).

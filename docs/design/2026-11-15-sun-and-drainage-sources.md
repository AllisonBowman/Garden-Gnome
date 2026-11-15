# Sun and drainage sources (B2b, build 1.2.0)

Date 2026-11-15. Measured live only at the two public landmarks (United
States National Arboretum 38.9123, -76.9681, block `blk1_15565_-25656`; Zilker
Park 30.2669, -97.7729, block `blk1_12107_-32591`), from a laptop sandbox, a
few requests at a time, generic User-Agent. Not yet measured from Fly.

## What was tried and what worked

| Source | Result | Seconds | Bytes | Licence and attribution |
|---|---|---|---|---|
| Elevation: 3D Elevation Program dynamic service, `exportImage`, block bounds in degrees, 600 by 500 raw floats (`format=bsq`) | **Used.** Both blocks are 1 metre laser survey (Arboretum: MD VA Sandy NCR 2014; Zilker: TX Central B1 2017). Centre value matched `getSamples` within 2 cm. | 13 to 41 when cold (one retry at Zilker), 0.2 when the service's cache is warm. Several requests answered 504 after about 10 s, and the service's cache repeats a 504 for a while, so the code falls back to the block's four cells (300 by 250 each, one of which took 54 s). | 1,237,500 received; 229 to 243 KB stored (centimetres, row differences, compressed). Over the PLAN target of 80 KB. | Public domain. Credit: "Map services and data available from U.S. Geological Survey, National Geospatial Program." |
| Survey details: `getSamples` at the block's centre vertex, then catalog `query` by survey id | `getSamples` worked (2 to 4 s). The catalog query took 20 s once and otherwise timed out or answered 502, so the survey year is often missing on the first try; it is cached separately and asked again after a day. | 2 to 51 | under 1 KB | Same |
| Canopy: Meta and World Resources Institute High Resolution Canopy Height Maps v2, ranged reads of the zoom-10 tiled GeoTIFF on the Amazon Web Services open data registry | **Used.** Read with a 60-line standard-library reader plus numpy (no imaging library). Directory (first 64 KB) plus the 4 internal tiles the block touches. Heights 0 to 33 m at the Arboretum, 0 to 19 m at Zilker. | 0.5 at both | 227 to 241 KB received; 48 to 53 KB stored | Creative Commons Attribution 4.0. Attribution: "Meta and World Resources Institute". |
| First-return surface from the laser survey (trees and roofs) | Not used. Only the point clouds carry it; reading them needs the PDAL point cloud tools, outside the dependency rule. | | | Public domain |
| Building footprints with heights (Overture Maps) | Not used. Published as Parquet; reading needs a Parquet library, outside the dependency rule. Heights are sparse in suburbs anyway. | | | Open Database License (attribution for derived results) |
| Tree cover percentage from land cover (B2a's `tree_cover` reading) | The coarse fallback, used only when the canopy map fails. Open-sky hours are reduced by the tree cover share. | | | Public domain |

So the estimate counts terrain and tree canopy. **Buildings are never
counted**, so the sun estimate is always "Rough estimate" from public data and
its reason says "Buildings are not counted."

## How the numbers are made

Terrain: Horn 3 by 3 gradient over the footprint, the 10 metre pin radius left
out; one priority flood over the whole 600 by 500 window gives the filled
depression depth and the flow paths. Low spot: 10 cm deep over 4 square metres
of the footprint; flow path: runoff from 2,000 square metres or more
(engineering defaults). No water reading from elevation coarser than 3.5
metres. Sun: the National Oceanic and Atmospheric Administration solar
equations every 10 minutes on every 7th day of the frost-free period (from the
station normals, else April to October); horizons in 72 directions walked
250 metres over ground, then over ground plus canopy; up to 49 sample points
per footprint. One block on this laptop: terrain 0.3 s, sun 0.1 s; the
process grew by about 64 MB for the terrain pass (Python lists in the flood),
62.7 MB peak traced for fetch plus terrain plus sun.

## Honest limits at the landmarks

- **Arboretum, default footprint:** open sky 12.9 hours, about 7.0 with
  canopy (full sun), but the sample points range from 0 to 10.9 hours: the
  square straddles woodland edge, so the average hides real shade. A box drawn
  30 m east, under trees, reads 0.3 hours (shade). The survey is from 2014.
- **Zilker, default footprint:** open sky 12.6, 11.9 with canopy (full sun);
  no canopy over the square. Near-flat (2.1 degrees), so no facing direction.
- **Everywhere:** buildings and roofs are not counted; canopy heights are a
  machine-learning estimate from satellite images of uncertain date (version 1
  reported a 2.8 m typical error); a point under a crown counts as fully shaded
  while leaves are out, which overstates shade under thin or high canopy;
  hills farther than about 125 to 375 m (outside the block) are not counted;
  sun is geometric (no refraction, no clouds), so it is the hours the sun could
  reach the spot, not the sunshine it will get.

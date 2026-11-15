Recorded 2026-11-15 from the two public landmarks only (build spec section 2).

- `*_crop.npz`: 200 by 200 pixels (0.00001 degree lattice) around each landmark,
  cut from the block windows read live: `z_cm` ground height in centimetres from the
  United States Geological Survey 3D Elevation Program (public domain), `chm_m` tree
  canopy height in metres from the Meta and World Resources Institute High Resolution
  Canopy Height Maps version 2 (Creative Commons Attribution 4.0), `bounds` west,
  south, east, north in degrees.
- `*_getsamples.json`, `catalog_query.json`: the elevation service's answers about
  which survey it used at each block's centre vertex.

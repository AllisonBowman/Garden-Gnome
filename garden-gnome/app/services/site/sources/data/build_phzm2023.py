"""Build phzm2023_conus.bin from the official 2023 hardiness raster.

Run once by hand (build time only; the server never runs this):

    .venv/bin/python -m app.services.site.sources.data.build_phzm2023 \
        /path/to/2023ConusNAD83_Clip.tif

Input: the 2023 USDA Plant Hardiness Zone Map raster for the contiguous
United States, "2023ConusNAD83_Clip.tif" (18,253,084 bytes) from the
Ag Data Commons record 25343293 (https://ndownloader.figshare.com/files/44868940).
It is a 7025 by 3105 grid of 30 arc-second cells in NAD83 degrees, holding
the 1991 to 2020 mean annual extreme minimum temperature in hundredths of a
degree Fahrenheit, with -32768 for no data.

Output: each value floored to half a degree Fahrenheit and stored as a signed
byte (-128 = no data), cut into 256 by 256 tiles compressed with zlib, so a
lookup decompresses one tile. Flooring to 0.5 °F never moves a value across a
zone line, because every zone line is a whole multiple of 5 °F. Needs Pillow
and numpy at build time only.
"""
from __future__ import annotations

import json
import struct
import sys
import zlib
from pathlib import Path

import numpy as np

TILE = 256
NODATA = -128
OUT = Path(__file__).with_name("phzm2023_conus.bin")
MAGIC = b"PHZM2023"


def build(tif: Path, out: Path = OUT) -> dict:
    from PIL import Image  # build-time only

    Image.MAX_IMAGE_PIXELS = None
    im = Image.open(tif)
    tags = im.tag_v2
    scale = tags[33550]
    tie = tags[33922]
    raw = np.array(im).astype(np.int32)
    nodata = raw == -32768
    q = np.where(nodata, NODATA, np.floor(raw / 50.0)).astype(np.int8)
    rows, cols = q.shape
    header = {
        "source": "USDA Plant Hardiness Zone Map 2023, 2023ConusNAD83_Clip.tif",
        "crs": "NAD83 geographic degrees (EPSG:4269)",
        "west": float(tie[3]), "north": float(tie[4]),
        "cell_deg": float(scale[0]),
        "rows": rows, "cols": cols, "tile": TILE,
        "units": "half degrees Fahrenheit, floored", "nodata": NODATA,
    }
    tiles = []
    for r0 in range(0, rows, TILE):
        for c0 in range(0, cols, TILE):
            tiles.append(zlib.compress(q[r0:r0 + TILE, c0:c0 + TILE].tobytes(), 9))
    head = json.dumps(header, sort_keys=True).encode()
    offsets = []
    pos = 0
    for t in tiles:
        offsets.append(pos)
        pos += len(t)
    with open(out, "wb") as f:
        f.write(MAGIC)
        f.write(struct.pack("<II", len(head), len(tiles)))
        f.write(head)
        f.write(struct.pack(f"<{len(tiles) + 1}Q", *offsets, pos))
        for t in tiles:
            f.write(t)
    header["bytes"] = out.stat().st_size
    return header


if __name__ == "__main__":  # pragma: no cover
    print(json.dumps(build(Path(sys.argv[1])), indent=1))

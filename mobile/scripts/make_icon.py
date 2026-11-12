"""Draw the PlantAdvocate icon and write every size the app ships.

Run from the repository root with a Python that has Pillow:

    garden-gnome/.venv/bin/python mobile/scripts/make_icon.py

The pot is a flowerpot seen from the front: a rim band over a body that
narrows toward the foot, with a seedling in it. The body must stay wider at
the top than at the bottom. The first 1.1.3 icon was a dome on a saucer and
read as something else entirely.
"""
from pathlib import Path

from PIL import Image, ImageDraw

ASSETS = Path(__file__).resolve().parent.parent / "assets"

GREEN = (47, 74, 51)
TERRACOTTA = (169, 84, 47)
TERRACOTTA_DARK = (134, 62, 33)
SOIL = (74, 48, 30)
CREAM = (245, 238, 221)
WHITE = (255, 255, 255)

SS = 4  # supersampling factor


def _leaf(size, colour, angle):
    """One leaf: a pointed lens, drawn flat then turned."""
    w, h = size
    layer = Image.new("RGBA", (w * 2, w * 2), (0, 0, 0, 0))
    mask = Image.new("L", (w * 2, w * 2), 0)
    a = Image.new("L", (w * 2, w * 2), 0)
    b = Image.new("L", (w * 2, w * 2), 0)
    # Two big circles whose overlap is a lens w wide and h tall, with its
    # left tip at the centre of the layer.
    r = (w * w / 4 + h * h / 4) / h
    cx, cy = w + w / 2, w
    ImageDraw.Draw(a).ellipse([cx - r, cy - h / 2, cx + r, cy - h / 2 + 2 * r], fill=255)
    ImageDraw.Draw(b).ellipse([cx - r, cy + h / 2 - 2 * r, cx + r, cy + h / 2], fill=255)
    mask = Image.composite(a, mask, b)
    layer.paste(colour + (255,), (0, 0), mask)
    return layer.rotate(angle, resample=Image.BICUBIC, center=(w, w))


def draw(px, scale=1.0, mono=False):
    """The artwork on a transparent square px wide, centred, at `scale`."""
    n = px * SS
    img = Image.new("RGBA", (n, n), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    u = n / 1024 * scale  # one design unit
    ox = n / 2 - 512 * u
    oy = n / 2 - 512 * u

    def X(x):
        return ox + x * u

    def Y(y):
        return oy + y * u

    pot = WHITE if mono else TERRACOTTA
    sprout = WHITE if mono else CREAM

    # Body: wide at the rim, narrow at the foot.
    top, foot = 512, 800
    d.polygon([(X(512 - 212), Y(top)), (X(512 + 212), Y(top)),
               (X(512 + 148), Y(foot - 26)), (X(512 + 122), Y(foot)),
               (X(512 - 122), Y(foot)), (X(512 - 148), Y(foot - 26))], fill=pot)
    if mono:
        # A gap stands in for the shadow under the rim.
        d.rectangle([X(250), Y(top), X(774), Y(top + 16)], fill=(0, 0, 0, 0))
    else:
        d.polygon([(X(512 - 212), Y(top)), (X(512 + 212), Y(top)),
                   (X(512 + 207), Y(top + 22)), (X(512 - 207), Y(top + 22))],
                  fill=TERRACOTTA_DARK)
        # Soil showing above the rim.
        d.ellipse([X(512 - 200), Y(424 - 30), X(512 + 200), Y(424 + 30)], fill=SOIL)
    # Rim band.
    d.rounded_rectangle([X(512 - 256), Y(424), X(512 + 256), Y(top)],
                        radius=22 * u, fill=pot)

    # Seedling.
    stem_top = 262
    d.rounded_rectangle([X(512 - 11), Y(stem_top), X(512 + 11), Y(428)],
                        radius=11 * u, fill=sprout)
    lw, lh = int(168 * u), int(92 * u)
    for angle, flip in ((28, False), (28, True)):
        leaf = _leaf((lw, lh), sprout, angle)
        if flip:
            leaf = leaf.transpose(Image.FLIP_LEFT_RIGHT)
        img.alpha_composite(leaf, (int(X(512)) - lw, int(Y(stem_top + 6)) - lw))

    return img.resize((px, px), Image.LANCZOS)


def on_green(px, scale=1.0):
    bg = Image.new("RGBA", (px, px), GREEN + (255,))
    bg.alpha_composite(draw(px, scale))
    return bg.convert("RGB")


def main():
    on_green(1024).save(ASSETS / "icon.png")
    draw(1024).save(ASSETS / "splash-icon.png")
    on_green(48, 1.1).save(ASSETS / "favicon.png")
    # Android masks the adaptive icon to its middle two thirds.
    draw(512, 0.64).save(ASSETS / "android-icon-foreground.png")
    Image.new("RGB", (512, 512), GREEN).save(ASSETS / "android-icon-background.png")
    draw(432, 0.64, mono=True).save(ASSETS / "android-icon-monochrome.png")
    for f in sorted(ASSETS.glob("*.png")):
        print(f.name, Image.open(f).size)


if __name__ == "__main__":
    main()

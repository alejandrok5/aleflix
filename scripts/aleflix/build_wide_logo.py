"""Build the 16:9 Aleflix logo: the Ridge landscape (moon, wolf, pines) beside
the Aleflix wordmark, the same lockup as the Android TV banner, drawn for big
screens.

Outputs, in branding/logo/:
  aleflix-logo-16x9.png              3840 x 2160, on Aleflix Noir
  aleflix-logo-16x9-1080p.png        1920 x 1080, on Aleflix Noir
  aleflix-logo-16x9-transparent.png  3840 x 2160, transparent background
  aleflix-wordmark.png               transparent, medallion and name (web header)
  aleflix-mark.png                   512 x 512, the medallion alone

Use the 1080p file for the Jellyfin splash screen (Dashboard -> Branding).

Needs Python with resvg-py and Pillow (see build_assets.py):
  /tmp/aleflix-brand/bin/python scripts/aleflix/build_wide_logo.py
"""
import io
import pathlib
import re

import resvg_py
from PIL import Image, ImageDraw, ImageFilter, ImageFont

NOIR = (14, 13, 12, 255)
IVORY = (244, 239, 230, 255)
CHAMPAGNE = (200, 169, 106, 255)

repo = pathlib.Path(__file__).resolve().parents[2]
out = repo / "branding/logo"
out.mkdir(parents=True, exist_ok=True)
fraunces_light = str(repo / "assets/fonts/Fraunces-Light.ttf")


def clean_svg(path):
    """Drop the C2PA metadata and the full-canvas background path."""
    t = path.read_text()
    t = re.sub(r"<metadata>.*?</metadata>", "", t, flags=re.S)
    t = re.sub(r'\s+xmlns:c2pa="[^"]*"', "", t)
    first = re.search(r"<path\b[^>]*/>", t)
    assert first and 'd="M 0 0 L 2048 0' in first.group(0), "unexpected first path"
    return t[: first.start()] + t[first.end():]


def with_viewbox(svg, box):
    x, y, w, h = box
    svg = re.sub(r'viewBox="[^"]*"', f'viewBox="{x:.1f} {y:.1f} {w:.1f} {h:.1f}"', svg, count=1)
    svg = re.sub(r'\swidth="\d+"', f' width="{w:.0f}"', svg, count=1)
    svg = re.sub(r'\sheight="\d+"', f' height="{h:.0f}"', svg, count=1)
    return svg.replace('preserveAspectRatio="none"', 'preserveAspectRatio="xMidYMid meet"')


def render(svg, width):
    png = bytes(resvg_py.svg_to_bytes(svg_string=svg, width=int(width)))
    return Image.open(io.BytesIO(png)).convert("RGBA")


def alpha_bbox(img):
    return img.getchannel("A").point(lambda a: 255 if a > 24 else 0).getbbox()


def save(img, name):
    path = out / name
    img.save(path, optimize=True)
    print(f"  {path.relative_to(repo)}  {img.size[0]}x{img.size[1]}")


W, H = 3840, 2160

# ---- The Ridge, trimmed to its art -------------------------------------------
ridge = clean_svg(repo / "branding/source/ridge.svg")
l, t, r, b = alpha_bbox(render(ridge, 2048))
ridge_art = render(with_viewbox(ridge, (l, t, r - l, b - t)), 2600)
ridge_art = ridge_art.crop(alpha_bbox(ridge_art))

# The moon, located by its ivory pixels, anchors the layout.
ivory = ridge_art.convert("RGB").point(lambda v: 255 if v > 225 else 0).convert("L")
ml, mt, mr, mb = ivory.point(lambda v: 255 if v == 255 else 0).getbbox()
moon_cy_frac = (mt + mb) / 2 / ridge_art.height
moon_cx_frac = (ml + mr) / 2 / ridge_art.width

# Fade the far ends of the slopes and the foot of the mountain into the
# background, so the art has no hard edges on any backdrop.
def feather(img, side=0.16, bottom=0.10):
    w, h = img.size
    mask = Image.new("L", (w, h), 255)
    md = ImageDraw.Draw(mask)
    fs, fb = round(w * side), round(h * bottom)
    for i in range(fs):
        v = round(255 * (i / fs) ** 1.5)
        md.line((i, 0, i, h), fill=v)
        md.line((w - 1 - i, 0, w - 1 - i, h), fill=v)
    bottom_mask = Image.new("L", (w, h), 255)
    bd = ImageDraw.Draw(bottom_mask)
    for i in range(fb):
        bd.line((0, h - 1 - i, w, h - 1 - i), fill=round(255 * (i / fb) ** 1.5))
    alpha = img.getchannel("A")
    alpha = Image.composite(alpha, Image.new("L", (w, h), 0), mask)
    alpha = Image.composite(alpha, Image.new("L", (w, h), 0), bottom_mask)
    img.putalpha(alpha)
    return img


# ---- Layout: art and wordmark centred together as one group, inside the
# central 80% so a TV's overscan never clips it ---------------------------------
text = "Aleflix"
art_h = round(H * 0.50)
art = ridge_art.resize((round(ridge_art.width * art_h / ridge_art.height), art_h), Image.LANCZOS)
art = feather(art)
font = ImageFont.truetype(fraunces_light, round(art_h * 0.37))
probe = ImageDraw.Draw(Image.new("RGBA", (1, 1)))
tl, tt, tr, tb = probe.textbbox((0, 0), text, font=font, anchor="ls")
text_w, cap_h = tr - tl, -tt
gap = round(W * 0.03)
group_w = art.width + gap + text_w
assert group_w <= W * 0.80, f"lockup too wide: {group_w}"
x0 = (W - group_w) // 2
art_y = (H - art_h) // 2
# The name sits on the moon's centre line, with a short champagne rule below it.
moon_cx = x0 + round(art.width * moon_cx_frac)
moon_cy = art_y + round(art_h * moon_cy_frac)
text_x = x0 + art.width + gap
baseline = moon_cy + cap_h // 2

layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
layer.alpha_composite(art, (x0, art_y))
d = ImageDraw.Draw(layer)
d.text((text_x - tl, baseline), text, font=font, fill=IVORY, anchor="ls")
rule_y = baseline + round(cap_h * 0.36)
rule_h = max(6, round(cap_h * 0.022))
d.rectangle((text_x + round(cap_h * 0.02), rule_y, text_x + round(text_w * 0.2), rule_y + rule_h), fill=CHAMPAGNE)

# ---- Backgrounds -------------------------------------------------------------
# A faint warm glow behind the moon gives the noir field some depth without a
# visible gradient band.
glow = Image.new("L", (W, H), 0)
gx, gy = moon_cx, moon_cy
gr = round(art_h * 0.95)
ImageDraw.Draw(glow).ellipse((gx - gr, gy - gr, gx + gr, gy + gr), fill=34)
glow = glow.filter(ImageFilter.GaussianBlur(gr * 0.45))
opaque = Image.new("RGBA", (W, H), NOIR)
opaque = Image.composite(Image.new("RGBA", (W, H), (138, 122, 94, 255)), opaque, glow)
opaque.alpha_composite(layer)

print("16:9 logo")
save(opaque.convert("RGB"), "aleflix-logo-16x9.png")
save(opaque.convert("RGB").resize((1920, 1080), Image.LANCZOS), "aleflix-logo-16x9-1080p.png")
save(layer, "aleflix-logo-16x9-transparent.png")

# ---- Web header wordmark: the Howl medallion and the name, one line ---------
print("Header wordmark")
WW, WH = 1600, 400
howl = (repo / "branding/marks/howl.svg").read_text()
medal = render(howl, WH)
word = Image.new("RGBA", (WW, WH), (0, 0, 0, 0))
word.alpha_composite(medal, (0, 0))
wfont = ImageFont.truetype(fraunces_light, 300)
wd = ImageDraw.Draw(word)
wcap = -wfont.getbbox("A", anchor="ls")[1]
wx = WH + round(WH * 0.2)
wd.text((wx, WH // 2 + wcap // 2), text, font=wfont, fill=IVORY, anchor="ls")
word = word.crop(alpha_bbox(word))
save(word, "aleflix-wordmark.png")
# The medallion alone, for square spots such as the TV-layout header.
save(render(howl, 512), "aleflix-mark.png")
print("done")

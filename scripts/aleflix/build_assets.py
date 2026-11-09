"""Build every Aleflix Android/Flutter brand asset from the two chosen vector marks.

  The Howl  (branding/source/howl.svg): launcher icon, themed icon, in-app logo, wordmark
  The Ridge (branding/source/ridge.svg): splash screen, Android TV banner

Both are Recraft V4.1 vector outputs. Needs Python with resvg-py and Pillow:
  uv venv /tmp/aleflix-brand && uv pip install --python /tmp/aleflix-brand resvg-py pillow
  /tmp/aleflix-brand/bin/python scripts/aleflix/build_assets.py [--preview <dir>]
"""
import io
import pathlib
import re
import sys

import resvg_py
from PIL import Image, ImageDraw, ImageFont

CHARCOAL = (14, 13, 12, 255)
IVORY = (244, 239, 230, 255)
GOLD = (200, 169, 106, 255)

repo = pathlib.Path(__file__).resolve().parents[2]
brand = repo / "branding"
preview = pathlib.Path(sys.argv[sys.argv.index("--preview") + 1]) if "--preview" in sys.argv else None
res = repo / "android/app/src/main/res"
fonts = repo / "assets/fonts"
marks = brand / "marks"
marks.mkdir(exist_ok=True)


def clean_svg(path):
    """Drop the C2PA metadata and the full-canvas background path."""
    t = path.read_text()
    t = re.sub(r"<metadata>.*?</metadata>", "", t, flags=re.S)
    t = re.sub(r'\s+xmlns:c2pa="[^"]*"', "", t)
    first = re.search(r"<path\b[^>]*/>", t)
    assert first and 'd="M 0 0 L 2048 0' in first.group(0), "unexpected first path"
    return t[: first.start()] + t[first.end():]


def with_viewbox(svg, box, extra=""):
    x, y, w, h = box
    svg = re.sub(r'viewBox="[^"]*"', f'viewBox="{x:.1f} {y:.1f} {w:.1f} {h:.1f}"', svg, count=1)
    svg = re.sub(r'\swidth="\d+"', f' width="{w:.0f}"', svg, count=1)
    svg = re.sub(r'\sheight="\d+"', f' height="{h:.0f}"', svg, count=1)
    svg = svg.replace('preserveAspectRatio="none"', 'preserveAspectRatio="xMidYMid meet"')
    if extra:  # inserted as the first drawn element
        svg = re.sub(r"(<svg\b[^>]*>)", r"\1" + extra.replace("\\", "\\\\"), svg, count=1)
    return svg


def render(svg, width):
    png = bytes(resvg_py.svg_to_bytes(svg_string=svg, width=int(width)))
    return Image.open(io.BytesIO(png)).convert("RGBA")


def alpha_bbox(img):
    return img.getchannel("A").point(lambda a: 255 if a > 24 else 0).getbbox()


def square_box(cx, cy, side):
    return (cx - side / 2, cy - side / 2, side, side)


def save(img, path):
    path.parent.mkdir(parents=True, exist_ok=True)
    img.save(path, optimize=True)
    print(f"  {path.relative_to(repo) if repo in path.parents else path}  {img.size[0]}x{img.size[1]}")


howl = clean_svg(brand / "source/howl.svg")
ridge = clean_svg(brand / "source/ridge.svg")

# Locate the moon in canvas units (both SVGs are 2048 x 2048).
full = render(howl, 2048)
l, t, r, b = alpha_bbox(full)
moon_cx, moon_cy = (l + r) / 2, (t + b) / 2
moon_r = max(r - l, b - t) / 2
print(f"Howl moon: center=({moon_cx:.0f},{moon_cy:.0f}) r={moon_r:.0f}")

ridge_full = render(ridge, 2048)
rl, rt, rr, rb = alpha_bbox(ridge_full)
# The moon is the tallest ivory shape; take its top edge and width from the
# central column to keep the slopes from widening the box.
ridge_moon_top = rt
print(f"Ridge art bbox: {rl},{rt},{rr},{rb}")

# A charcoal disc behind the moon makes the wolf solid instead of a cutout, so
# the logo still reads over photos and artwork.
disc = f'<circle cx="{moon_cx:.1f}" cy="{moon_cy:.1f}" r="{moon_r - 2:.1f}" fill="rgb(14,13,12)"/>'
howl_box = square_box(moon_cx, moon_cy, moon_r * 2 * 1.02)
howl_solid_svg = with_viewbox(howl, howl_box, disc)
howl_cutout_svg = with_viewbox(howl, howl_box)
(marks / "howl.svg").write_text(howl_solid_svg)
(marks / "howl-cutout.svg").write_text(howl_cutout_svg)

print("Flutter assets")
(repo / "assets/icons/moonfin_logo.svg").write_text(howl_solid_svg)
print("  assets/icons/moonfin_logo.svg  (vector)")

# ---- Launcher icon (adaptive) ------------------------------------------------
# The foreground sits in a 10dp inset (drawable/ic_launcher_foreground_inset),
# so the 108dp layer is drawn at 88dp. A moon 66% of the layer wide lands near
# 58dp, inside the 66dp safe zone that every mask shape keeps.
print("Launcher icons")
DENSITIES = {"mdpi": 1, "hdpi": 1.5, "xhdpi": 2, "xxhdpi": 3, "xxxhdpi": 4}
fg_master = Image.new("RGBA", (1728, 1728), (0, 0, 0, 0))
mark = render(howl_cutout_svg, round(1728 * 0.66))
fg_master.alpha_composite(mark, ((1728 - mark.width) // 2, (1728 - mark.height) // 2))

# Themed (monochrome) icon: the launcher tints it, so only alpha matters. Ivory
# becomes opaque and the dark edge detail fades out with it.
lum = fg_master.convert("L")
mono_alpha = Image.eval(lum, lambda v: max(0, min(255, int((v - 70) * 255 / (230 - 70)))))
mono_master = Image.new("RGBA", fg_master.size, (255, 255, 255, 0))
mono_master.putalpha(Image.composite(mono_alpha, Image.new("L", fg_master.size, 0), fg_master.getchannel("A")))

legacy_master = Image.new("RGBA", (768, 768), (0, 0, 0, 0))
ImageDraw.Draw(legacy_master).ellipse((0, 0, 767, 767), fill=CHARCOAL)
lm = render(howl_cutout_svg, round(768 * 0.74))
legacy_master.alpha_composite(lm, ((768 - lm.width) // 2, (768 - lm.height) // 2))

for name, scale in DENSITIES.items():
    fg = round(108 * scale)
    save(fg_master.resize((fg, fg), Image.LANCZOS), res / f"mipmap-{name}/ic_launcher_foreground.png")
    save(mono_master.resize((fg, fg), Image.LANCZOS), res / f"mipmap-{name}/ic_launcher_monochrome.png")
    lg = round(48 * scale)
    save(legacy_master.resize((lg, lg), Image.LANCZOS), res / f"mipmap-{name}/ic_launcher.png")

# ---- Store / generic icon ----------------------------------------------------
store = Image.new("RGBA", (1024, 1024), CHARCOAL)
sm = render(howl_cutout_svg, round(1024 * 0.70))
store.alpha_composite(sm, ((1024 - sm.width) // 2, (1024 - sm.height) // 2))
save(store, repo / "assets/icons/app_icon.png")
save(store.resize((512, 512), Image.LANCZOS), repo / "assets/icons/moonfin.png")
if preview:
    save(store, preview / "store-icon-1024.png")

# ---- Wordmark ----------------------------------------------------------------
# Same 1179 x 266 frame as upstream's logo_and_text.png, so every screen that
# sizes it by height keeps its layout.
print("Wordmark")
W, H = 1179 * 2, 266 * 2
word = Image.new("RGBA", (W, H), (0, 0, 0, 0))
disc_img = render(howl_solid_svg, H)
word.alpha_composite(disc_img, (0, 0))
font = ImageFont.truetype(str(fonts / "Fraunces-Light.ttf"), 400)
d = ImageDraw.Draw(word)
text = "Aleflix"
tb = d.textbbox((0, 0), text, font=font, anchor="ls")
text_x = H + int(H * 0.22)
cap_h = -font.getbbox("A", anchor="ls")[1]
baseline = H // 2 + cap_h // 2
d.text((text_x, baseline), text, font=font, fill=IVORY, anchor="ls")
word = word.crop((0, 0, min(W, text_x + tb[2] + 8), H))
canvas = Image.new("RGBA", (W, H), (0, 0, 0, 0))
canvas.alpha_composite(word, (0, 0))
save(canvas.resize((1179, 266), Image.LANCZOS), repo / "assets/images/logo_and_text.png")

# ---- Splash (Android 12+ system splash, and the pre-12 launch window) ---------
# Icon without a background: 288dp canvas, contents kept inside a 192dp circle.
print("Splash")
SPL = 1152  # 288dp at xxxhdpi
ridge_side = (rr - rl) * 0.62
ridge_cx = (rl + rr) / 2
ridge_box = (ridge_cx - ridge_side / 2, ridge_moon_top - ridge_side * 0.04, ridge_side, ridge_side)
ridge_crop_svg = with_viewbox(ridge, ridge_box)
(marks / "ridge-crop.svg").write_text(ridge_crop_svg)
inner = round(SPL * 192 / 288)
art = render(ridge_crop_svg, inner)
mask = Image.new("L", (inner, inner), 0)
ImageDraw.Draw(mask).ellipse((0, 0, inner - 1, inner - 1), fill=255)
art.putalpha(Image.composite(art.getchannel("A"), Image.new("L", art.size, 0), mask))
splash = Image.new("RGBA", (SPL, SPL), (0, 0, 0, 0))
splash.alpha_composite(art, ((SPL - inner) // 2, (SPL - inner) // 2))
save(splash, res / "drawable-xxxhdpi/aleflix_splash.png")

# ---- Android TV banner (320 x 180, xhdpi) --------------------------------------
print("TV banner")
S = 4  # supersample
BW, BH = 320 * S, 180 * S
banner = Image.new("RGBA", (BW, BH), CHARCOAL)
art_h = round(BH * 0.80)
ridge_wide_box = (rl, ridge_moon_top - (rb - ridge_moon_top) * 0.06, rr - rl, (rb - ridge_moon_top) * 1.06)
ridge_wide = render(with_viewbox(ridge, ridge_wide_box), 2048)
ridge_wide = ridge_wide.resize((round(ridge_wide.width * art_h / ridge_wide.height), art_h), Image.LANCZOS)
# The central part of the landscape: moon, wolf and both slopes, with the
# far foothills trimmed so the wordmark has clean space on the right.
keep_w = round(BW * 0.46)
ox = (ridge_wide.width - keep_w) // 2
ridge_part = ridge_wide.crop((ox, 0, ox + keep_w, art_h))
banner.alpha_composite(ridge_part, (round(BW * 0.03), BH - art_h))
bfont = ImageFont.truetype(str(fonts / "Fraunces-Light.ttf"), round(BH * 0.27))
bd = ImageDraw.Draw(banner)
bcap = -bfont.getbbox("A", anchor="ls")[1]
bx = round(BW * 0.545)
by = BH // 2 + bcap // 2
bd.text((bx, by), "Aleflix", font=bfont, fill=IVORY, anchor="ls")
# A short champagne hairline under the name: the only accent on the banner.
tw = bd.textlength("Aleflix", font=bfont)
bd.rectangle((bx + 2 * S, by + round(BH * 0.07), bx + 2 * S + round(tw * 0.22), by + round(BH * 0.07) + S), fill=GOLD)
save(banner.resize((320, 180), Image.LANCZOS).convert("RGB"), res / "drawable-nodpi/aleflix_tv_banner.png")
if preview:
    save(banner.convert("RGB"), preview / "tv-banner-1280.png")
    save(splash, preview / "splash-1152.png")
    save(canvas, preview / "wordmark-2x.png")
    save(mono_master.resize((432, 432)), preview / "monochrome-432.png")
    save(fg_master.resize((432, 432)), preview / "foreground-432.png")
print("done")

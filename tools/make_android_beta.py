"""One-off: Android beta recruitment post (1080x1350) and Story (1080x1920)."""
import os
from PIL import Image, ImageDraw, ImageFont
R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(R, "posts", "2026-11-18_android-beta")
F = lambda n, s: ImageFont.truetype(os.path.join(R, "tools", "fonts", n + ".ttf"), s)
SERIF = lambda s: F("newsreader-latin-400-normal", s); SANS = lambda s: F("karla-latin-500-normal", s); BOLD = lambda s: F("karla-latin-700-normal", s)
FOREST, FOREST2 = (18, 58, 49), (32, 70, 59); CREAM = (250, 247, 240); CORAL = (242, 154, 115); SAGE = (157, 195, 171); GREEN = (61, 220, 132)
ICON = Image.open(os.path.join(R, "tools", "brand", "icon.jpg")).convert("RGB")
SCREEN = Image.open(os.path.join(R, "tools", "screens", "health-care.png")).convert("RGB")

def bg(W, H):
    im = Image.new("RGB", (W, H), FOREST); d = ImageDraw.Draw(im)
    for y in range(H):
        k = y / H; d.line([(0, y), (W, y)], fill=tuple(int(FOREST[i] + (FOREST2[i] - FOREST[i]) * k) for i in range(3)))
    return im

def brand(im, x, y):
    d = ImageDraw.Draw(im); m = Image.new("L", (64, 64), 0); ImageDraw.Draw(m).rounded_rectangle([0, 0, 63, 63], radius=16, fill=255)
    im.paste(ICON.resize((64, 64), Image.LANCZOS), (x, y), m); d.text((x + 80, y + 10), "MyGroom", font=SERIF(38), fill=CREAM)

def phone(im, x, y, maxh):
    k = maxh / SCREEN.height; w, h = int(SCREEN.width * k), maxh
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([x - 14, y - 14, x + w + 14, y + h + 14], radius=48, fill=(10, 28, 23), outline=(62, 100, 86), width=3)
    m = Image.new("L", (w, h), 0); ImageDraw.Draw(m).rounded_rectangle([0, 0, w, h], radius=36, fill=255)
    im.paste(SCREEN.resize((w, h), Image.LANCZOS), (x, y), m)
    return w

def pill(d, x, y, text, fill, fg, f):
    tw = d.textlength(text, font=f); d.rounded_rectangle([x, y, x + tw + 56, y + f.size + 34], radius=(f.size + 34) // 2, fill=fill)
    d.text((x + 28, y + 15), text, font=f, fill=fg); return tw + 56

def make(W, H, story):
    im = bg(W, H); d = ImageDraw.Draw(im); pad = 84 if story else 72
    top = 250 if story else 64
    brand(im, pad, top)
    y = top + 120
    pill(d, pad, y, "ANDROID BETA", GREEN, FOREST, BOLD(30)); y += 100
    for line in ["Android owners,", "we need you"]:
        d.text((pad, y), line, font=SERIF(96 if story else 86), fill=CREAM); y += 104 if story else 94
    y += 16
    body = ["Help test MyGroom on Android", "before it launches. Track your", "horses, dogs and cats, then tell", "us what to fix."]
    for l in body: d.text((pad, y), l, font=SANS(40 if story else 36), fill=(232, 238, 232)); y += 54 if story else 48
    y += 30
    steps = ["1   Send us a DM saying ANDROID", "2   We add you to the beta", "3   Download and tell us what you think"]
    for s in steps: d.text((pad, y), s, font=BOLD(36 if story else 32), fill=SAGE); y += 56 if story else 50
    if story:
        k = 560 / SCREEN.height; pw = int(SCREEN.width * k)
        phone(im, W - pad - pw, 1120, 560)
        cy = H - 500
    else:
        k = 410 / SCREEN.height; pw = int(SCREEN.width * k)
        phone(im, W - 60 - pw, 900, 410)
        cy = H - 190
    f = BOLD(40 if story else 36)
    pill(d, pad, cy, "DM us: ANDROID", CORAL, FOREST, f)
    fy = cy + (110 if story else 100)
    d.text((pad, fy), "Already on iPhone? MyGroom is free", font=SANS(28 if story else 25), fill=SAGE)
    d.text((pad, fy + (40 if story else 34)), "mygroom.co.uk/start", font=SANS(28 if story else 25), fill=SAGE)
    return im

make(1080, 1350, False).save(os.path.join(OUT, "post.png"), optimize=True)
make(1080, 1920, True).save(os.path.join(OUT, "story.png"), optimize=True)
print("ok")

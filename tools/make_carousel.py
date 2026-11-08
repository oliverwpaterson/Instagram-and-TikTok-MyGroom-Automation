"""Build a MyGroom swipeable carousel (1080x1350 PNG slides) from real photos + exact text.

Usage: python3 tools/make_carousel.py carousel.json out_dir/
carousel.json:
{
  "label": "Winter care",                       # small tag on the cover
  "slides": [
    {"type": "cover", "photo": "horse-winter/123.jpg", "title": "Winter yard check", "sub": "5 things to look at this week"},
    {"type": "point", "photo": "horse-hoof/456.jpg", "title": "Heels and legs", "body": "After muddy days, check heels and pasterns for scabs or heat."},
    {"type": "end", "title": "Save this for your next yard visit", "question": "What's on your winter checklist?"}
  ]
}
Photos are paths under photos/library/. "focus" (0-1, default 0.4) sets the vertical crop point.
Point slides are numbered automatically. Every slide gets the logo and a page counter.
"""
import json, os, sys
from PIL import Image, ImageDraw, ImageFont, ImageFilter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FONTS = os.path.join(ROOT, "tools", "fonts")
LIB = os.path.join(ROOT, "photos", "library")
W, H = 1080, 1350
FOREST, FOREST2 = (18, 58, 49), (32, 70, 59)
CREAM, CORAL, SAGE = (250, 247, 240), (242, 154, 115), (157, 195, 171)
PAD = 84

def font(name, size): return ImageFont.truetype(os.path.join(FONTS, name + ".ttf"), size)
SERIF = lambda s: font("newsreader-latin-400-normal", s)
SANS = lambda s: font("karla-latin-500-normal", s)
SANSB = lambda s: font("karla-latin-700-normal", s)

def wrap(d, text, f, maxw):
    out, cur = [], ""
    for w in text.split():
        t = (cur + " " + w).strip()
        if d.textlength(t, font=f) <= maxw: cur = t
        else: out.append(cur); cur = w
    if cur: out.append(cur)
    return out

def cover_crop(im, focus=0.4):
    k = max(W / im.width, H / im.height)
    im = im.resize((int(im.width * k + 1), int(im.height * k + 1)), Image.LANCZOS)
    x = (im.width - W) // 2
    y = int((im.height - H) * focus)
    return im.crop((x, y, x + W, y + H))

def gradient(im, start=0.38, strength=0.92):
    """Darken the lower part of the photo with forest green so text stays legible."""
    g = Image.new("L", (1, H))
    for y in range(H):
        t = max(0.0, (y / H - start) / (1 - start))
        g.putpixel((0, y), int(255 * min(1, strength * (t ** 0.85) + 0.18 * (y / H))))
    mask = g.resize((W, H))
    return Image.composite(Image.new("RGB", (W, H), FOREST), im, mask)

def brand(im, d, n, total, icon):
    if icon is not None:
        ic = icon.resize((76, 76), Image.LANCZOS)
        m = Image.new("L", (76, 76), 0); ImageDraw.Draw(m).rounded_rectangle([0, 0, 75, 75], radius=18, fill=255)
        im.paste(ic, (PAD, 64), m)
    d.text((PAD + 94, 76), "MyGroom", font=SERIF(38), fill=CREAM)
    t = f"{n} / {total}"
    f = SANSB(26); tw = d.textlength(t, font=f)
    d.rounded_rectangle([W - PAD - tw - 36, 72, W - PAD, 118], radius=23, outline=CREAM, width=2)
    d.text((W - PAD - tw - 18, 80), t, font=f, fill=CREAM)

def text_block(d, lines, f, y, fill, lh):
    for l in lines:
        d.text((PAD, y), l, font=f, fill=fill); y += lh
    return y

APPROVED = json.load(open(os.path.join(LIB, "credits.json"))) if os.path.exists(os.path.join(LIB, "credits.json")) else {}

def photo_bg(photo, focus):
    if not APPROVED.get(photo, {}).get("approved"):
        raise SystemExit(f"photo not approved in photos/library/credits.json: {photo}")
    im = Image.open(os.path.join(LIB, photo)).convert("RGB")
    im = cover_crop(im, focus)
    # soft top shade so the logo reads on bright skies
    shade = Image.new("L", (1, H))
    for y in range(H): shade.putpixel((0, y), int(120 * max(0, 1 - y / 260)))
    im = Image.composite(Image.new("RGB", (W, H), (10, 25, 20)), im, shade.resize((W, H)))
    return gradient(im)

def slide_cover(s, n, total, label, icon):
    im = photo_bg(s["photo"], s.get("focus", 0.4)); d = ImageDraw.Draw(im)
    brand(im, d, n, total, icon)
    size = 118
    while True:
        f = SERIF(size); lines = wrap(d, s["title"], f, W - 2 * PAD)
        if len(lines) <= 3 or size <= 80: break
        size -= 8
    sub = wrap(d, s.get("sub", ""), SANS(44), W - 2 * PAD) if s.get("sub") else []
    block = 70 + len(lines) * int(size * 1.05) + 20 + len(sub) * 60 + 110
    y = H - block - 40
    if label:
        lf = SANSB(26); lw = d.textlength(label.upper(), font=lf)
        d.rounded_rectangle([PAD, y, PAD + lw + 40, y + 48], radius=24, fill=CORAL)
        d.text((PAD + 20, y + 9), label.upper(), font=lf, fill=FOREST)
    y += 70
    y = text_block(d, lines, f, y, CREAM, int(size * 1.05)) + 20
    y = text_block(d, sub, SANS(44), y, CREAM, 60)
    d.text((PAD, y + 40), "Swipe", font=SANSB(36), fill=CORAL)
    ax = PAD + d.textlength("Swipe", font=SANSB(36)) + 18; ay = y + 64
    d.line([(ax, ay), (ax + 44, ay)], fill=CORAL, width=5)
    d.polygon([(ax + 44, ay - 12), (ax + 62, ay), (ax + 44, ay + 12)], fill=CORAL)
    return im

def slide_point(s, n, total, k, icon):
    im = photo_bg(s["photo"], s.get("focus", 0.4)); d = ImageDraw.Draw(im)
    brand(im, d, n, total, icon)
    tf = SERIF(96); tl = wrap(d, s["title"], tf, W - 2 * PAD)
    bf = SANS(42); bl = wrap(d, s.get("body", ""), bf, W - 2 * PAD)
    y = H - (110 + len(tl) * 100 + 24 + len(bl) * 58) - 70
    d.ellipse([PAD, y, PAD + 84, y + 84], fill=CORAL)
    num = str(k); nf = SANSB(44); nw = d.textlength(num, font=nf)
    d.text((PAD + 42 - nw / 2, y + 14), num, font=nf, fill=FOREST)
    y += 110
    y = text_block(d, tl, tf, y, CREAM, 100) + 24
    text_block(d, bl, bf, y, (232, 238, 232), 58)
    return im

def slide_end(s, n, total, icon):
    im = Image.new("RGB", (W, H), FOREST); d = ImageDraw.Draw(im)
    for y in range(H):
        k = y / H; d.line([(0, y), (W, y)], fill=tuple(int(FOREST[i] + (FOREST2[i] - FOREST[i]) * k) for i in range(3)))
    brand(im, d, n, total, icon)
    y = 300
    d.text((PAD, y), "SAVE THIS", font=SANSB(30), fill=CORAL); y += 80
    y = text_block(d, wrap(d, s["title"], SERIF(84), W - 2 * PAD), SERIF(84), y, CREAM, 92) + 60
    if s.get("question"):
        d.line([(PAD, y), (W - PAD, y)], fill=(62, 100, 86), width=2); y += 50
        d.text((PAD, y), "Your turn:", font=SANSB(34), fill=SAGE); y += 56
        y = text_block(d, wrap(d, s["question"], SERIF(64), W - 2 * PAD), SERIF(64), y, CORAL, 74) + 10
        d.text((PAD, y), "Tell us in the comments", font=SANS(36), fill=CREAM); y += 60
    # download button
    bf = SANSB(38); label = "Free app: link in bio"; bw = d.textlength(label, font=bf) + 80
    by = H - 250
    d.rounded_rectangle([PAD, by, PAD + bw, by + 92], radius=46, fill=CORAL)
    d.text((PAD + 40, by + 22), label, font=bf, fill=FOREST)
    d.text((PAD, by + 120), "iPhone & web  ·  mygroom.co.uk/start", font=SANS(32), fill=SAGE)
    return im

def main(cfg_path, out_dir):
    cfg = json.load(open(cfg_path)); slides = cfg["slides"]; total = len(slides)
    icon_p = os.path.join(ROOT, "tools", "brand", "icon.jpg")
    icon = Image.open(icon_p).convert("RGB") if os.path.exists(icon_p) else None
    os.makedirs(out_dir, exist_ok=True); k = 0; paths = []
    for i, s in enumerate(slides, 1):
        if s["type"] == "cover": im = slide_cover(s, i, total, cfg.get("label", ""), icon)
        elif s["type"] == "point": k += 1; im = slide_point(s, i, total, k, icon)
        elif s["type"] == "end": im = slide_end(s, i, total, icon)
        else: raise SystemExit(f"unknown slide type {s['type']}")
        p = os.path.join(out_dir, f"{i:02d}.png"); im.save(p, optimize=True); paths.append(p)
    print("\n".join(paths))

if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])

"""'What a horse costs a month' trend carousel: full-bleed real photo + small TikTok-style caption per slide.
Writes tiktok-NN.png (1080x1920) and ig-NN.png (1080x1350) into posts/2026-11-20_horse-cost/."""
import json, os
from PIL import Image, ImageDraw, ImageFont, ImageFilter
R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LIB = os.path.join(R, "photos", "library"); OUT = os.path.join(R, "posts", "2026-11-20_horse-cost")
APPROVED = json.load(open(os.path.join(LIB, "credits.json")))
BOLD = lambda s: ImageFont.truetype(os.path.join(R, "tools", "fonts", "karla-latin-700-normal.ttf"), s)
ICON = Image.open(os.path.join(R, "tools", "brand", "icon.jpg")).convert("RGB")
SLIDES = [
 ("horse-field/caa34827-01fe-4695-b78e-2bd4d71f8a47.jpg", 0.5, 0.5, ["What it costs to own a horse", "in the UK, every month ✨"], 0.30),
 ("horse-stable/4a5217b2-2964-447a-89b6-dcc28dc8a629.jpg", 0.5, 0.5, ["DIY livery - £200"], 0.30),
 ("horse-hay/5d81cc90-148a-4505-be6b-37912949ca95.jpg", 0.5, 0.5, ["Hay & hard feed - £120"], 0.28),
 ("horse-stable/e4602385-09be-4c59-ae7f-831a2f3fccee.jpg", 0.5, 0.4, ["Bedding - £45"], 0.30),
 ("farrier/farrier-4VWoFIHnlLc.jpg", 0.5, 0.5, ["Farrier - £65"], 0.22),
 ("horse-field/5210b744-ab2a-4202-b837-721acfeb454e.jpg", 0.5, 0.3, ["Insurance - £100"], 0.22),
 ("horse-portrait/28719819-5eb9-4c6e-be43-9598c2f7c445.jpg", 0.12, 0.35, ["Jabs, dentist & worming - £26"], 0.24),
 ("horse-field/5a026897-8e6a-451b-b7ab-200e4a02733c.jpg", 0.55, 0.5, ["Physio & saddle checks - £29"], 0.22),
 ("horse-rug/rug-N89g-ljbiPA.jpg", 0.5, 0.45, ["Total - £585 a month", "(and that's before the rugs 😅)"], 0.22),
 ("horse-rug/rug-I_1odt9Ej_Y.jpg", 0.5, 0.4, ["How do you compare?", "Higher, lower, or", "don't want to know? 👇"], 0.20),
]
EMOJI_FONT = "/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf"

def cover(path, W, H, fx, fy):
    im = Image.open(os.path.join(LIB, path)).convert("RGB"); k = max(W / im.width, H / im.height)
    im = im.resize((int(im.width * k) + 1, int(im.height * k) + 1), Image.LANCZOS)
    x = int((im.width - W) * fx); y = int((im.height - H) * fy); return im.crop((x, y, x + W, y + H))

def text_line(im, line, cx, y, size):
    """TikTok-style: white bold text with a soft dark shadow. Emoji drawn with Noto Color Emoji if present."""
    f = BOLD(size)
    parts, cur = [], ""
    for ch in line:
        if ord(ch) > 0x2000 and ch not in "£–-'’": 
            if cur: parts.append(("t", cur)); cur = ""
            parts.append(("e", ch))
        else: cur += ch
    if cur: parts.append(("t", cur))
    d = ImageDraw.Draw(im)
    ew = int(size * 1.15)
    widths = [d.textlength(p, font=f) if k == "t" else (ew if os.path.exists(EMOJI_FONT) else 0) for k, p in parts]
    x = cx - sum(widths) / 2
    sh = Image.new("RGBA", im.size, (0, 0, 0, 0)); sd = ImageDraw.Draw(sh)
    xx = x
    for (k, p), w in zip(parts, widths):
        if k == "t": sd.text((xx + 2, y + 3), p, font=f, fill=(0, 0, 0, 200))
        xx += w
    a = sh.split()[3]
    im.paste(Image.new("RGB", im.size, (0, 0, 0)), (0, 0), a.filter(ImageFilter.GaussianBlur(10)).point(lambda v: min(255, int(v * 1.6))))
    im.paste(Image.new("RGB", im.size, (0, 0, 0)), (0, 0), a.filter(ImageFilter.GaussianBlur(3)))
    d = ImageDraw.Draw(im)
    for (k, p), w in zip(parts, widths):
        if k == "t": d.text((x, y), p, font=f, fill="white")
        elif os.path.exists(EMOJI_FONT):
            ef = ImageFont.truetype(EMOJI_FONT, 109)
            e = Image.new("RGBA", (136, 128), (0, 0, 0, 0)); ImageDraw.Draw(e).text((0, 0), p, font=ef, embedded_color=True)
            e = e.resize((ew, int(ew * 128 / 136)), Image.LANCZOS); im.paste(e, (int(x), int(y - size * 0.05)), e)
        x += w

def badge(im):
    W, H = im.size; d = ImageDraw.Draw(im); f = BOLD(26); label = "@mygroomltd"; tw = d.textlength(label, font=f)
    x1, y1 = W - 28, H - (300 if H == 1920 else 28); x0, y0 = int(x1 - tw - 74), y1 - 50
    d.rounded_rectangle([x0, y0, x1, y1], radius=25, fill=(18, 58, 49))
    m = Image.new("L", (34, 34), 0); ImageDraw.Draw(m).ellipse([0, 0, 33, 33], fill=255)
    im.paste(ICON.resize((34, 34), Image.LANCZOS), (x0 + 10, y0 + 8), m); d.text((x0 + 54, y0 + 10), label, font=f, fill=(250, 247, 240))

for i, (photo, fx, fy, lines, ty) in enumerate(SLIDES, 1):
    assert APPROVED.get(photo, {}).get("approved"), photo
    for W, H, tag in ((1080, 1920, "tiktok"), (1080, 1350, "ig")):
        im = cover(photo, W, H, fx, fy)
        size = 46 if len(lines) == 1 else 44
        y = int(H * ty)
        for l in lines:
            text_line(im, l, W / 2, y, size); y += int(size * 1.35)
        if i in (1, len(SLIDES)) : badge(im)
        im.save(os.path.join(OUT, f"{tag}-{i:02d}.png"), optimize=True)
        im.convert("RGB").save(os.path.join(OUT, f"{tag}-{i:02d}.jpg"), quality=92, optimize=True)  # TikTok photos reject PNG
print("ok")

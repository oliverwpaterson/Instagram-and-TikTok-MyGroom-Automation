"""MyGroom meme maker: classic top/bottom meme text over a real, approved photo.

Usage: python3 tools/make_meme.py memes.json out_dir/
memes.json:
{"memes": [
  {"name": "farrier-hour", "photo": "farrier/farrier-4VWoFIHnlLc.jpg", "focus": 0.3, "focus_x": 0.5,
   "top": "When the farrier texts 'here in an hour'", "bottom": "And your pony's in the furthest field",
   "sticker": "Face screaming in fear", "sticker_pos": "right", "sticker_y": 0.5}
]}
Writes for each meme:
  <name>.png        1080x1350 feed image (Instagram post / TikTok photo)
  <name>_story.png  1080x1920 story image
  <name>.mp4        1080x1920, ~6 s animated version (slow zoom, punchline drops in, 3D emoji sticker bounces)
- Text is drawn in Anton (SIL OFL, tools/fonts) in capitals, white with a black outline, auto-sized.
- "sticker" is a Microsoft Fluent Emoji 3D name (MIT), fetched from GitHub into tools/stickers/ and cached.
  We never use film/TV reaction GIFs or other copyrighted meme templates; the emoji sticker is our "GIF".
- Photos must be approved in photos/library/credits.json. Keep jokes kind: laugh with owners, never at
  animals' welfare; no medical claims.
"""
import json, os, subprocess, sys, urllib.parse, urllib.request
from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LIB = os.path.join(ROOT, "photos", "library")
FONT = os.path.join(ROOT, "tools", "fonts", "anton-regular.ttf")
SANSB = os.path.join(ROOT, "tools", "fonts", "karla-latin-700-normal.ttf")
STICKERS = os.path.join(ROOT, "tools", "stickers")
ICON = os.path.join(ROOT, "tools", "brand", "icon.jpg")
APPROVED = json.load(open(os.path.join(LIB, "credits.json")))
FPS = 30


def cover(path, W, H, fx, fy, zoom=1.0):
    im = Image.open(path).convert("RGB")
    k = max(W / im.width, H / im.height) * zoom
    im = im.resize((int(im.width * k) + 1, int(im.height * k) + 1), Image.LANCZOS)
    x = int((im.width - W) * fx); y = int((im.height - H) * fy)
    return im.crop((x, y, x + W, y + H))


def fit(d, text, W, max_lines=3, start=104, low=56):
    text = text.upper()
    size = start
    while True:
        f = ImageFont.truetype(FONT, size)
        lines, cur = [], ""
        for w in text.split():
            t = (cur + " " + w).strip()
            if d.textlength(t, font=f) <= W - 90: cur = t
            else: lines.append(cur); cur = w
        lines.append(cur)
        if len(lines) <= max_lines or size <= low: return f, lines, size
        size -= 4


def draw_block(d, text, W, y, anchor_top=True, scale=1.0):
    f, lines, size = fit(d, text, W)
    if scale != 1.0:
        f = ImageFont.truetype(FONT, max(10, int(size * scale))); size = int(size * scale)
    lh = int(size * 1.08)
    total = lh * len(lines)
    y0 = y if anchor_top else y - total
    for i, l in enumerate(lines):
        tw = d.textlength(l, font=f)
        d.text(((W - tw) / 2, y0 + i * lh), l, font=f, fill="white", stroke_width=max(4, size // 14), stroke_fill="black")
    return total


def sticker(name):
    os.makedirs(STICKERS, exist_ok=True)
    fn = os.path.join(STICKERS, name.lower().replace(" ", "_") + ".png")
    if not os.path.exists(fn):
        base = "https://raw.githubusercontent.com/microsoft/fluentui-emoji/main/assets/"
        q = urllib.parse.quote(name)
        low = name.lower().replace(" ", "_").replace("-", "_")
        for url in (f"{base}{q}/3D/{low}_3d.png", f"{base}{q}/Default/3D/{low}_3d_default.png"):
            try:
                urllib.request.urlretrieve(url, fn); break
            except Exception:
                continue
    return Image.open(fn).convert("RGBA") if os.path.exists(fn) else None


def badge(im):
    d = ImageDraw.Draw(im)
    W, H = im.size
    f = ImageFont.truetype(SANSB, 26)
    label = "@mygroomltd"
    tw = d.textlength(label, font=f)
    x1, y1 = W - 28, H - 28
    x0, y0 = int(x1 - tw - 74), y1 - 50
    d.rounded_rectangle([x0, y0, x1, y1], radius=25, fill=(18, 58, 49))
    ic = Image.open(ICON).convert("RGB").resize((34, 34), Image.LANCZOS)
    m = Image.new("L", (34, 34), 0); ImageDraw.Draw(m).ellipse([0, 0, 33, 33], fill=255)
    im.paste(ic, (x0 + 10, y0 + 8), m)
    d.text((x0 + 54, y0 + 10), label, font=f, fill=(250, 247, 240))


def still(m, W, H):
    im = cover(os.path.join(LIB, m["photo"]), W, H, m.get("focus_x", 0.5), m.get("focus", 0.4))
    d = ImageDraw.Draw(im)
    top_y = 60 if H == 1350 else 250
    bot_y = H - 110 if H == 1350 else H - 330
    draw_block(d, m["top"], W, top_y, True)
    draw_block(d, m["bottom"], W, bot_y, False)
    st = sticker(m["sticker"]) if m.get("sticker") else None
    if st:
        s = 230
        st = st.resize((s, s), Image.LANCZOS)
        x = W - s - 40 if m.get("sticker_pos", "right") == "right" else 40
        im.paste(st, (x, int(H * m.get("sticker_y", 0.5)) - s // 2), st)
    badge(im)
    return im


def animated(m, out):
    W, H, dur = 1080, 1920, 6.0
    base = os.path.join(LIB, m["photo"])
    st = sticker(m["sticker"]) if m.get("sticker") else None
    p = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                          "-r", str(FPS), "-i", "-", "-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo", "-shortest",
                          "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-pix_fmt", "yuv420p",
                          "-c:a", "aac", "-movflags", "+faststart", out], stdin=subprocess.PIPE)
    src = Image.open(base).convert("RGB")
    for i in range(int(dur * FPS)):
        t = i / FPS
        z = 1.0 + 0.06 * (t / dur)
        k = max(W / src.width, H / src.height) * z
        rs = src.resize((int(src.width * k) + 1, int(src.height * k) + 1), Image.BILINEAR)
        x = int((rs.width - W) * m.get("focus_x", 0.5)); y = int((rs.height - H) * m.get("focus", 0.4))
        im = rs.crop((x, y, x + W, y + H))
        d = ImageDraw.Draw(im)
        draw_block(d, m["top"], W, 250, True)
        if t >= 1.6:
            pt = min(1.0, (t - 1.6) / 0.25)
            sc = 1.35 - 0.35 * pt if pt < 1 else 1.0
            draw_block(d, m["bottom"], W, H - 330, False, sc)
        if st and t >= 1.9:
            s = 260
            bt = t - 1.9
            bounce = int(abs((bt * 3) % 2 - 1) * 40) if bt > 0.3 else int((1 - bt / 0.3) * -200)
            sz = int(s * min(1.0, 0.4 + bt * 2))
            sti = st.resize((sz, sz), Image.LANCZOS)
            xx = W - sz - 50 if m.get("sticker_pos", "right") == "right" else 50
            im.paste(sti, (xx, int(H * m.get("sticker_y", 0.5)) - sz // 2 + bounce), sti)
        badge(im)
        p.stdin.write(im.tobytes())
    p.stdin.close(); p.wait()


def main(cfg, out):
    os.makedirs(out, exist_ok=True)
    for m in json.load(open(cfg))["memes"]:
        if not APPROVED.get(m["photo"], {}).get("approved"):
            raise SystemExit(f"photo not approved: {m['photo']}")
        feed = still(m, 1080, 1350)
        feed.save(os.path.join(out, m["name"] + ".png"), optimize=True)
        feed.convert("RGB").save(os.path.join(out, m["name"] + ".jpg"), quality=92, optimize=True)  # TikTok photos reject PNG
        still(m, 1080, 1920).save(os.path.join(out, m["name"] + "_story.png"), optimize=True)
        if m.get("animated", True):
            animated(m, os.path.join(out, m["name"] + ".mp4"))
        print("wrote", m["name"])


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])

"""Build MyGroom Instagram Story frames (1080x1920 PNG) from real photos or app screens + exact text.

Usage: python3 tools/make_story.py stories.json out_dir/      (writes story-1.png, story-2.png ...)
       python3 tools/make_story.py stories.json out_dir/ --tiktok   (writes tiktok-story-1.png ... for TikTok Stories)
--tiktok: same stories, laid out for TikTok's overlays (text kept clear of the right-hand buttons and the bottom
  caption/reply bar). TikTok Stories have no poll/slider/question stickers we can rely on, so question stories show
  a comment prompt instead of the sticker box (default per sticker type, or set "tiktok_prompt" on the story).
stories.json:
{"stories": [
  {"type": "question", "photo": "horse-winter/123.jpg", "focus": 0.4,
   "kicker": "Be honest", "question": "How many rugs does your horse own?", "sticker": "poll"},
  {"type": "app", "screen": "rug-advisor", "title": "Which rug tonight?", "body": "The Rug Advisor checks your local weather and clip."},
  {"type": "tip", "photo": "dog-winter/456.jpg", "label": "Wet walk tip", "title": "Towel, then paws", "body": "Wipe paws after gritted roads."}
]}
- question: photo on top, the question, and an empty dashed box where the owner adds Instagram's
  poll / question / slider sticker in the app ("sticker": "poll" | "question" | "slider" sets the hint).
  Stickers can't be added through Metricool, so question stories go in as "post by hand" (autoPublish false).
- app: a real MyGroom screenshot from tools/screens/<name>.png in a phone frame. Only claim what it shows.
- tip: photo with one short tip.
Every frame ends with "Free app: link in bio". Keep the top 250px and bottom 300px free of key text
(Instagram covers them with the profile bar and reply box). "focus"/"focus_x" (0-1) set the crop point. Photos must be approved in photos/library/credits.json.
"""
import json, os, sys
from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FONTS = os.path.join(ROOT, "tools", "fonts")
LIB = os.path.join(ROOT, "photos", "library")
SCREENS = os.path.join(ROOT, "tools", "screens")
W, H = 1080, 1920
FOREST, FOREST2 = (18, 58, 49), (32, 70, 59)
CREAM, CORAL, SAGE = (250, 247, 240), (242, 154, 115), (157, 195, 171)
PAD = 84
TIKTOK = "--tiktok" in sys.argv
RPAD = 190 if TIKTOK else PAD            # TikTok's like/comment/share buttons sit down the right edge
TEXTW = W - PAD - RPAD
FOOT_Y = H - 560 if TIKTOK else H - 420  # TikTok's caption and reply bar cover more of the bottom

def font(name, size): return ImageFont.truetype(os.path.join(FONTS, name + ".ttf"), size)
SERIF = lambda s: font("newsreader-latin-400-normal", s)
SANS = lambda s: font("karla-latin-500-normal", s)
SANSB = lambda s: font("karla-latin-700-normal", s)
APPROVED = json.load(open(os.path.join(LIB, "credits.json")))
ICON = Image.open(os.path.join(ROOT, "tools", "brand", "icon.jpg")).convert("RGB")

def wrap(d, text, f, maxw):
    out, cur = [], ""
    for w in text.split():
        t = (cur + " " + w).strip()
        if d.textlength(t, font=f) <= maxw: cur = t
        else: out.append(cur); cur = w
    if cur: out.append(cur)
    return out

def fit(d, text, mk, start, low, maxw, maxlines):
    size = start
    while True:
        f = mk(size); lines = wrap(d, text, f, maxw)
        if len(lines) <= maxlines or size <= low: return f, lines, size
        size -= 6

def green_bg():
    im = Image.new("RGB", (W, H), FOREST); d = ImageDraw.Draw(im)
    for y in range(H):
        k = y / H; d.line([(0, y), (W, y)], fill=tuple(int(FOREST[i] + (FOREST2[i] - FOREST[i]) * k) for i in range(3)))
    return im

def photo_bg(photo, focus, fade_from, focus_x=0.5):
    if not APPROVED.get(photo, {}).get("approved"):
        raise SystemExit(f"photo not approved in photos/library/credits.json: {photo}")
    im = Image.open(os.path.join(LIB, photo)).convert("RGB")
    k = max(W / im.width, H / im.height)
    im = im.resize((int(im.width * k + 1), int(im.height * k + 1)), Image.LANCZOS)
    x = int((im.width - W) * focus_x); y = int((im.height - H) * focus)
    im = im.crop((x, y, x + W, y + H))
    g = Image.new("L", (1, H))
    for yy in range(H):
        t = yy / H
        v = max(0.0, 0.45 * (1 - t / 0.14)) if t < 0.14 else 0.0          # top shade for the logo
        if t > fade_from: v = min(0.95, (t - fade_from) / 0.14 * 0.95)    # forest band for text
        g.putpixel((0, yy), int(255 * v))
    return Image.composite(green_bg(), im, g.resize((W, H)))

def brand(im, d):
    m = Image.new("L", (72, 72), 0); ImageDraw.Draw(m).rounded_rectangle([0, 0, 71, 71], radius=18, fill=255)
    im.paste(ICON.resize((72, 72), Image.LANCZOS), (PAD, 250), m)
    d.text((PAD + 90, 262), "MyGroom", font=SERIF(38), fill=CREAM)

def footer(d, y=None):
    bf = SANSB(38); label = "Free app: link in bio"; bw = d.textlength(label, font=bf) + 80
    by = y if y is not None else FOOT_Y
    d.rounded_rectangle([PAD, by, PAD + bw, by + 90], radius=45, fill=CORAL)
    d.text((PAD + 40, by + 21), label, font=bf, fill=FOREST)
    d.text((PAD, by + 112), "iPhone & web  ·  mygroom.co.uk/start", font=SANS(32), fill=SAGE)

def dashed_box(d, box, hint):
    x0, y0, x1, y1 = box
    for x in range(x0, x1, 36): d.line([(x, y0), (min(x + 20, x1), y0)], fill=SAGE, width=3); d.line([(x, y1), (min(x + 20, x1), y1)], fill=SAGE, width=3)
    for y in range(y0, y1, 36): d.line([(x0, y), (x0, min(y + 20, y1))], fill=SAGE, width=3); d.line([(x1, y), (x1, min(y + 20, y1))], fill=SAGE, width=3)
    f = SANS(30); tw = d.textlength(hint, font=f)
    d.text(((x0 + x1 - tw) / 2, (y0 + y1) / 2 - 18), hint, font=f, fill=SAGE)

TT_PROMPTS = {"poll": "Vote in the comments", "question": "Tell us in the comments", "slider": "Score yourself out of 10 in the comments"}

def comment_prompt(d, y, text):
    f = SANSB(44); lines = wrap(d, text, f, TEXTW - 60); h = 40 + 58 * len(lines)
    d.rounded_rectangle([PAD, y, PAD + TEXTW, y + h], radius=28, outline=CORAL, width=4)
    yy = y + 22
    for l in lines: d.text((PAD + 30, yy), l, font=f, fill=CREAM); yy += 58
    return h

HINTS = {"poll": "add a poll sticker here", "question": "add a question sticker here", "slider": "add an emoji slider here"}

def story_question(s):
    im = photo_bg(s["photo"], s.get("focus", 0.4), 0.36, s.get("focus_x", 0.5)); d = ImageDraw.Draw(im); brand(im, d)
    y = int(H * (0.42 if TIKTOK else 0.47))
    if s.get("kicker"):
        d.text((PAD, y), s["kicker"].upper(), font=SANSB(32), fill=CORAL); y += 62
    f, lines, size = fit(d, s["question"], SERIF, 96, 64, TEXTW, 3)
    for l in lines: d.text((PAD, y), l, font=f, fill=CREAM); y += int(size * 1.08)
    y += 40
    if TIKTOK:
        h = comment_prompt(d, y, s.get("tiktok_prompt") or TT_PROMPTS.get(s.get("sticker", "question"), TT_PROMPTS["question"]))
        footer(d, max(y + h + 60, FOOT_Y))
    else:
        dashed_box(d, (PAD, y, W - PAD, y + 230), HINTS.get(s.get("sticker", "question"), HINTS["question"]))
        footer(d, max(y + 290, FOOT_Y))
    return im

def story_tip(s):
    im = photo_bg(s["photo"], s.get("focus", 0.4), 0.42, s.get("focus_x", 0.5)); d = ImageDraw.Draw(im); brand(im, d)
    y = int(H * (0.48 if TIKTOK else 0.55))
    if s.get("label"):
        lf = SANSB(28); lw = d.textlength(s["label"].upper(), font=lf)
        d.rounded_rectangle([PAD, y, PAD + lw + 40, y + 50], radius=25, fill=CORAL)
        d.text((PAD + 20, y + 10), s["label"].upper(), font=lf, fill=FOREST); y += 80
    f, lines, size = fit(d, s["title"], SERIF, 100, 70, TEXTW, 2)
    for l in lines: d.text((PAD, y), l, font=f, fill=CREAM); y += int(size * 1.08)
    y += 20
    for l in wrap(d, s.get("body", ""), SANS(44), TEXTW): d.text((PAD, y), l, font=SANS(44), fill=(232, 238, 232)); y += 60
    footer(d, max(y + 40, FOOT_Y) if TIKTOK else None)
    return im

def story_app(s):
    im = green_bg(); d = ImageDraw.Draw(im); brand(im, d)
    y = 380
    f, lines, size = fit(d, s["title"], SERIF, 92, 64, TEXTW, 2)
    for l in lines: d.text((PAD, y), l, font=f, fill=CREAM); y += int(size * 1.08)
    for l in wrap(d, s.get("body", ""), SANS(40), TEXTW): d.text((PAD, y + 10), l, font=SANS(40), fill=SAGE); y += 54
    sc = Image.open(os.path.join(SCREENS, s["screen"] + ".png")).convert("RGB")
    top = y + 50; maxh = FOOT_Y - 50 - top; maxw = 640
    k = min(maxw / sc.width, maxh / sc.height); sw, sh = int(sc.width * k), int(sc.height * k)
    x0 = (W - sw) // 2
    d.rounded_rectangle([x0 - 16, top - 16, x0 + sw + 16, top + sh + 16], radius=56, fill=(12, 30, 25), outline=(62, 100, 86), width=3)
    m = Image.new("L", (sw, sh), 0); ImageDraw.Draw(m).rounded_rectangle([0, 0, sw, sh], radius=42, fill=255)
    im.paste(sc.resize((sw, sh), Image.LANCZOS), (x0, top), m)
    footer(d, FOOT_Y + 20)
    return im

def main(cfg, out):
    os.makedirs(out, exist_ok=True)
    for i, s in enumerate(json.load(open(cfg))["stories"], 1):
        im = {"question": story_question, "tip": story_tip, "app": story_app}[s["type"]](s)
        p = os.path.join(out, f"{'tiktok-' if TIKTOK else ''}story-{i}.png"); im.save(p, optimize=True); print("wrote", p)

if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])

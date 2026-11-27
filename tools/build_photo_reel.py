"""Build a 9:16 kinetic-text reel for MyGroom with PIL frames + ffmpeg.
Put icon.jpg (app icon) and logo.jpg (full logo) next to this script, and
illustration PNGs in ./img (name.png). Voiceover uses kokoro-onnx with
./tts/kokoro.onnx + ./tts/voices.bin when present.
Usage: python3 build_reel.py out.mp4 scenes.json [--music] [--no-vo]
Scene: [dur, kind, data, {"img": "horse", "vo": "spoken line"}]  (4th item optional)
Kinds: hook, tip, screen (real app screenshot from ./screens), cta
"""
import math, subprocess, sys, os
from PIL import Image, ImageDraw, ImageFont

W, H, FPS = 1080, 1920, 30
BG = (32, 70, 59)        # MyGroom forest green (app icon background)
BG2 = (22, 54, 45)
CREAM = (252, 248, 238)
ACCENT = (238, 140, 105) # MyGroom coral (cat)
SAGE = (140, 168, 138)   # MyGroom sage (dog)
MUTED = (196, 212, 196)
HERE = os.path.dirname(os.path.abspath(__file__))
def load(name):
    p = os.path.join(HERE, name)
    return Image.open(p).convert("RGB") if os.path.exists(p) else None
ICON = load("icon.jpg")   # square app icon, forest-green background
LOGO = load("logo.jpg")   # full logo with wordmark, cream background
def rounded(img, size, radius):
    img = img.resize(size, Image.LANCZOS)
    m = Image.new("L", size, 0); ImageDraw.Draw(m).rounded_rectangle([0, 0, size[0], size[1]], radius=radius, fill=255)
    return img, m
FONT_DIR = "/usr/share/fonts/opentype/inter/"
def font(w, s): return ImageFont.truetype(FONT_DIR + f"Inter-{w}.otf", s)
F_HOOK = font("Black", 112)
F_BIG = font("ExtraBold", 84)
F_BODY = font("Medium", 54)
F_NUM = font("Black", 64)
F_SMALL = font("SemiBold", 40)

import json
CFG = json.load(open(sys.argv[2] if len(sys.argv) > 2 else "scenes.json"))
ARGS = sys.argv[3:]
SCENES = [(x[0], x[1], x[2], x[3] if len(x) > 3 else {}) for x in CFG["scenes"]]
VOICE = CFG.get("voice", "bf_emma")
IMG_DIR = os.path.join(HERE, "img")
_img_cache = {}
def illo(name):
    if not name: return None
    if name not in _img_cache:
        p = os.path.join(IMG_DIR, name + ".png")
        _img_cache[name] = Image.open(p).convert("RGBA") if os.path.exists(p) else None
    return _img_cache[name]
def paste_illo(img, name, lt, box):
    im = illo(name)
    if im is None: return
    x0, y0, size = box
    s = ease(lt / 0.45)
    s = s * (1 + 0.08 * math.sin(min(1, lt / 0.45) * math.pi))  # small overshoot pop
    sz = max(1, int(size * s))
    bob = int(10 * math.sin(lt * 2.2))
    r = im.resize((sz, sz), Image.LANCZOS)
    img.paste(r, (x0 + (size - sz) // 2, y0 + (size - sz) // 2 + bob), r)
TAG = CFG.get("tag", "care tips")
SCREEN_DIR = os.path.join(HERE, "screens")
_screen_cache = {}
def screen(name):
    """Real app screenshot from ./screens/<name>.png (or .jpg/.webp)."""
    if name not in _screen_cache:
        im = None
        for ext in (".png", ".jpg", ".webp"):
            p = os.path.join(SCREEN_DIR, name + ext)
            if os.path.exists(p): im = Image.open(p).convert("RGB"); break
        _screen_cache[name] = im
    return _screen_cache[name]

def ease(t):  # easeOutCubic
    t = max(0.0, min(1.0, t)); return 1 - (1 - t) ** 3

def wrap(draw, text, f, maxw):
    words, lines, cur = text.split(), [], ""
    for w in words:
        test = (cur + " " + w).strip()
        if draw.textlength(test, font=f) <= maxw: cur = test
        else: lines.append(cur); cur = w
    if cur: lines.append(cur)
    return lines

def background(t):
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)
    # slow drifting gradient band for motion
    for y in range(0, H, 8):
        k = 0.5 + 0.5 * math.sin(y / 420 + t * 0.6)
        c = tuple(int(BG2[i] + (BG[i] - BG2[i]) * k) for i in range(3))
        d.rectangle([0, y, W, y + 8], fill=c)
    return img

def draw_text_in(d, x, y, text, f, fill, p, dy=60):
    a = ease(p)
    yy = y + (1 - a) * dy
    col = tuple(int(fill[i] * a + BG[i] * (1 - a)) for i in range(3))
    d.text((x, yy), text, font=f, fill=col)


PHOTO_DIR = os.path.join(HERE, "photos")
_photo_cache = {}
def photo_bg(name, lt, dur, focus=0.5):
    """Full-bleed real photo, cover-cropped to 9:16 with a slow Ken Burns zoom, darkened toward the bottom."""
    if name not in _photo_cache:
        im = Image.open(os.path.join(PHOTO_DIR, name)).convert("RGB")
        k = max(W * 1.12 / im.width, H * 1.12 / im.height)
        im = im.resize((int(im.width * k) + 1, int(im.height * k) + 1), Image.LANCZOS)
        grad = Image.new("L", (1, H))
        for y in range(H):
            v = (int(60 * (1 - y / 260)) if y < 260 else 0) if y < 760 else int(225 * min(1, (y - 760) / 520))
            grad.putpixel((0, y), v)
        _photo_cache[name] = (im, grad.resize((W, H)))
    im, grad = _photo_cache[name]
    z = 1.0 + 0.06 * min(1, lt / max(dur, 0.1))
    cw, ch = int(W * 1.12 / z), int(H * 1.12 / z)
    cx = int((im.width - cw) * focus); cy = (im.height - ch) // 2
    fr = im.crop((cx, cy, cx + cw, cy + ch)).resize((W, H), Image.LANCZOS)
    dark = Image.new("RGB", (W, H), (8, 20, 16))
    return Image.composite(dark, fr, grad)
def shadow_text(d, xy, text, f, fill):
    x, y = xy
    for dx, dy in ((3, 3), (2, 2)):
        d.text((x + dx, y + dy), text, font=f, fill=(0, 0, 0))
    d.text((x, y), text, font=f, fill=fill)

def render_scene(kind, data, lt, dur, gt, total, ex=None):
    ex = ex or {}
    pad = 90
    if kind in ("photohook", "phototip"):
        img = photo_bg(ex["photo"], lt, dur, ex.get("focus", 0.5))
    else:
        img = background(gt)
    d = ImageDraw.Draw(img)
    if kind == "photohook":
        # fully drawn on frame one (it is the cover)
        lab = ex.get("label", "")
        if lab:
            lf = F_SMALL
            tw = d.textlength(lab, font=lf)
            d.rounded_rectangle([pad, 1040, pad + tw + 56, 1110], radius=35, fill=ACCENT)
            d.text((pad + 28, 1052), lab, font=lf, fill=CREAM)
        y = 1150
        for i, line in enumerate(data):
            shadow_text(d, (pad, y), line, F_HOOK.font_variant(size=104), ACCENT if i == len(data) - 1 else CREAM)
            y += 128
    elif kind == "phototip":
        n, total_n, title, body = data[:4]
        a = ease(lt / 0.35)
        for k in range(total_n):
            x = pad + k * 44
            d.ellipse([x, 1010, x + 22, 1032], fill=ACCENT if k < n else (200, 200, 190))
        y = 1070 + int((1 - a) * 40)
        for line in wrap(d, title, F_BIG, W - 2 * pad):
            shadow_text(d, (pad, y), line, F_BIG, CREAM); y += 100
        y += 20
        b = ease((lt - 0.35) / 0.4)
        if b > 0:
            for line in wrap(d, body, F_BODY, W - 2 * pad):
                shadow_text(d, (pad, y + int((1 - b) * 20)), line, F_BODY, (235, 240, 232)); y += 70
        if ex.get("source"):
            d.text((pad, H - 150), ex["source"], font=F_SMALL.font_variant(size=32), fill=(210, 220, 210))
    elif kind == "hook":
        # Hook is fully drawn from frame one: that frame becomes the Instagram/TikTok cover
        # and is what viewers see in the first half-second, so no fade-in here.
        lt = lt + 1.2
        y = 640
        if ex.get("img"):
            paste_illo(img, ex["img"], lt, (W // 2 - 210, 300, 420)); y = 790
        for i, line in enumerate(data):
            f = F_HOOK
            fill = ACCENT if i == len(data) - 1 else CREAM
            draw_text_in(d, pad, y, line, f, fill, (lt - i * 0.18) / 0.35)
            y += 140
    elif kind == "tip":
        n, title, body = data[:3]
        if ex.get("img"):
            paste_illo(img, ex["img"], lt - 0.1, (W - pad - 380, 300, 380))
        # number badge pops
        s = ease(lt / 0.3)
        r = int(70 * s)
        cx, cy = pad + 70, 700
        if r > 0:
            d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=ACCENT)
            if s > 0.6:
                tw = d.textlength(str(n), font=F_NUM)
                d.text((cx - tw / 2, cy - 40), str(n), font=F_NUM, fill=CREAM)
        y = 820
        for line in wrap(d, title, F_BIG, W - 2 * pad):
            draw_text_in(d, pad, y, line, F_BIG, CREAM, (lt - 0.15) / 0.35); y += 100
        y += 30
        for j, line in enumerate(wrap(d, body, F_BODY, W - 2 * pad)):
            draw_text_in(d, pad, y, line, F_BODY, MUTED, (lt - 0.45 - j * 0.1) / 0.35, 30); y += 72
        # step dots
        for k in range(5):
            x = pad + k * 44
            d.ellipse([x, 560, x + 22, 582], fill=ACCENT if k < n else (62, 100, 86))
    elif kind == "screen":
        # Real app screen in a phone frame: data = ["caption line", "highlighted line", "screenshot name"]
        cap, hi, name = data[:3]
        y = 300
        draw_text_in(d, pad, y, cap, F_BIG.font_variant(size=64), CREAM, lt / 0.3, 40); y += 80
        draw_text_in(d, pad, y, hi, F_BIG.font_variant(size=64), ACCENT, (lt - 0.12) / 0.3, 40)
        sc = screen(name)
        if sc is not None:
            maxw, maxh = 700, 1180
            k = min(maxw / sc.width, maxh / sc.height)
            sw, sh = int(sc.width * k), int(sc.height * k)
            p = ease((lt - 0.2) / 0.5)
            x0 = (W - sw) // 2; y0 = 500 + int((1 - p) * 120)
            bez = 18
            d.rounded_rectangle([x0 - bez, y0 - bez, x0 + sw + bez, y0 + sh + bez], radius=64, fill=(12, 30, 25), outline=(62, 100, 86), width=3)
            card, m = rounded(sc, (sw, sh), 48)
            if p < 1: m = m.point(lambda v: int(v * max(0.0, p)))
            img.paste(card, (x0, y0), m)
    elif kind == "cta":
        y = 520
        draw_text_in(d, pad, y, data[0], F_BIG, CREAM, lt / 0.35); y += 100
        # highlight line (often the comment question): wrap to 3 lines, shrinking the font if needed
        hf = F_HOOK
        for size in (112, 100, 88, 78, 70):
            hf = F_HOOK.font_variant(size=size)
            hl = wrap(d, data[1], hf, W - 2 * pad)
            if len(hl) <= 3: break
        for k, line in enumerate(hl):
            draw_text_in(d, pad, y, line, hf, ACCENT, (lt - 0.15 - k * 0.08) / 0.35); y += int(hf.size * 1.15)
        y += 190 - int(hf.size * 1.15)
        for j, line in enumerate(wrap(d, data[2] + " " + data[3], F_BODY, W - 2 * pad)):
            draw_text_in(d, pad, y, line, F_BODY, CREAM, (lt - 0.5 - j * 0.1) / 0.35, 30); y += 72
        y += 50
        p = ease((lt - 0.9) / 0.45)
        if p > 0:
            cw = W - 2 * pad
            if LOGO is not None:
                ch = int(cw * LOGO.height / LOGO.width)
                card, m = rounded(LOGO, (cw, ch), 40)
                off = int((1 - p) * 40)
                if p < 1:
                    m = m.point(lambda v: int(v * p))
                img.paste(card, (pad, y + off), m); y += ch + 40
            else:
                y += 20
            q = ease((lt - 1.3) / 0.4)
            if q > 0:
                # Download prompt: posts can't carry clickable links, so point to the bio link page
                pf = F_BIG.font_variant(size=50)
                label = "Free download: link in bio"
                full = int(d.textlength(label, font=pf)) + 100
                bw = int(full * q)
                d.rounded_rectangle([pad, y, pad + bw, y + 110], radius=55, fill=ACCENT)
                if q > 0.9:
                    d.text((pad + 50, y + 28), label, font=pf, fill=CREAM)
                    d.text((pad + 6, y + 135), "iPhone & web  ·  mygroom.co.uk/start", font=F_SMALL, fill=SAGE)
    # brand + progress bar (constant motion cue)
    tx = pad
    if ICON is not None:
        ic, m = rounded(ICON, (110, 110), 26)
        img.paste(ic, (pad, 120), m); tx = pad + 135
        d.rounded_rectangle([pad - 2, 118, pad + 112, 232], radius=28, outline=(62, 100, 86), width=2)
    d.text((tx, 135), "MyGroom", font=F_SMALL, fill=CREAM)
    d.text((tx, 182), TAG, font=F_SMALL.font_variant(size=34), fill=SAGE)
    d.rectangle([0, H - 14, int(W * gt / total), H], fill=ACCENT)
    return img

SR = 24000
def make_vo():
    """Return list of (np.array audio or None) per scene, using kokoro-onnx."""
    import numpy as np
    if "--no-vo" in ARGS or not any(e.get("vo") for *_, e in SCENES): return None
    mp, vp = os.path.join(HERE, "tts", "kokoro.onnx"), os.path.join(HERE, "tts", "voices.bin")
    if not os.path.exists(mp):
        print("no TTS model; rendering without voiceover"); return None
    from kokoro_onnx import Kokoro
    k = Kokoro(mp, vp); out = []
    for *_, e in SCENES:
        if e.get("vo"):
            a, sr = k.create(e["vo"], voice=VOICE, speed=e.get("speed", 1.08), lang="en-gb")
            out.append(np.asarray(a, dtype="float32"))
        else: out.append(None)
    return out

def make_music(total, vo_mask):
    """Soft royalty-free pad + pluck bed (generated, no licensing), ducked under voice."""
    import numpy as np
    t = np.arange(int(total * SR)) / SR
    chords = [[261.6, 329.6, 392.0], [196.0, 246.9, 392.0], [220.0, 261.6, 329.6], [174.6, 220.0, 349.2]]
    bar = 2.4; y = np.zeros_like(t)
    for i in range(int(total / bar) + 1):
        seg = (t >= i * bar) & (t < (i + 1) * bar + 0.6)
        tt = t[seg] - i * bar
        env = np.minimum(1, tt / 0.5) * np.exp(-tt / 3.0)
        for f in chords[i % 4]:
            y[seg] += 0.05 * env * (np.sin(2 * np.pi * f * tt) + 0.3 * np.sin(4 * np.pi * f * tt))
        for j, f in enumerate(chords[i % 4] + [chords[i % 4][0] * 2]):  # arpeggio plucks
            st = j * bar / 4; pm = (tt >= st)
            p = tt[pm] - st
            y[np.where(seg)[0][pm]] += 0.06 * np.exp(-p * 6) * np.sin(2 * np.pi * f * 2 * p)
    duck = np.where(vo_mask, 0.35, 1.0)
    k = int(0.15 * SR); duck = np.convolve(duck, np.ones(k) / k, mode="same")
    fade = np.minimum(1, np.minimum(t / 0.5, (total - t) / 1.2))
    return (y * duck * fade).astype("float32")

def main(out):
    import numpy as np
    vo = make_vo()
    # stretch scene durations so each voice line fits
    durs = []
    for i, (dur, kind, data, ex) in enumerate(SCENES):
        need = (len(vo[i]) / SR + 0.45) if vo and vo[i] is not None else 0
        durs.append(round(max(dur, need), 2))
    total = sum(durs)
    silent = out.replace(".mp4", "_silent.tmp.mp4")
    proc = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
        "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "veryfast",
        "-crf", "20", "-pix_fmt", "yuv420p", "-movflags", "+faststart", silent], stdin=subprocess.PIPE)
    gt = 0.0
    for (dur0, kind, data, ex), dur in zip(SCENES, durs):
        for fi in range(int(dur * FPS)):
            lt = fi / FPS
            proc.stdin.write(render_scene(kind, data, lt, dur, gt + lt, total, ex).tobytes())
        gt += dur
    proc.stdin.close(); proc.wait()
    music = "--music" in ARGS
    if not vo and not music:
        os.replace(silent, out); print(f"wrote {out} ({total:.1f}s, silent)"); return
    n = int(total * SR); mix = np.zeros(n, dtype="float32"); mask = np.zeros(n, dtype=bool)
    pos = 0.0
    for i, dur in enumerate(durs):
        if vo and vo[i] is not None:
            a = vo[i]; st = int((pos + 0.2) * SR); en = min(n, st + len(a))
            mix[st:en] += a[: en - st]; mask[st:en] = True
        pos += dur
    if music: mix += make_music(total, mask)
    peak = float(np.max(np.abs(mix))) or 1.0
    mix = mix / peak * 0.89
    import soundfile as sf
    wav = out.replace(".mp4", ".tmp.wav"); sf.write(wav, mix, SR)
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", silent, "-i", wav, "-c:v", "copy",
        "-c:a", "aac", "-b:a", "160k", "-shortest", out], check=True)
    os.remove(silent); os.remove(wav)
    print(f"wrote {out} ({total:.1f}s, voiceover={'yes' if vo else 'no'}, music={'yes' if music else 'no'})")

if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "reel.mp4")

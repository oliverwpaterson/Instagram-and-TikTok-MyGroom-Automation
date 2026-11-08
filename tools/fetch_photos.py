"""Download free-to-use real photos (CC0 / public domain only) from Openverse into photos/library/.
Reads photos/queries.txt: one "folder|search words|how many" per line. Skips images already downloaded.
Writes photos/library/credits.json with the source of every image (good practice even when no credit is required).
Run by .github/workflows/fetch-photos.yml (GitHub's servers have open internet access)."""
import io, json, os, sys, time, urllib.parse, urllib.request
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LIB = os.path.join(ROOT, "photos", "library")
CREDITS = os.path.join(LIB, "credits.json")
UA = {"User-Agent": "MyGroomPhotoLibrary/1.0 (+https://www.mygroom.co.uk)"}

def get(url, timeout=30):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()

def main():
    os.makedirs(LIB, exist_ok=True)
    credits = json.load(open(CREDITS)) if os.path.exists(CREDITS) else {}
    lines = [l.strip() for l in open(os.path.join(ROOT, "photos", "queries.txt")) if l.strip() and not l.startswith("#")]
    for line in lines:
        folder, query, n = [p.strip() for p in line.split("|")]
        n = int(n); have = [k for k, v in credits.items() if v["folder"] == folder and v.get("query") == query]
        need = n - len(have)
        if need <= 0: continue
        os.makedirs(os.path.join(LIB, folder), exist_ok=True)
        page, got = 1, 0
        while got < need and page <= 5:
            q = urllib.parse.urlencode({"q": query, "license": "cc0,pdm", "mature": "false", "size": "large", "page_size": 20, "page": page})
            try:
                res = json.loads(get(f"https://api.openverse.org/v1/images/?{q}"))
            except Exception as e:
                print("search failed", query, e); break
            for it in res.get("results", []):
                if got >= need: break
                key = f"{folder}/{it['id']}.jpg"
                if key in credits: continue
                w, h = it.get("width") or 0, it.get("height") or 0
                if min(w, h) < 900: continue
                try:
                    im = Image.open(io.BytesIO(get(it["url"]))).convert("RGB")
                except Exception as e:
                    print("download failed", it.get("url"), e); continue
                if min(im.size) < 900: continue
                im.thumbnail((1800, 1800), Image.LANCZOS)
                im.save(os.path.join(LIB, key), "JPEG", quality=86, optimize=True, progressive=True)
                credits[key] = {"folder": folder, "query": query, "title": it.get("title"), "creator": it.get("creator"),
                                "license": it.get("license"), "license_version": it.get("license_version"),
                                "source": it.get("source"), "page": it.get("foreign_landing_url"), "size": list(im.size)}
                got += 1; print("saved", key, it.get("license"), it.get("title")); time.sleep(0.5)
            page += 1; time.sleep(1)
        json.dump(credits, open(CREDITS, "w"), indent=1, sort_keys=True)
    print("total images:", len(credits))

if __name__ == "__main__":
    main()

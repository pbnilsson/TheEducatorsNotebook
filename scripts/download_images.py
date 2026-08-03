#!/usr/bin/env python3
"""One-time: download all issue images from WordPress into static/images/
and rewrite data/issues.json to reference the local copies.

Run LOCALLY (needs normal internet access): python3 scripts/download_images.py
Safe to re-run; skips files that already exist.
"""
import json, os, urllib.request, urllib.parse

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
IMG_DIR = os.path.join(REPO, "static", "images")
ISSUES = os.path.join(REPO, "data", "issues.json")

def local_name(src):
    path = urllib.parse.urlparse(src).path  # /wp-content/uploads/2026/08/Six-Sentences.png
    parts = [p for p in path.split("/") if p]
    return "-".join(parts[-3:])  # 2026-08-Six-Sentences.png

def main():
    os.makedirs(IMG_DIR, exist_ok=True)
    issues = json.load(open(ISSUES))
    done = fail = 0
    for d, meta in issues.items():
        for img in meta.get("images", []):
            src = img.get("src") or ""
            if not src.startswith("http"):
                continue  # already local
            name = local_name(src)
            dest = os.path.join(IMG_DIR, name)
            if not os.path.exists(dest):
                try:
                    urllib.request.urlretrieve(src, dest)
                except Exception as e:
                    print("FAILED:", src, e)
                    fail += 1
                    continue
            img["src"] = f"/assets/images/{name}"
            done += 1
    json.dump(issues, open(ISSUES, "w"), ensure_ascii=False, indent=1)
    print(f"{done} images localized, {fail} failures. Rebuild and push when done.")

if __name__ == "__main__":
    main()

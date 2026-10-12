"""Record the static HTML animation cards as video segments.

Opens each HTML file in Playwright Chromium at 1920x1080 with a light theme and
captures a continuous video for a fixed wall-clock duration. No model API, no
network beyond file://. Raw webm is preserved under work/video_build/raw/.
"""
from __future__ import annotations
import argparse
import json
import shutil
import sys
import time
from pathlib import Path

ROOT = Path(r"D:\notes\pkuaiagent")
BUILD = ROOT / "work" / "video_build"
RAW = BUILD / "raw"

# name -> (html file, seconds to record)
SEGMENTS = [
    ("seg1_title", BUILD / "html" / "part1_title.html", 30.0),
    ("seg3_results", BUILD / "html" / "part3_results.html", 62.0),
    ("seg4_limits_team", BUILD / "html" / "part4_limits_team.html", 28.0),
]


def main():
    from playwright.sync_api import sync_playwright
    RAW.mkdir(parents=True, exist_ok=True)
    outdir = RAW / "html_segs"
    outdir.mkdir(parents=True, exist_ok=True)
    results = []
    with sync_playwright() as pw:
        browser = pw.chromium.launch(args=["--no-sandbox", "--disable-gpu",
            "--force-color-profile=srgb", "--hide-scrollbars"])
        for name, html, seconds in SEGMENTS:
            tmp = outdir / name
            if tmp.exists():
                shutil.rmtree(tmp)
            tmp.mkdir(parents=True)
            context = browser.new_context(viewport={"width": 1920, "height": 1080},
                record_video_dir=str(tmp), record_video_size={"width": 1920, "height": 1080},
                device_scale_factor=1, color_scheme="light")
            page = context.new_page()
            page.goto(html.as_uri(), wait_until="load")
            page.wait_for_timeout(600)
            t0 = time.monotonic()
            page.wait_for_timeout(int(seconds * 1000))
            video = page.video.path()
            wall = time.monotonic() - t0
            context.close()
            dest = RAW / f"{name}.webm"
            shutil.move(str(video), str(dest))
            shutil.rmtree(tmp, ignore_errors=True)
            results.append({"segment": name, "html": str(html.relative_to(ROOT)),
                            "requested_seconds": seconds, "recorded_seconds": round(wall, 2),
                            "raw": str(dest.relative_to(ROOT))})
            print(json.dumps(results[-1], ensure_ascii=False), flush=True)
        browser.close()
    (raw_receipt := BUILD / "html_segments.json").write_text(
        json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"ok": True, "count": len(results)}, ensure_ascii=False))


if __name__ == "__main__":
    sys.exit(main())

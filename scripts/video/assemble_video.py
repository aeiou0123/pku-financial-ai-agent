"""Assemble the final 04_运行视频.mp4 from recorded segments.

Pipeline:
  1. Speed up the app segment (local compute, no speech) to fit the time budget,
     and letterbox-scale every source to 1920x1080 (white bars).
  2. Normalize each segment to H.264 + silent AAC at a common profile.
  3. concat (demuxer) into one silent video.
  4. Mix in the CC0 background track at low volume with 2s fade-in / 3s fade-out,
     then loudness-normalize the mix to about -20 LUFS.
  5. Attach chapter markers via an FFMETADATA file.

No model API is called. Only ffmpeg is used.
"""
from __future__ import annotations
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(r"D:\notes\pkuaiagent")
BUILD = ROOT / "work" / "video_build"
RAW = BUILD / "raw"
NORM = BUILD / "norm"
FFMPEG = ROOT / ".venv-semifinal" / "Lib" / "site-packages" / "imageio_ffmpeg" / "binaries" / "ffmpeg-win-x86_64-v7.1.exe"
MUSIC = BUILD / "music" / "dunes.mp3"
OUT = ROOT / "deliverables" / "semifinal_20261012" / "饮水思源_Claim2Value" / "04_运行视频.mp4"

# Segment order with per-segment playback speed (video+audio together).
# HTML cards already run at intended pace; the app segment is sped up modestly.
SPEED = {"seg1_title": 1.0, "seg2_app": 1.4, "seg3_results": 1.0, "seg4_limits_team": 1.0}
# Exact output length per segment (seconds), trimming Playwright's buffer tail.
TRIM = {"seg1_title": 30.0, "seg2_app": 150.0, "seg3_results": 62.0, "seg4_limits_team": 30.0}
ORDER = ["seg1_title", "seg2_app", "seg3_results", "seg4_limits_team"]

# Chapter boundaries expressed as (segment, offset-seconds) in the ORIGINAL segment timeline.
# Chapter times are recomputed after speed changes below.
CHAPTERS = [
    ("01 项目与功能说明", "seg1_title", 0.0),
    ("02 真实运行演示", "seg2_app", 0.0),
    ("03 效果与技术依据", "seg3_results", 0.0),
    ("04 局限与适用范围", "seg4_limits_team", 0.0),
]


def run(args):
    proc = subprocess.run(args, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if proc.returncode != 0:
        print("FFMPEG ERROR:\n" + (proc.stderr or "")[-3000:])
        raise SystemExit(proc.returncode)
    return proc


def probe_duration(path: Path) -> float:
    proc = subprocess.run([str(FFMPEG), "-i", str(path)], capture_output=True, text=True, encoding="utf-8", errors="replace")
    for line in proc.stderr.splitlines():
        if "Duration:" in line:
            ts = line.split("Duration:")[1].split(",")[0].strip()
            h, m, s = ts.split(":")
            return int(h) * 3600 + int(m) * 60 + float(s)
    raise RuntimeError(f"no duration for {path}")


def normalize(name: str) -> Path:
    src = RAW / f"{name}.webm"
    dst = NORM / f"{name}.mp4"
    speed = SPEED.get(name, 1.0)
    trim = TRIM.get(name)
    # trim on the source BEFORE speed-up so the target output length is exact
    vf = f"scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2:color=white,fps=30"
    args = [str(FFMPEG), "-y"]
    if trim is not None:
        args += ["-t", f"{trim * speed:.3f}"]
    args += ["-i", str(src)]
    if speed != 1.0:
        vf += f",setpts=PTS/{speed}"
    args += ["-vf", vf, "-an", "-c:v", "libx264", "-preset", "medium", "-crf", "20",
             "-pix_fmt", "yuv420p", "-g", "60"]
    if trim is not None:
        args += ["-t", f"{trim:.3f}"]
    args += [str(dst)]
    run(args)
    return dst


def main():
    NORM.mkdir(parents=True, exist_ok=True)
    durations = {}
    for name in ORDER:
        p = normalize(name)
        d = probe_duration(p)
        durations[name] = d
        print(json.dumps({"segment": name, "seconds": round(d, 2), "speed": SPEED.get(name, 1.0)}, ensure_ascii=False), flush=True)

    # chapter start times in the concatenated timeline
    starts, acc = {}, 0.0
    for name in ORDER:
        starts[name] = acc
        acc += durations[name]
    total = acc
    chapter_rows = [(title, starts[seg]) for title, seg, _ in CHAPTERS]
    print(json.dumps({"total_seconds": round(total, 2), "chapters": [(t, round(s, 2)) for t, s in chapter_rows]}, ensure_ascii=False), flush=True)

    # concat list
    lst = BUILD / "concat_list.txt"
    with lst.open("w", encoding="utf-8") as fh:
        for name in ORDER:
            fh.write(f"file '{NORM / (name + '.mp4')}'\n")

    silent = BUILD / "silent.mp4"
    run([str(FFMPEG), "-y", "-f", "concat", "-safe", "0", "-i", str(lst), "-c", "copy", str(silent)])

    # FFmetadata chapters
    meta = BUILD / "chapters.ffmeta"
    with meta.open("w", encoding="utf-8") as fh:
        fh.write(";FFMETADATA1\ntitle=Claim2Value 研究工作台 运行视频\nartist=饮水思源\n")
        for i, (title, start) in enumerate(chapter_rows):
            end = chapter_rows[i + 1][1] if i + 1 < len(chapter_rows) else total
            fh.write("[CHAPTER]\nTIMEBASE=1/1000\n")
            fh.write(f"START={int(round(start * 1000))}\nEND={int(round(end * 1000))}\n")
            fh.write(f"title={title}\n")

    # mix music + loudnorm, then write chapters
    fade_out_start = max(0.0, total - 3.0)
    af = (f"volume=0.12,afade=t=in:st=0:d=2,afade=t=out:st={fade_out_start:.2f}:d=3,"
          f"loudnorm=I=-20:TP=-2:LRA=11,aresample=48000")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    run([str(FFMPEG), "-y",
         "-i", str(silent),
         "-i", str(MUSIC),
         "-filter_complex", f"[1:a]{af}[a]",
         "-map", "0:v", "-map", "[a]",
         "-map_metadata", "1", "-map_chapters", "-1",
         "-c:v", "copy", "-c:a", "aac", "-b:a", "128k", "-ar", "48000",
         "-t", f"{total:.3f}",
         "-movflags", "+faststart", str(BUILD / "mixed.mp4")])

    # attach chapters (re-mux, copy streams)
    run([str(FFMPEG), "-y", "-i", str(BUILD / "mixed.mp4"), "-i", str(meta),
         "-map", "0", "-map_metadata", "1", "-c", "copy", "-movflags", "+faststart", str(OUT)])

    print(json.dumps({"ok": True, "out": str(OUT), "bytes": OUT.stat().st_size,
                      "total_seconds": round(total, 2),
                      "chapters": [(t, round(s, 2)) for t, s in chapter_rows]}, ensure_ascii=False))


if __name__ == "__main__":
    sys.exit(main())

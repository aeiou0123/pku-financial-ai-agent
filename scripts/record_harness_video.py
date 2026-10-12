"""Record real local workbench interactions with explanatory captions.

Drives harness_app.py on a private port, captures a continuous browser video and
per-chapter screenshots, and writes a receipt. Uses only the bundled synthetic
samples; uploads no private material and calls no model API. Never edits app output.
"""
from __future__ import annotations
import argparse
import hashlib
import importlib.metadata
import json
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PORT = "8511"


def main():
    from playwright.sync_api import sync_playwright
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=False)
    log = (args.out / "app.log").open("w")
    server = subprocess.Popen([sys.executable, "-m", "streamlit", "run", "harness_app.py",
        "--server.headless", "true", "--server.port", PORT, "--server.address", "127.0.0.1",
        "--browser.gatherUsageStats", "false", "--server.maxUploadSize", "20"], cwd=ROOT, stdout=log, stderr=log)
    started = time.monotonic()
    chapters, events = [], []
    try:
        for _ in range(120):
            try:
                with urllib.request.urlopen(f"http://127.0.0.1:{PORT}/_stcore/health", timeout=1) as response:
                    if response.read() == b"ok":
                        break
            except Exception:
                time.sleep(0.25)
        else:
            raise RuntimeError("Local page did not start")
        with sync_playwright() as pw:
            browser = pw.chromium.launch(args=["--no-sandbox", "--disable-dev-shm-usage", "--disable-gpu",
                "--use-gl=angle", "--use-angle=swiftshader", "--enable-unsafe-swiftshader"])
            context = browser.new_context(viewport={"width": 1280, "height": 900},
                record_video_dir=str(args.out), record_video_size={"width": 1280, "height": 900})
            page = context.new_page()
            video_start = time.monotonic()
            page.goto(f"http://127.0.0.1:{PORT}")
            page.get_by_role("radio", name="工作区").wait_for()

            def caption(title, text, seconds=8, chapter=False):
                when = time.monotonic() - video_start
                if chapter:
                    chapters.append({"start_seconds": round(when, 2), "title": title})
                page.evaluate("""({title,text}) => {
                    let el=document.getElementById('recording-explanation');
                    if(!el){el=document.createElement('div');el.id='recording-explanation';
                      el.style.cssText='position:fixed;bottom:20px;left:320px;right:20px;z-index:999999;background:#763b32;color:#fafaf8;padding:12px 20px;font:15px Microsoft YaHei,sans-serif;line-height:1.65;pointer-events:none';
                      document.body.appendChild(el);}
                    el.replaceChildren();const b=document.createElement('strong');b.textContent=title;
                    const t=document.createElement('div');t.textContent=text;el.append(b,t);
                }""", {"title": title, "text": text})
                events.append({"seconds": round(when, 2), "title": title, "caption": text})
                page.screenshot(path=str(args.out / f"frame_{len(events):02d}.png"))
                print(json.dumps({"event": len(events), "title": title}, ensure_ascii=False), flush=True)
                page.wait_for_timeout(seconds * 1000)

            def click_radio(label, wait=2500):
                page.locator('div[data-testid="stRadio"] label', has_text=label).first.click()
                page.wait_for_timeout(wait)

            caption("01 / 项目简介", "Claim2Value 是面向机器人产业链研究的本地工作台，把企业表述、公告原文、口径检查与工程到财务的假设放在同一处。这段是连续实际录屏。", 10, True)
            caption("任务首页", "三个任务：观点审查、财务整理、策略回测。本地计算不需要模型密钥。", 8)
            click_radio("工作区", 3000)
            caption("02 / 实际运行", "进入工作区，先选择合适的任务，再上传材料或载入合成样例。", 10, True)
            load = page.get_by_role("button", name="载入这项任务的样例")
            if load.count():
                load.first.click()
                page.wait_for_timeout(4000)
            caption("财务整理", "载入合成样例后，可以看清每一步需要什么材料、会得到什么结果。", 8)
            click_radio("整理财务数据", 3000)
            caption("导入与提取", "财务整理支持两种输入：从年报 PDF 提取候选，或导入已整理的 16 列长表。", 8)
            click_radio("量化处理与回测", 3000)
            caption("数据体检", "策略回测先用本机规则体检行情数据：列映射、代码格式、日期、重复与因子可得时间，不需要 AI。", 10)
            click_radio("研究成果", 2500) if page.locator('div[data-testid="stRadio"] label', has_text="研究成果").count() else None
            click_radio("教程与示例", 2500)
            caption("03 / 效果依据", "教程与示例提供可离线运行的本地计算演示，结果可下载。引用锚定、报表口径校验与单位校验都在本机规则里执行。", 10, True)
            click_radio("成果记录", 2500)
            caption("成果找回", "成果记录可以搜索最近的本机运行，重新打开报告与快照。", 8)
            click_radio("模型与套餐", 2500)
            caption("模型连接", "需要模型时在侧栏配置自备接口；密钥只留在当前会话，不写入运行目录。", 8)
            caption("04 / 使用范围", "本地计算不需要密钥；扫描件、无标题页与多指标归属仍需人工核对。Windows 已实际验收，Linux 未真机验证，真人试用尚未完成。", 10, True)
            duration = time.monotonic() - video_start
            video_path = page.video.path()
            context.close()
            browser.close()
        files = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in args.out.iterdir()
                 if p.is_file() and p.name != "app.log"}
        receipt = {"status": "CONTINUOUS_REAL_LOCAL_UI_RECORDING", "source_video": Path(video_path).name,
            "duration_seconds_wall": round(duration, 2), "chapters": chapters, "events": events,
            "files_sha256": files, "external_model_calls": 0, "speedup": False,
            "browser_automation": True, "human_trial": False,
            "environment": {name: importlib.metadata.version(name) for name in ("streamlit", "numpy", "pandas", "playwright")},
            "app_sha256": hashlib.sha256((ROOT / "harness_app.py").read_bytes()).hexdigest(),
            "recorder_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            "elapsed_seconds_including_startup": round(time.monotonic() - started, 2)}
        (args.out / "recording_receipt.json").write_text(json.dumps(receipt, ensure_ascii=False, indent=2), encoding="utf-8")
        print(json.dumps({"ok": True, "video": Path(video_path).name, "duration": round(duration, 2)}, ensure_ascii=False))
    finally:
        server.terminate()
        server.wait(timeout=15)
        log.close()


if __name__ == "__main__":
    main()

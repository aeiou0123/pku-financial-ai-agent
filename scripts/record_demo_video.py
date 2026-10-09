"""Record actual local Streamlit interactions with explicit explanatory captions.

Requires Playwright, a Chromium executable, and its video encoder. Never edits
the app's outputs. The recording remains uncut and is kept with input/download
evidence; MP4 conversion and chapter metadata are separate steps.
"""
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


def main():
    from playwright.sync_api import sync_playwright
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--chromium", required=True)
    p.add_argument("--out", required=True, type=Path)
    a = p.parse_args()
    a.out.mkdir(parents=True, exist_ok=False)
    log = (a.out / "app.log").open("w")
    server = subprocess.Popen([sys.executable, "-m", "streamlit", "run", "app.py",
        "--server.headless", "true", "--server.port", "8507", "--server.address", "127.0.0.1",
        "--browser.gatherUsageStats", "false"], cwd=ROOT, stdout=log, stderr=log)
    started = time.monotonic()
    chapters, events = [], []
    try:
        for _ in range(120):
            try:
                with urllib.request.urlopen("http://127.0.0.1:8507/_stcore/health", timeout=1) as response:
                    if response.read() == b"ok":
                        break
            except Exception:
                time.sleep(0.25)
        else:
            raise RuntimeError("Local page did not start")
        with sync_playwright() as pw:
            browser = pw.chromium.launch(executable_path=a.chromium, args=["--no-sandbox",
                "--disable-dev-shm-usage", "--disable-gpu", "--use-gl=angle",
                "--use-angle=swiftshader", "--enable-unsafe-swiftshader"])
            context = browser.new_context(viewport={"width": 1280, "height": 900},
                record_video_dir=str(a.out), record_video_size={"width": 1280, "height": 900})
            page = context.new_page()
            video_start = time.monotonic()
            page.goto("http://127.0.0.1:8507")
            page.get_by_role("button", name="运行示例", exact=True).wait_for()

            def caption(title, text, seconds=8, chapter=False):
                when = time.monotonic() - video_start
                if chapter:
                    chapters.append({"start_seconds": when, "title": title})
                page.evaluate("""({title,text}) => {
                    let el=document.getElementById('recording-explanation');
                    if(!el){el=document.createElement('div');el.id='recording-explanation';
                      el.style.cssText='position:fixed;top:0;left:0;right:0;z-index:999999;background:#102e42;color:white;padding:12px 24px;font:19px sans-serif;line-height:1.5;pointer-events:none';
                      document.body.appendChild(el);}
                    el.replaceChildren();const b=document.createElement('strong');b.textContent=title;
                    const t=document.createElement('div');t.textContent=text;el.append(b,t);
                }""", {"title": title, "text": text})
                events.append({"seconds": when, "title": title, "caption": text})
                page.screenshot(path=str(a.out / f"frame_{len(events):02d}.png"))
                print(json.dumps({"event": len(events), "title": title}), flush=True)
                page.wait_for_timeout(seconds * 1000)

            caption("第一章 项目与功能", "Claim2Value 机器人产业链声明核查。以下为2026年10月9日本地页面的连续真实操作，字幕用于说明。", 12, True)
            page.get_by_text("当前能力与适用范围", exact=True).click()
            caption("项目范围", "自研规则、证据记录、经济映射与财务原型。页面使用Streamlit，不调用Qwen、Kimi或其他外部模型。", 10)
            page.get_by_role("button", name="运行示例", exact=True).click()
            page.get_by_text("已完成的核查记录", exact=True).wait_for()
            caption("第二章 真实运行演示", "绿的谐波示例：实际核查结果提示测试条件缺失。来源和定位仍需人工核原文。", 12, True)
            page.get_by_role("tab", name="分析与情景", exact=True).click()
            page.get_by_text("财务三情景（单位：十亿元人民币）", exact=True).scroll_into_view_if_needed()
            caption("绿的谐波财务情景", "表格来自本次运行。固定参数用于敏感性分析，不表示已识别技术声明对收入或估值的因果效应。", 12)
            page.get_by_role("tab", name="导出记录", exact=True).click()
            with page.expect_download() as download:
                page.get_by_role("button", name="下载结构化记录 JSON", exact=True).click()
            download.value.save_as(str(a.out / "green_actual_download.json"))
            caption("报告导出", "已通过页面下载本次JSON，记录输入、判断与中间状态。当前函数耗时不含浏览器交互或人工阅读。", 8)
            combo = page.get_by_role("combobox")
            combo.scroll_into_view_if_needed()
            combo.click()
            # Keyboard selection also works with the newer React Aria wrapper.
            combo.press("ArrowDown")
            combo.press("Enter")
            page.get_by_text("环动科技下游客户已覆盖埃斯顿、埃夫特、卡诺普、爱仕达旗下钱江机器人等知名机器人制造商", exact=True).wait_for()
            page.get_by_role("button", name="运行示例", exact=True).click()
            page.get_by_text("记录模式：preset_scenario_demo · 双环传动/环动科技", exact=False).wait_for()
            page.get_by_role("tab", name="分析与情景", exact=True).click()
            page.get_by_text("财务三情景（单位：十亿元人民币）", exact=True).scroll_into_view_if_needed()
            caption("双环传动切换与重算", "公司输入与情景参数随切换变化。客户覆盖需要进一步核实订单、收入及统计口径。", 12)
            page.get_by_role("tab", name="导出记录", exact=True).click()
            with page.expect_download() as download:
                page.get_by_role("button", name="下载结构化记录 JSON", exact=True).click()
            download.value.save_as(str(a.out / "shuanghuan_actual_download.json"))
            page.get_by_text("自定义核查", exact=True).click()
            page.get_by_role("textbox", name="待核查声明", exact=True).fill("公司产品适用于机器人")
            page.get_by_role("button", name="核查声明", exact=True).click()
            # A previous record can still exist while Streamlit reruns the form.
            # Wait for this newly submitted claim, not the unchanged heading.
            page.get_by_text("公司产品适用于机器人", exact=True).wait_for()
            page.get_by_text("证据不足或规则无法判断", exact=True).wait_for()
            caption("自定义输入与缺证处理", "本次确实修改输入，并留空证据。系统拒答，不为此输入生成财务估值。", 12)
            page.get_by_role("tab", name="分析与情景", exact=True).click()
            caption("第三章 效果与技术依据", "既有开发库87/98标签命中，来自19个家族，非独立业务准确率。250项软件测试通过，失败记录保留。", 12, True)
            page.get_by_role("tab", name="导出记录", exact=True).click()
            with page.expect_download() as download:
                page.get_by_role("button", name="下载结构化记录 JSON", exact=True).click()
            download.value.save_as(str(a.out / "missing_actual_download.json"))
            caption("技术题证据", "首轮2020年扣费Sharpe为−0.091。12个新候选未达到开发期替换标准，保留原名单；比赛测试收益未知。", 12)
            page.get_by_text("当前能力与适用范围", exact=True).scroll_into_view_if_needed()
            caption("第四章 局限与适用范围", "适合研究者辅助核查文本。无实时检索、PDF上传或在线语义模型；真人试用、真实财务样本与Windows验收待完成。", 15, True)
            duration = time.monotonic() - video_start
            video_path = page.video.path()
            context.close()
            browser.close()
        files = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in a.out.iterdir()
                 if p.is_file() and p.name != "app.log"}
        receipt = {"status": "CONTINUOUS_REAL_LOCAL_UI_RECORDING", "source_video": Path(video_path).name,
            "duration_seconds_wall": duration, "chapters": chapters, "events": events,
            "files_sha256": files, "external_model_calls": 0, "speedup": False,
            "browser_automation": True, "human_trial": False,
            "environment": {name: importlib.metadata.version(name)
                            for name in ("streamlit", "numpy", "pandas", "playwright")},
            "app_sha256": hashlib.sha256((ROOT / "app.py").read_bytes()).hexdigest(),
            "recorder_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            "elapsed_seconds_including_startup": time.monotonic() - started}
        (a.out / "recording_receipt.json").write_text(json.dumps(receipt, ensure_ascii=False, indent=2))
    finally:
        server.terminate()
        server.wait(timeout=15)
        log.close()


if __name__ == "__main__":
    main()

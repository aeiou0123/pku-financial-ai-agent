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
    p.add_argument("--verification", required=True, type=Path)
    a = p.parse_args()
    verification = json.loads(a.verification.read_text(encoding="utf-8"))
    if verification.get("technical_reproduction") != "PASS" or not verification.get("software_tests_passed"):
        raise ValueError("Actual test and technical reproduction evidence is required before recording")
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
            page.get_by_role("heading", name="绿的谐波", exact=True).wait_for()
            page.get_by_text("购建固定资产、无形资产和其他长期资产支付的现金", exact=True).first.wait_for()

            def caption(title, text, seconds=8, chapter=False):
                when = time.monotonic() - video_start
                if chapter:
                    chapters.append({"start_seconds": when, "title": title})
                page.evaluate("""({title,text}) => {
                    let el=document.getElementById('recording-explanation');
                    if(!el){el=document.createElement('div');el.id='recording-explanation';
                      el.style.cssText='position:fixed;bottom:20px;left:320px;right:20px;z-index:999999;background:#29493d;color:#fafbf5;padding:12px 20px;font:15px Microsoft YaHei,sans-serif;line-height:1.65;pointer-events:none';
                      document.body.appendChild(el);}
                    el.replaceChildren();const b=document.createElement('strong');b.textContent=title;
                    const t=document.createElement('div');t.textContent=text;el.append(b,t);
                }""", {"title": title, "text": text})
                events.append({"seconds": when, "title": title, "caption": text})
                page.screenshot(path=str(a.out / f"frame_{len(events):02d}.png"))
                print(json.dumps({"event": len(events), "title": title}), flush=True)
                page.wait_for_timeout(seconds * 1000)

            caption("01 / 项目简介", "Claim2Value把机器人产业链的财务记录、企业声明和测算假设放在一个工作台里。这是连续实际录屏，由浏览器自动操作。", 10, True)
            page.get_by_text("2024比较数来自2025年报，披露日为2026-04-23。这些数据不能当作2024年当时已经可得的信息。", exact=True).scroll_into_view_if_needed()
            caption("年度财务与原件", "两年数据按指标并排。34条原值取自年报，2024比较数实际披露于2026年4月23日，不能当作2024实时样本。", 8)
            with page.expect_download() as download:
                page.get_by_role("button", name="下载记录 · JSON", exact=True).click()
            download.value.save_as(str(a.out / "financial_actual_download.json"))
            page.get_by_test_id("stSidebar").get_by_text("情景测算", exact=True).click()
            page.get_by_role("button", name="计算情景", exact=True).click()
            page.get_by_role("heading", name="遗漏限定条件", exact=True).wait_for()
            caption("02 / 实际操作", "绿的谐波的减重声明没有保留原文中的同等出力条件。页面显示原文、出处和仍需核实的内容。", 10, True)
            page.get_by_role("tab", name="测算与假设", exact=True).click()
            page.get_by_text("企业价值（亿元）", exact=True).scroll_into_view_if_needed()
            caption("固定假设测算", "企业价值统一用亿元。这里比较基准、上行和下行假设；不是股价或已经证实的技术收益。", 8)
            page.get_by_role("tab", name="下载报告", exact=True).click()
            with page.expect_download() as download:
                page.get_by_role("button", name="下载记录 · JSON", exact=True).click()
            download.value.save_as(str(a.out / "green_actual_download.json"))
            combo = page.get_by_role("combobox", name="研究案例")
            combo.scroll_into_view_if_needed()
            combo.click()
            # Keyboard selection also works with the newer React Aria wrapper.
            combo.press("ArrowDown")
            combo.press("Enter")
            page.get_by_text("环动科技下游客户已覆盖埃斯顿、埃夫特、卡诺普、爱仕达旗下钱江机器人等知名机器人制造商", exact=True).wait_for()
            page.get_by_role("button", name="计算情景", exact=True).click()
            page.get_by_role("tab", name="测算与假设", exact=True).click()
            page.get_by_text("企业价值（亿元）", exact=True).scroll_into_view_if_needed()
            caption("切换公司", "双环传动按自己的固定参数重算。客户覆盖不直接证明订单、收入或利润兑现。", 8)
            page.get_by_role("tab", name="下载报告", exact=True).click()
            with page.expect_download() as download:
                page.get_by_role("button", name="下载记录 · JSON", exact=True).click()
            download.value.save_as(str(a.out / "shuanghuan_actual_download.json"))
            page.get_by_test_id("stSidebar").get_by_text("财务记录", exact=True).click()
            company = page.get_by_role("combobox", name="公司", exact=True)
            company.click(); company.press("ArrowDown"); company.press("ArrowDown"); company.press("Enter")
            page.get_by_text("尚未收录已核对的公开财务记录。", exact=True).wait_for()
            caption("资料缺口", "步科尚没有完成原页核对的公开财务样本。页面明确保留缺口，不填入猜测的数值。", 8)
            page.get_by_test_id("stSidebar").get_by_text("声明核查", exact=True).click()
            page.get_by_role("textbox", name="企业声明", exact=True).fill("公司产品适用于机器人")
            page.get_by_role("button", name="核查声明", exact=True).click()
            # A previous record can still exist while Streamlit reruns the form.
            # Wait for this newly submitted claim, not the unchanged heading.
            page.get_by_text("公司产品适用于机器人", exact=True).wait_for()
            page.get_by_role("heading", name="缺少证据", exact=True).wait_for()
            caption("缺少引用原文", "输入一条声明，证据留空，系统不作判断，也不为这条输入生成估值。", 8)
            page.get_by_role("tab", name="下载报告", exact=True).click()
            with page.expect_download() as download:
                page.get_by_role("button", name="下载记录 · JSON", exact=True).click()
            download.value.save_as(str(a.out / "missing_actual_download.json"))
            caption("03 / 效果依据", f"开发题87/98命中，11条失败保留；这不是独立业务准确率。本次{verification['software_tests_passed']}项软件检查通过。", 10, True)
            caption("技术题复现", "冻结名单24,240行，Windows独立复现哈希一致。2020扣费Sharpe为负；比赛测试收益未知。", 8)
            page.get_by_test_id("stSidebar").get_by_text("使用说明", exact=True).click()
            caption("04 / 使用范围", "当前只检查已有规则，不做联网检索或完整语义判断。CSMAR字段定义、四条技术声明和真人试用仍需补齐。", 10, True)
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
            "presentation_sha256": {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest()
                for name in ("src/review_ui.py", "src/financial_evidence.py")},
            "recorder_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            "elapsed_seconds_including_startup": time.monotonic() - started}
        (a.out / "recording_receipt.json").write_text(json.dumps(receipt, ensure_ascii=False, indent=2), encoding="utf-8")
    finally:
        server.terminate()
        server.wait(timeout=15)
        log.close()


if __name__ == "__main__":
    main()

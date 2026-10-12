"""Probe the live app UI: dump radio labels, buttons and the history record list.

Read-only navigation. Does not click any model button and never reads a key.
"""
from __future__ import annotations
import json
import sys
from pathlib import Path

URL = "http://127.0.0.1:8510"


def click_radio(page, label, wait=3000):
    page.locator('div[data-testid="stRadio"] label', has_text=label).first.click(force=True)
    page.wait_for_timeout(wait)


def dump(page, label):
    radios = page.locator('div[data-testid="stRadio"] label').all_inner_texts()
    buttons = page.locator('button').all_inner_texts()
    print(json.dumps({"where": label, "radios": radios,
                      "buttons": [b for b in buttons if b.strip()][:40]}, ensure_ascii=False), flush=True)


def main():
    from playwright.sync_api import sync_playwright
    with sync_playwright() as pw:
        browser = pw.chromium.launch(args=["--no-sandbox", "--disable-gpu"])
        page = browser.new_context(viewport={"width": 1600, "height": 1000}).new_page()
        page.goto(URL, wait_until="load")
        page.wait_for_timeout(6000)
        dump(page, "start")

        click_radio(page, "成果记录", 4000)
        # search box (history page placeholder)
        boxes = page.get_by_placeholder("输入文件名、研究问题或记录编号")
        print("search boxes:", boxes.count(), flush=True)
        if boxes.count():
            boxes.first.fill("505c5491ea")
            page.wait_for_timeout(3500)
        print("after search body has id:", "505c5491ea" in page.inner_text("body"), flush=True)
        # dump visible text around the record list
        body = page.inner_text("body")
        i = body.find("选择研究记录")
        print("HISTORY SNIPPET >>>", body[max(0,i-200):i+400].replace("\n", " | "), flush=True)
        page.screenshot(path="work/video_build/checks/probe_history.png", full_page=False)

        # workspace radios
        click_radio(page, "工作区", 4000)
        dump(page, "workspace_financial")
        click_radio(page, "检查研究观点", 3000)
        dump(page, "industry_opinion")
        click_radio(page, "量化处理与回测", 4000)
        dump(page, "quant")
        browser.close()


if __name__ == "__main__":
    sys.exit(main())

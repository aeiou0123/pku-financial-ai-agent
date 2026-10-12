"""Second probe: history search with Enter, and file-upload selector check."""
from __future__ import annotations
import json
import sys

URL = "http://127.0.0.1:8510"


def click_radio(page, label, wait=3000):
    page.locator('div[data-testid="stRadio"] label', has_text=label).first.click(force=True)
    page.wait_for_timeout(wait)


def main():
    from playwright.sync_api import sync_playwright
    with sync_playwright() as pw:
        browser = pw.chromium.launch(args=["--no-sandbox", "--disable-gpu"])
        page = browser.new_context(viewport={"width": 1600, "height": 1000}).new_page()
        page.goto(URL, wait_until="load")
        page.wait_for_timeout(6000)
        click_radio(page, "成果记录", 4000)
        box = page.get_by_placeholder("输入文件名、研究问题或记录编号").first
        box.fill("505c5491ea")
        box.press("Enter")
        page.wait_for_timeout(4000)
        body = page.inner_text("body")
        print("found target id:", "505c5491ea" in body, flush=True)
        i = body.find("在最近200条记录中找到")
        print("count line:", body[i:i+40], flush=True)
        i2 = body.find("选择研究记录")
        print("SELECT SNIPPET >>>", body[i2:i2+260].replace("\n", " | "), flush=True)
        page.screenshot(path="work/video_build/checks/probe_history2.png")

        # upload element check on workspace financial
        click_radio(page, "工作区", 3000)
        click_radio(page, "整理财务数据", 3000)
        files = page.locator('input[type="file"]')
        print("file inputs:", files.count(), flush=True)
        browser.close()


if __name__ == "__main__":
    sys.exit(main())

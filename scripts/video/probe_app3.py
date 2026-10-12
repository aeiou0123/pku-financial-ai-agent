"""Third probe: open the record's 报告正文 tab and dump visible text."""
from __future__ import annotations
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
        # click report tab
        tab = page.locator('[role="tab"]', has_text="报告正文")
        print("report tab count:", tab.count(), flush=True)
        if tab.count():
            tab.first.click(force=True)
            page.wait_for_timeout(4000)
        body = page.inner_text("body")
        i = body.find("项目")
        print("REPORT SNIPPET >>>", body[i:i+1500].replace("\n", " | "), flush=True)
        page.screenshot(path="work/video_build/checks/probe_report.png", full_page=True)
        browser.close()


if __name__ == "__main__":
    sys.exit(main())

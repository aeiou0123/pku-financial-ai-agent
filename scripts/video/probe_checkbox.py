"""Probe: can we reliably tick a Streamlit checkbox by label text?"""
from __future__ import annotations
import sys

URL = "http://127.0.0.1:8510"
FIN_CSV = r"D:\notes\pkuaiagent\work\real_case_validation_20261011\financial_reference.csv"
FIN_PDF = r"D:\notes\pkuaiagent\work\real_case_validation_20261011\originals\green_2024_annual.pdf"


def click_radio(page, label, wait=2500):
    page.locator('div[data-testid="stRadio"] label', has_text=label).first.click(force=True)
    page.wait_for_timeout(wait)


def check_by_text(page, text):
    lab = page.locator('label', has_text=text).first
    inp = lab.locator('input[type="checkbox"]').first
    inp.check(force=True)
    page.wait_for_timeout(800)
    return inp.is_checked()


def main():
    from playwright.sync_api import sync_playwright
    with sync_playwright() as pw:
        b = pw.chromium.launch(args=["--no-sandbox", "--disable-gpu"])
        page = b.new_context(viewport={"width": 1600, "height": 1000}).new_page()
        page.goto(URL, wait_until="load")
        page.wait_for_timeout(6000)
        click_radio(page, "工作区", 3000)
        click_radio(page, "整理财务数据", 2500)
        page.locator('input[type="file"]').first.set_input_files([FIN_CSV, FIN_PDF])
        page.wait_for_timeout(5000)
        click_radio(page, "导入已整理财务长表", 3000)
        page.get_by_role("button", name="读取财务长表").first.click(force=True)
        page.wait_for_timeout(4500)
        print("labels with 核对:", page.locator('label', has_text="我已对照原件核对字段").count(), flush=True)
        ok = check_by_text(page, "我已对照原件核对字段")
        print("after check -> is_checked:", ok, flush=True)
        page.get_by_role("button", name="校验并生成财务成果").first.click(force=True)
        page.wait_for_timeout(6000)
        body = page.inner_text("body")
        print("has 标准化记录:", "已生成" in body or "标准化记录" in body, flush=True)
        i = body.find("已生成")
        print("SNIP:", body[max(0,i-60):i+120].replace("\n", " | "), flush=True)
        # now look for the earnings bridge button
        page.wait_for_timeout(2000)
        btns = page.get_by_role("button").all_inner_texts()
        print("生成盈利变化研究底稿 present:", any("生成盈利变化研究底稿" in x for x in btns), flush=True)
        print("buttons:", [x for x in btns if x.strip()][:20], flush=True)
        b.close()


if __name__ == "__main__":
    sys.exit(main())

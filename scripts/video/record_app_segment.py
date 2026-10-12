"""Record the real Claim2Value workbench on the live port with caption overlay.

Drives only LOCAL computation paths (read-only history browsing, local research
template, long-table import, data health check, local backtest, DCF sensitivity).
No model button is ever clicked, no API key is read, and nothing under the
deliverable directory is touched. Raw footage is kept under work/video_build/raw/.
"""
from __future__ import annotations
import json
import shutil
import sys
import time
from pathlib import Path

ROOT = Path(r"D:\notes\pkuaiagent")
BUILD = ROOT / "work" / "video_build"
RAW = BUILD / "raw"
URL = "http://127.0.0.1:8510"
FIN_CSV = ROOT / "work" / "real_case_validation_20261011" / "financial_reference.csv"
FIN_PDF = ROOT / "work" / "real_case_validation_20261011" / "originals" / "green_2024_annual.pdf"

events = []
video_start = 0.0


def click_radio(page, label, wait=2000):
    page.locator('div[data-testid="stRadio"] label', has_text=label).first.click(force=True)
    page.wait_for_timeout(wait)


def click_button(page, name, wait=2500, nth=0):
    page.get_by_role("button", name=name).nth(nth).click(force=True)
    page.wait_for_timeout(wait)


def click_checkbox(page, text, wait=1200):
    """Tick a Streamlit checkbox by its visible label text via Playwright's native check."""
    lab = page.locator('label', has_text=text).first
    inp = lab.locator('input[type="checkbox"]').first
    inp.check(force=True)
    page.wait_for_timeout(wait)
    return inp.is_checked()


def is_checked(page, text):
    return page.evaluate("""(t) => {
        const labels=[...document.querySelectorAll('label')];
        const el=labels.find(l=>l.innerText.includes(t));
        if(!el) return null;
        const i=el.querySelector('input'); return i? i.checked : null;
    }""", text)


def fill_input(page, placeholder, value, wait=500):
    try:
        page.get_by_placeholder(placeholder).first.fill(value)
        page.wait_for_timeout(wait)
        return True
    except Exception:
        return False


def caption(page, title, text, seconds=6):
    when = round(time.monotonic() - video_start, 2)
    page.evaluate("""({title,text}) => {
        let el=document.getElementById('recording-explanation');
        if(!el){el=document.createElement('div');el.id='recording-explanation';
          el.style.cssText='position:fixed;bottom:22px;left:360px;right:26px;z-index:999999;background:#763b32;color:#fafaf8;padding:16px 26px;border-radius:10px;font:26px Microsoft YaHei,sans-serif;line-height:1.6;pointer-events:none;box-shadow:0 4px 18px rgba(0,0,0,.25)';
          document.body.appendChild(el);}
        el.replaceChildren();
        const b=document.createElement('strong');b.textContent=title;b.style.cssText='display:block;font-size:27px;margin-bottom:6px';
        const t=document.createElement('div');t.textContent=text;
        el.append(b,t);
    }""", {"title": title, "text": text})
    events.append({"seconds": when, "title": title, "text": text})
    print(json.dumps({"caption": title, "at": when}, ensure_ascii=False), flush=True)
    page.wait_for_timeout(int(seconds * 1000))


def scroll_to(page, needle):
    try:
        page.get_by_text(needle, exact=False).first.scroll_into_view_if_needed(timeout=4000)
        page.wait_for_timeout(300)
    except Exception:
        pass


def reset(page, wait=6000):
    """Reload to a fresh session so prior uploads no longer occupy the workspace."""
    page.goto(URL, wait_until="load")
    page.wait_for_timeout(wait)


def run_script(page):
    # ---- 02a 成果记录: the real measured run (budget ~12s) ------------------
    caption(page, "02 真实运行演示 · 成果记录",
            "先看本机保存的一次真实运行：2026-10-12 15:18 的财务整理记录。", 4)
    click_radio(page, "成果记录", 3000)
    box = page.get_by_placeholder("输入文件名、研究问题或记录编号").first
    box.fill("505c5491ea")
    box.press("Enter")
    page.wait_for_timeout(3000)
    caption(page, "定位这次运行",
            "编号 20261012_151837_505c5491ea；输入 green_2024_annual.pdf（苏州绿的谐波 2024 年年报）。", 4)
    tab = page.locator('[role="tab"]', has_text="下载文件")
    if tab.count():
        tab.first.click(force=True)
        page.wait_for_timeout(2000)
    caption(page, "真实计量的运行数据",
            "本次实跑：348.5 秒、3 次调用、17,932 token；分 2 批完成，收下 30 条财务候选。", 6)

    # ---- 02b 财务整理 (all local, budget ~64s) -----------------------------
    reset(page)
    click_radio(page, "工作区", 3000)
    click_radio(page, "整理财务数据", 2200)
    caption(page, "02b 财务整理 · 本地计算", "以下全部为本地计算，不调用任何模型接口。", 3)
    page.locator('input[type="file"]').first.set_input_files([str(FIN_CSV), str(FIN_PDF)])
    page.wait_for_timeout(5000)
    caption(page, "上传两份材料", "同时上传 16 列财务长表，和它引用的 PDF 原件 green_2024_annual.pdf。", 3)
    click_radio(page, "导入已整理财务长表", 3000)
    click_button(page, "读取财务长表", 4000)
    caption(page, "读取结果", "本机读取 24 行长表（2024 与 2023 两期、12 个指标），PDF 已在本地解析。", 4)
    scroll_to(page, "我已对照原件核对字段")
    click_checkbox(page, "我已对照原件核对字段", 1200)
    caption(page, "核对确认", "字段仍可人工编辑；确认口径、单位与披露日期后勾选核对确认。", 4)
    click_button(page, "校验并生成财务成果", 4500)
    caption(page, "标准化结果", "本机校验生成 24 条标准化记录；来源真实性仍以原件核对为准。", 4)
    scroll_to(page, "生成盈利变化研究底稿")
    click_button(page, "生成盈利变化研究底稿", 4500)
    caption(page, "盈利变化底稿", "对比 2023 与 2024 合并口径：收入、毛利率与其余项目各自的贡献。", 6)
    scroll_to(page, "变化（元）")
    page.wait_for_timeout(500)
    click_checkbox(page, "添加现金流估值", 2000)
    fill_input(page, "例如：1000000，1100000，1200000，1300000，1400000", "120000000,135000000,150000000,165000000,180000000")
    click_checkbox(page, "这些现金流、折现率和增长率是我确认的假设", 1000)
    click_button(page, "计算假设 DCF", 4500)
    caption(page, "DCF 敏感性",
            "五年自由现金流由操作人明确输入；本机计算假设企业价值与折现率、增长率的敏感性。", 6)
    scroll_to(page, "假设企业价值")
    page.wait_for_timeout(1500)

    # ---- 02c 观点审查 (industry, local template, budget ~22s) --------------
    reset(page)
    click_radio(page, "工作区", 3000)
    click_radio(page, "检查研究观点", 3000)
    caption(page, "02c 观点审查 · 本地模板", "切到检查研究观点，把观点拆成待检查条件；这一步走本地模板，不调用模型。", 3)
    click_button(page, "载入这项任务的样例", 4000)
    fill_input(page, "例如：某公司；与原件名称一致", "公司甲")
    fill_input(page, "例如：耳机、减速器", "减速器")
    dates = page.get_by_placeholder("YYYY-MM-DD；未知则留空")
    for i, d in enumerate(["2026-01-01", "2026-02-01"]):
        try:
            dates.nth(i).fill(d)
            page.wait_for_timeout(300)
        except Exception:
            pass
    page.wait_for_timeout(1200)
    click_checkbox(page, "已核对日期和适用范围", 800)
    page.wait_for_timeout(400)
    click_checkbox(page, "已核对日期和适用范围 · synthetic_industry_counterevidence", 1200)
    caption(page, "核对材料", "登记每份材料的披露日期与适用范围；日期确认与来源确认是两步。", 3)
    click_button(page, "使用本地研究模板（不调用模型）", 4000)
    caption(page, "待检查条件表", "本地清单给出逐条待检查条件与检索词，覆盖技术、产能、需求、价格与成本，可人工增删。", 6)
    scroll_to(page, "待检查条件")
    page.wait_for_timeout(1200)

    # ---- 02d 策略回测 (quant, local, budget ~30s) --------------------------
    reset(page)
    click_radio(page, "量化处理与回测", 4000)
    caption(page, "02d 策略回测 · 本地计算", "研究方向切到量化处理与回测；同样走本地计算，先做数据体检。", 3)
    click_button(page, "载入这项任务的样例", 4000)
    click_button(page, "检查数据（不调用模型）", 4500)
    caption(page, "数据体检", "本机检查列映射、代码格式、日期、重复与因子可得时间；体检不改数据、不需模型。", 5)
    scroll_to(page, "检查数据")
    page.wait_for_timeout(600)
    click_checkbox(page, "我确认价格已经复权", 1000)
    click_button(page, "校验数据并运行回测", 7000)
    caption(page, "回测结果", "本机计算净收益、最大回撤、计入收益的交易日，并给出同费率基准净值曲线。", 6)
    scroll_to(page, "样本净收益")
    page.wait_for_timeout(1500)
    try:
        page.get_by_text("比较多组参数与成本（可选）", exact=False).first.click(force=True)
        page.wait_for_timeout(2000)
    except Exception:
        pass
    click_checkbox(page, "我预先声明这些参数", 1000)
    click_button(page, "运行策略诊断", 7000)
    caption(page, "参数诊断", "在共同区间比较全部声明参数组，保留失败组与已查看样本登记。", 5)
    scroll_to(page, "共同持仓收益区间")
    page.wait_for_timeout(1500)
    caption(page, "本地演示结束", "以上财务整理、盈利变化、DCF、数据体检、回测与参数诊断均在本机完成，未调用模型。", 4)


def main():
    from playwright.sync_api import sync_playwright
    global video_start
    RAW.mkdir(parents=True, exist_ok=True)
    tmp = RAW / "app_seg_tmp"
    if tmp.exists():
        shutil.rmtree(tmp)
    tmp.mkdir(parents=True)

    with sync_playwright() as pw:
        browser = pw.chromium.launch(args=["--no-sandbox", "--disable-dev-shm-usage", "--disable-gpu",
            "--force-color-profile=srgb", "--hide-scrollbars", "--enable-unsafe-swiftshader"])
        context = browser.new_context(viewport={"width": 1600, "height": 1000},
            record_video_dir=str(tmp), record_video_size={"width": 1600, "height": 1000},
            device_scale_factor=1, color_scheme="light")
        page = context.new_page()
        page.goto(URL, wait_until="load")
        page.wait_for_timeout(7000)
        video_start = time.monotonic()
        try:
            run_script(page)
        except Exception as exc:
            print(json.dumps({"error": type(exc).__name__, "msg": str(exc)[:400]}, ensure_ascii=False), flush=True)
        wall = round(time.monotonic() - video_start, 2)
        video_path = page.video.path()
        context.close()
        browser.close()

    dest = RAW / "seg2_app.webm"
    shutil.move(str(video_path), str(dest))
    shutil.rmtree(tmp, ignore_errors=True)
    receipt = {"segment": "seg2_app", "wall_seconds": wall, "raw": str(dest.relative_to(ROOT)),
               "events": events, "external_model_calls": 0, "url": URL}
    (BUILD / "app_segment.json").write_text(json.dumps(receipt, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"ok": True, "wall": wall, "raw": str(dest)}, ensure_ascii=False))


if __name__ == "__main__":
    sys.exit(main())

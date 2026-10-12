# -*- coding: utf-8 -*-
"""Update 03_展示稿.pptx so the deck matches the current workbench and evidence.

Edits text in place, preserving the deck layout, fonts and geometry. Facts come
from work/claude_review_20261012/financial_rerun_receipt.json and the page-level
reference table; nothing is invented here.
"""
from __future__ import annotations
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DECK = ROOT / "deliverables/semifinal_20261012/饮水思源_Claim2Value/03_展示稿.pptx"
OLD_DATE, NEW_DATE = "2026-10-10", "2026-10-12"


def set_text(shape, text):
    """Replace a text frame's content, keeping the first run's formatting."""
    frame = shape.text_frame
    paragraph = frame.paragraphs[0]
    if paragraph.runs:
        paragraph.runs[0].text = text
        for run in paragraph.runs[1:]:
            run._element.getparent().remove(run._element)
    else:
        paragraph.add_run(text)
    for extra in frame.paragraphs[1:]:
        extra._element.getparent().remove(extra._element)


def set_bullets(shape, lines):
    """Rewrite a multi-line body frame, cloning the first paragraph's formatting."""
    frame = shape.text_frame
    first = frame.paragraphs[0]
    template = first._p
    for extra in frame.paragraphs[1:]:
        extra._element.getparent().remove(extra._element)
    set_text(shape, lines[0])
    for line in lines[1:]:
        new = template.makeelement(template.tag, {})
        template.addnext(new)
        from pptx.text.text import _Paragraph
        paragraph = _Paragraph(new, frame)
        paragraph.add_run().text = line


def replace_cell(table, row, col, text):
    cell = table.cell(row, col)
    paragraph = cell.text_frame.paragraphs[0]
    if paragraph.runs:
        paragraph.runs[0].text = text
        for run in paragraph.runs[1:]:
            run._element.getparent().remove(run._element)
    else:
        paragraph.add_run(text)


def main():
    from pptx import Presentation
    deck = Presentation(str(DECK))
    slides = list(deck.slides)

    # Slide 1 — cover
    for shape in slides[0].shapes:
        if shape.has_text_frame and "机器人产业链声明核查" in shape.text_frame.text:
            set_text(shape, "机器人产业链声明核查与财务证据\n\n北京大学金融AI智能体创新大赛复赛\n本地工作台 · 事实与假设分开呈现")

    # Slide 3 — workflow table
    table = next(sh.table for sh in slides[2].shapes if getattr(sh, "has_table", False) and sh.has_table)
    rows = [("环节", "实现与限定"),
            ("观点审查", "拆成待检查条件；检索支持与反证，缺证不作判断"),
            ("财务整理", "逐字引用锚定＋报表口径校验；16列长表校验"),
            ("策略回测", "先体检数据，再算净值、回撤与同费率基准"),
            ("本地计算", "核验、体检、回测不需要模型密钥"),
            ("外部组件", "Streamlit、openpyxl、NumPy/pandas/PyArrow、pypdf")]
    for r, pair in enumerate(rows):
        for c, value in enumerate(pair):
            replace_cell(table, r, c, value)

    # Slide 6 — regression table
    table = next(sh.table for sh in slides[5].shapes if getattr(sh, "has_table", False) and sh.has_table)
    for r, pair in enumerate([("验证", "结果", "解释"),
                              ("数据锚定", "逐字校验", "摘录须能在标注页找到"),
                              ("口径校验", "6条拦截", "离线复放标出母公司错标"),
                              ("真实重跑", "30/30", "数值与参考表全部相符"),
                              ("目标覆盖", "24/24", "含原先缺失的4个口径"),
                              ("软件回归", "557通过", "工程检查，非业务效果")]):
        for c, value in enumerate(pair):
            replace_cell(table, r, c, value)
    notes = next(sh for sh in slides[5].shapes if sh.has_text_frame and "11条未命中" in sh.text_frame.text)
    set_text(notes, "重跑未触发拆批，拦截规则的效果由离线复放证明；不是受控对照，不称准确率提升比例。")

    # Slide 8 — real run
    body = next(sh for sh in slides[7].shapes if sh.has_text_frame and "历史财务页面" in sh.text_frame.text)
    set_bullets(body, ["工作台首页选择任务后进入工作区。",
                       "财务整理：读取13页→提取候选→核对→生成成果。",
                       "重跑调用3次、348.5秒、返回17,932 token。",
                       "本地计算路径API调用0次；算力费用未计量。",
                       "Windows 11一键启动已验收；Linux未真机验证。"])

    # Slide 10 — reviewer path
    body = next(sh for sh in slides[9].shapes if sh.has_text_frame and "start_demo" in sh.text_frame.text)
    set_bullets(body, ["06_本地部署：Windows双击start_harness.bat。",
                       "浏览器打开 http://127.0.0.1:8510 。",
                       "默认无需账号；本地计算无需模型密钥。",
                       "首次安装依赖需联网，之后可离线运行。",
                       "视频为连续原始录屏，配四部分章节。"])

    # Slide 11 — boundaries and handover
    body = next(sh for sh in slides[10].shapes if sh.has_text_frame and "四条技术声明" in sh.text_frame.text)
    set_bullets(body, ["文件哈希只检查字节，不认证原件来源。",
                       "缺披露日14条、更正标记30条、股票代码16条待人工补。",
                       "CSMAR正式定义与四条技术声明仍有缺口，不自动升级。",
                       "真人试用尚未完成；自动化流程不等于真人试用。",
                       "官方截止：2026-10-13 00:00 北京时间；上传后保存回执。"])

    # Footers
    for slide in slides:
        for shape in slide.shapes:
            if shape.has_text_frame and OLD_DATE in shape.text_frame.text:
                for paragraph in shape.text_frame.paragraphs:
                    for run in paragraph.runs:
                        run.text = run.text.replace(OLD_DATE, NEW_DATE)

    deck.save(str(DECK))
    print(f"updated {DECK.name}: {len(slides)} slides")


if __name__ == "__main__":
    main()

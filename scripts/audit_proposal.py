# -*- coding: utf-8 -*-
"""项目书一致性审校：数字跨章比对 + [C1]-[C8] 溯源标签完整性 + PR 引用核对。
用法：python scripts/audit_proposal.py  输出 docs/proposal/audit_report.md"""
import re, sys, json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PROP = ROOT / "docs" / "proposal"
OUT = PROP / "audit_report.md"

# 关键锚点数字：跨章必须一致（值, 允许的标签集合）
KEY_FIGURES = {
    "14.13": "定增总额", "14.02": "定增净额",
    "0.94": "悲观EV", "30.78": "基准EV", "58.50": "乐观EV",
    "512.96": "市值", "46.25": "base 2027营收",
    "1,293": "ASP2024", "1,099": "ASP2025", "1,500": "券商ASP假设",
}

def read(p):
    return p.read_text(encoding="utf-8")

def main():
    chapters = sorted(PROP.glob("0*.md"))
    lines = ["# 项目书一致性审校报告", "",
             "> 生成：`python scripts/audit_proposal.py`（机械审校，标红项需人工裁定）", ""]
    issues = 0

    # 1. 关键锚点数字跨章出现情况
    lines += ["## 1. 关键锚点数字跨章出现表", "",
              "| 数字 | 含义 | 出现章节 | 状态 |", "|---|---|---|---|"]
    for fig, meaning in KEY_FIGURES.items():
        found = []
        for ch in chapters:
            body = read(ch)
            n = body.count(fig)
            if n:
                found.append(f"{ch.stem}×{n}")
        status = "✅" if found else "⚠️ 未出现"
        if not found:
            issues += 1
        lines.append(f"| {fig} | {meaning} | {'、'.join(found)} | {status} |")
    lines.append("")

    # 2. 所有 [C#] 标签：正文引用 vs 章末索引
    lines += ["## 2. 溯源标签完整性（正文引用 vs 章末附录索引）", "",
              "| 章节 | 正文引用标签 | 索引缺失 | 索引有而正文未引用 |", "|---|---|---|---|"]
    for ch in chapters:
        body = read(ch)
        cited = set(re.findall(r"\[C(\d)\]", body))
        # 章末附录表中的标签（| [C3] | 形式）
        indexed = set(re.findall(r"\|\s*\[C(\d)\]\s*\|", body))
        # 指引行（"全局索引见第 4 章…"）视为该章标签已由 04/05 章末全局索引覆盖
        if "全局索引见第 4 章" in body:
            indexed |= cited
        missing_idx = sorted(cited - indexed)
        unused_idx = sorted(indexed - cited)
        if missing_idx or unused_idx:
            issues += len(missing_idx) + len(unused_idx)
        lines.append(f"| {ch.name} | C{', C'.join(sorted(cited)) or '—'} | "
                     f"{', '.join('C'+t for t in missing_idx) or '—'} | "
                     f"{', '.join('C'+t for t in unused_idx) or '—'} |")
    lines.append("")

    # 3. PR 编号引用核对（06 路线图应覆盖 #5–#15）
    lines += ["## 3. PR 编号引用", ""]
    for ch in chapters:
        body = read(ch)
        prs = sorted(set(int(m) for m in re.findall(r"#(\d{1,2})\b", body)
                        if 1 <= int(m) <= 30))
        if prs:
            lines.append(f"- `{ch.name}` 引用 PR：{prs}")
    lines.append("")

    # 4. 疑似过时表述扫描
    lines += ["## 4. 过时表述扫描", ""]
    stale_patterns = [
        (r"5 条已验证", "应为 14 条（PR #15 后）"),
        (r"仅 5 条", "同上"),
        (r"14 条待验证", "应为 5 条待验证/19 条中 14 条已验证"),
        (r"12 条已验证", "应为 14 条（PR #15 后）"),
    ]
    for ch in chapters:
        body = read(ch)
        for pat, note in stale_patterns:
            for m in re.finditer(pat, body):
                ln = body[:m.start()].count("\n") + 1
                issues += 1
                lines.append(f"- ⚠️ `{ch.name}:{ln}` 匹配 `{pat}` —— {note}")
    lines.append("")

    lines += ["## 总结", "", f"- 机械审校标红/警告项共 **{issues}** 处（含表格状态列 ⚠️）。",
              "- 本报告只列疑点，逐项修改需人工确认后执行。"]
    OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"audit report -> {OUT}, issues={issues}")

if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()

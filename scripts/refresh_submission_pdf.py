# -*- coding: utf-8 -*-
"""Rebuild 02_项目说明.pdf from docs/semifinal/materials_content.json.

Reuses the bookmarked-PDF builder in scripts/build_semifinal_materials.py so the
submission package keeps its verified layout and section bookmarks.
"""
from __future__ import annotations
import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT / "deliverables/semifinal_20261012/饮水思源_Claim2Value/02_项目说明.pdf"
FONT = Path("C:/Windows/Fonts/msyh.ttc")


def load_builder():
    spec = importlib.util.spec_from_file_location("materials", ROOT / "scripts/build_semifinal_materials.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main():
    module = load_builder()
    module.make_pdf(TARGET, module.json.loads((ROOT / "docs/semifinal/materials_content.json").read_text(encoding="utf-8")), FONT)
    print(f"wrote {TARGET} ({TARGET.stat().st_size} bytes)")


if __name__ == "__main__":
    main()

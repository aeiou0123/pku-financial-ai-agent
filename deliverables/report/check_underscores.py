"""Find underscores that sit outside the detokenizing code macros (would break LaTeX)."""
import pathlib
import re

SRC = pathlib.Path(__file__).with_name("main.tex")
CODE = re.compile(r"\\(?:raw)?code\{[^}]*\}")
for number, line in enumerate(SRC.read_text(encoding="utf-8").split("\n"), 1):
    if "_" in CODE.sub("", line):
        print(f"{number}: {CODE.sub('', line).strip()[:170]}")

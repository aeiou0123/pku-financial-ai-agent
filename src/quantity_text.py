"""Bounded numeric-text normalization; original evidence is never rewritten.

Only registered units and valid grouped thousands are handled. This module
does not authenticate sources or implement general dimensional/semantic parsing.
"""
from decimal import Decimal
import re

GROUPED = re.compile(r'(?<![\d.,])\d{1,3}(?:,\d{3})+(?:\.\d+)?(?![\d.,])')
UNITS = {'kNm': ('Nm','1000'), 'kN·m': ('Nm','1000'),
         'Nm': ('Nm','1'), 'N·m': ('Nm','1'), 'N*m': ('Nm','1'),
         'kg': ('kg','1'), 'g': ('kg','0.001'),
         '亿元': ('元','100000000'), '万元': ('元','10000'), '元': ('元','1')}
UNIT_PATTERN = '|'.join(re.escape(u) for u in sorted(UNITS, key=len, reverse=True))
QUANTITY = re.compile(r'(?<![\d.])(?P<number>[+-]?\d+(?:\.\d+)?)\s*(?P<unit>' + UNIT_PATTERN + r')(?![A-Za-z])')
MODEL = re.compile(r'(?<![A-Za-z0-9_-])(?P<model>[A-Za-z][A-Za-z0-9_-]*)型号')


def normalize_quantities(text):
    text = GROUPED.sub(lambda m: m.group().replace(',', ''), text)
    # Only percentage-change decreases are signed; an amount decrease is
    # not itself a negative revenue/profit level.
    text = re.sub(r'(下降|减少|降低)\s*(\d+(?:\.\d+)?)(\s*(?:个百分点|pct|%))',
                  lambda m: m[1] + '-' + m[2] + m[3], text)
    def convert(match):
        unit, scale = UNITS[match['unit']]
        number = format(Decimal(match['number']) * Decimal(scale), 'f')
        if '.' in number:
            number = number.rstrip('0').rstrip('.')
        return number + ' ' + unit
    return QUANTITY.sub(convert, text)


def model_numeric_scope(claim, source):
    """Use every target-model segment for explicit X型号 labels only."""
    targets = {m['model'] for m in MODEL.finditer(claim)}
    markers = list(MODEL.finditer(source))
    if len(targets) != 1 or not markers:
        return source
    target = next(iter(targets))
    return '\n'.join(source[m.start():markers[i+1].start() if i+1 < len(markers) else len(source)]
                     for i, m in enumerate(markers) if m['model'] == target)

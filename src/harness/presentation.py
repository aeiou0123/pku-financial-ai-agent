"""Literal model text and a small, escaped report renderer without remote content."""
from __future__ import annotations
from .module_stamp import source_stamp
_c2v_loaded_source_hash = source_stamp(__file__)

from html import escape
import re


def literal_markup(text):
    return '<div class="desk-paragraph">' + escape(str(text)).replace('\n','<br>') + '</div>'


def literal(text):
    import streamlit as st
    st.markdown(literal_markup(text),unsafe_allow_html=True)


def plain_label(text):
    return re.sub(r'([\\`*{}\[\]()#+.!<>_$])',r'\\\1',str(text))


def report_markup(text):
    """Only headings, lists, quotes and pipe tables; all content remains literal."""
    lines = str(text)[:20000].splitlines()
    parts, paragraph = [], []
    def flush():
        if paragraph:
            parts.append('<p>'+'<br>'.join(escape(s) for s in paragraph)+'</p>')
            paragraph.clear()
    def cells(line):
        return [escape(s.strip().replace('\\|','|')) for s in re.split(r'(?<!\\)\|',line.strip()[1:-1])]
    i = 0
    while i < len(lines):
        line = lines[i]
        if not line.strip():
            flush(); i += 1; continue
        heading = re.match(r'^(#{1,3})\s+(.+)$',line)
        if heading:
            flush()
            level = len(heading[1])+1
            parts.append(f'<h{level}>'+escape(heading[2])+f'</h{level}>')
        elif line.startswith('|') and line.endswith('|') and i+1 < len(lines) and re.fullmatch(r'\|(?:\s*:?-+:?\s*\|)+',lines[i+1]):
            flush()
            parts.append('<div class="desk-report-table" role="region" tabindex="0" aria-label="报告表格，可横向滚动"><table><thead><tr>'+''.join('<th>'+s+'</th>' for s in cells(line))+'</tr></thead><tbody>')
            i += 2
            while i < len(lines) and lines[i].startswith('|') and lines[i].endswith('|'):
                parts.append('<tr>'+''.join('<td>'+s+'</td>' for s in cells(lines[i]))+'</tr>')
                i += 1
            parts.append('</tbody></table></div>')
            continue
        elif line.startswith('- '):
            flush(); items = []
            while i < len(lines) and lines[i].startswith('- '):
                items.append('<li>'+escape(lines[i][2:])+'</li>');i += 1
            parts.append('<ul>'+''.join(items)+'</ul>');continue
        elif line.startswith('> '):
            flush();parts.append('<blockquote>'+escape(line[2:])+'</blockquote>')
        else:
            paragraph.append(line)
        i += 1
    flush()
    return '<article class="desk-report">'+''.join(parts)+'</article>'


def render_report(text):
    import streamlit as st
    st.markdown(report_markup(text),unsafe_allow_html=True)

"""File-specific intake diagnostics; unsuccessful files never enter model scope."""
from __future__ import annotations
from .module_stamp import source_stamp
_c2v_loaded_source_hash = source_stamp(__file__)

import io
from pathlib import Path
import pandas as pd
from .documents import parse,table,digest,safe_name,MAX_BYTES,_check_zip


class FileReadError(ValueError):
    category='document'
    def __init__(self,name,reason,action,error_type):
        self.filename,self.reason,self.action,self.error_type=name,reason,action,error_type
        super().__init__(name+'：'+reason)


def file_error(exc,name):
    if getattr(exc,'category',None)=='document':
        return exc
    message=str(exc)
    # Only our own controlled parser messages are exposed; third-party messages
    # can contain file contents. Keep their exception type instead of their body.
    allowed=('文件为空','单个文件上限','PDF 已加密','没有可读取的文字','仅支持 UTF-8','CSV 存在重复列名',
             '表格为空','表格请使用','支持 PDF','压缩文档展开超过','解析范围超出','PDF页码')
    suffix=Path(name).suffix.lower()
    reason=message if type(exc) is ValueError and message.startswith(allowed) else {
        '.pdf':'PDF未能读取，文件可能损坏或不是有效PDF。',
        '.xlsx':'Excel工作簿未能读取，文件可能损坏或格式不符。',
        '.docx':'Word文档未能读取，文件可能损坏或格式不符。',
        '.csv':'CSV未能解析，请核对编码、引号和列数。',
    }.get(suffix,'文件未能读取，请核对格式与编码。')
    if 'OCR' in reason:
        action='先用OCR识别扫描页，核对文字与原件页码后重新上传；本版不会自动识别图片。'
    elif '加密' in reason:
        action='提供你有权读取的未加密PDF，再重新上传。'
    elif suffix in {'.xlsx','.docx'}:
        action='用'+('Excel' if suffix=='.xlsx' else 'Word')+'打开原件，重新另存为对应格式；不要只修改扩展名。'
    elif suffix in {'.csv','.txt','.md'}:
        action='重新导出UTF-8或GB18030文本；CSV还需核对列名、分隔符和引号。'
    else:
        action='先在本机打开原件确认可读，重新导出后上传；保留原始页码对应关系。'
    return FileReadError(name,reason,action,type(exc).__name__)


def parse_files(uploads, *, pdf_pages=None):
    documents,issues=[],[]
    for name,raw in uploads:
        try:
            documents.append(parse(raw,name,pdf_pages=(pdf_pages or {}).get(name,'')))
        except Exception as exc:
            error=file_error(exc,name)
            issues.append({'name':name,'source_file':safe_name(name),'sha256':digest(raw),'bytes':len(raw),
                'reason':error.reason,'action':error.action,'error_type':error.error_type,'read_status':'failed'})
    return documents,issues


def read_table(raw,name,sheet=0):
    try:
        return table(raw,name,sheet)
    except Exception as exc:
        raise file_error(exc,name) from None


def table_sheets(raw,name):
    try:
        if not raw or len(raw)>MAX_BYTES:
            raise ValueError('文件为空或超过 20 MB。')
        _check_zip(raw)
        with pd.ExcelFile(io.BytesIO(raw)) as workbook:
            return workbook.sheet_names
    except Exception as exc:
        raise file_error(exc,name) from None


def render_file_issues(issues):
    import streamlit as st
    from .presentation import plain_label
    if not issues:
        return
    st.error(f'{len(issues)}个文件未能读取。请替换或移除这些文件后重新读取；尚未发送模型请求。')
    st.table(pd.DataFrame([{'文件':plain_label(i['name']),'原因':plain_label(i['reason']),'处理方法':plain_label(i['action'])} for i in issues]))

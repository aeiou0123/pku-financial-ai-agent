"""Literal research workbooks using the deployment's existing Excel dependency."""
from .module_stamp import source_stamp
_c2v_loaded_source_hash = source_stamp(__file__)
import io
import pandas as pd


def workbook(tables):
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
        for name, frame in tables.items():
            frame.to_excel(writer, sheet_name=name, index=False)
        for sheet in writer.book:
            for row in sheet:
                for cell in row:
                    if isinstance(cell.value, str) and cell.value.startswith('='):
                        cell.data_type = 's'
    return buffer.getvalue()

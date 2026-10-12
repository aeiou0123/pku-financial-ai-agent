"""Source preparation before the existing original-document research workflow."""
from __future__ import annotations
from .module_stamp import source_stamp
_c2v_loaded_source_hash = source_stamp(__file__)

import json
from .catalog import COMPANIES,load_catalog,search_catalog,shortlist_tables,synthetic_catalog
from .exports import workbook
from .presentation import literal


def render(root):
    import streamlit as st
    from datetime import date
    st.title('资料目录')
    st.write('按公司、截止日和主题找公告，再准备原件进入研究。这里检索目录，不调用模型。')
    source=root/'work/csmar_handoff/20261009'
    exists=(source/'raw/C_announcements').is_dir()
    options=['本机已收CSMAR目录','合成示例'] if exists else ['合成示例']
    chosen=st.selectbox('目录来源',options,key='catalog_source')
    synthetic=chosen=='合成示例'
    if synthetic:
        catalog=synthetic_catalog()
        st.info('合成示例只演示检索与清单，不代表真实公司公告。')
        if not exists:
            st.caption('部署包不包含商业数据库原始数据。自己的数据目录可按操作说明接入。')
    else:
        catalog=load_catalog(source)
    summary=catalog['summary']
    st.caption(f"证券索引覆盖{summary['target_ids']}个目标公告ID；其中{summary['missing_target_info_ids']}个尚缺基本信息。全文已接入0份。")
    left,right=st.columns(2)
    company=left.selectbox('研究公司',list(COMPANIES),format_func=lambda code:code+' · '+('合成示例公司' if synthetic else COMPANIES[code]),key='catalog_company')
    cutoff=right.date_input('目录信息截止日',value=date.today(),key='catalog_cutoff')
    terms=st.text_input('公告标题关键词',placeholder='例如：扩产 订单 投资；多个词匹配任一，留空查看该公司已收目录',key='catalog_terms')
    found=search_catalog(catalog,company,cutoff.isoformat(),terms)
    st.caption(f'找到{len(found)}条，按公告日期筛选；标题命中只提供找原件的线索，不判断论点成立。')
    if not found:
        st.info('没有符合条件的目录记录。可减少关键词或核对公司与截止日；目录缺口不代表公司没有公告。')
    else:
        tables=shortlist_tables(found)
        st.dataframe(tables['待找原件'],hide_index=True,width='stretch')
        st.download_button('下载原件准备清单',workbook(tables),file_name='公告原件准备清单.xlsx',key='catalog_download')
        st.download_button('下载目录检索记录',json.dumps({'synthetic':synthetic,'company':company,
            'cutoff':cutoff.isoformat(),'title_terms':terms,'matching_rule':'literal_OR',
            'full_texts_loaded':0,'selected':found,'source_receipts':catalog['receipts']},ensure_ascii=False,indent=2),
            file_name='目录检索记录.json',key='catalog_receipt_download')
    st.subheader('拿到原件后怎么继续')
    st.write('到公司公告页或交易所，用标题、证券代码和日期找到原件。上传PDF或可核对文本，在工作区登记真实披露日与适用范围，然后审查证据。目录本身不会作为全文证据上传，也不会自动填入财务事实或估值参数。')
    with st.expander('目录完整性与来源检查'):
        st.json(summary)
        if catalog['issues']:
            for issue in catalog['issues']:
                literal(issue['file']+'：'+issue['issue'])
        st.caption('重复的相同ID合并并保留全部定位；日期或标题冲突的记录暂不进入按截止日检索。采集中断文件仅登记实际收到行。')

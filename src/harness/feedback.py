"""Plain error guidance with bounded, redacted technical details."""
from __future__ import annotations
from .module_stamp import source_stamp
_c2v_loaded_source_hash = source_stamp(__file__)

from .api import redact
from .presentation import literal


def describe_error(exc,secret=''):
    if getattr(exc,'category',None)=='document':
        return {'title':'文件未能读取','reason':'文件：'+str(exc.filename)+'。'+str(exc.reason),
            'action':str(exc.action),'detail':'读取类型：'+str(exc.error_type)}
    kinds={
        'auth':('模型调用权限未通过','核对密钥所属平台、模型权限和套餐范围；确认后再测试连接。'),
        'quota':('账户额度不足','查看服务商账户余额或套餐余量；额度恢复后再继续，不必反复点击测试。'),
        'budget':('本次请求数已用完','保留原会话、材料和研究要求，再继续未完成批次；已成功的批次会复用。'),
        'timeout':('模型等待超时','查看下方已完成范围；可在连接设置中调整等待时间，再继续。超时重试可能再次计费。'),
        'network':('模型连接中断','检查网络和服务状态，再继续未完成部分；不要重新上传同一批材料。'),
        'context_limit':('本批文字超过模型上限','减小“单批原文字符上限”，或选择更长上下文的模型，再继续。'),
        'output_limit':('模型输出达到上限','提高输出token上限，或减小“单批原文字符上限”后继续；本次截断内容没有采纳。'),
        'empty_response':('模型没有返回可用正文','检查模型和输出token上限后继续；思考过程不作为证据或结果。'),
        'json_format':('模型返回内容未能采纳','本次返回没有可采用的完整结构。检查模型与输出上限，再继续；不会自动修补数字或证据。'),
        'credentials':('返回内容包含凭据，已拒绝采用','清除材料中的密钥或检查服务响应；不要把凭据写入研究要求。'),
    }
    kind=getattr(exc,'kind',None)
    if kind in kinds:
        title,action=kinds[kind]
        return {'title':title,'reason':'本次操作未完成，已保存的结果可在“成果记录”查看。',
            'action':action,'detail':redact(str(exc),secret)[:2000]}
    status=getattr(exc,'status_code',None)
    if status is not None:
        action='稍后检查服务状态，再继续未完成部分。' if status>=500 else '核对地址、协议和实际模型ID；查看服务端说明后再调整。'
        if 300<=status<400:
            action='地址发生重定向。请填写服务商确认的最终地址；客户端没有继续发送密钥。'
        return {'title':f'模型请求未完成（HTTP {status}）','reason':'已有结果仍按原记录保留。',
            'action':action,'detail':redact(str(exc),secret)[:2000]}
    if isinstance(exc,ValueError):
        return {'title':'这一步需要修正','reason':redact(str(exc),secret)[:2000],
            'action':'按提示修正输入后再运行；已保存的历史记录可以继续查看。','detail':type(exc).__name__}
    return {'title':'这一步未完成','reason':'当前没有生成新的有效结果。',
        'action':'核对材料与配置后重试当前步骤。已保存结果可在“成果记录”查看；仍失败时请提供脱敏的错误类型。',
        'detail':type(exc).__name__}


def render_error(issue):
    import streamlit as st
    st.error(issue['title'])
    literal(issue['reason'])
    literal('处理方法：'+issue['action'])
    with st.expander('查看脱敏说明'):
        st.text(issue['detail'])


def show_error(exc,secret=''):
    render_error(describe_error(exc,secret))
